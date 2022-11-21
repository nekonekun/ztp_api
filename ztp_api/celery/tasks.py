import datetime

from celery import current_app
from aiogram import Bot
import re
import asyncio
from typing import Literal
from ztp_api.celery.dependencies import get_deviceapi_session, get_ftp_session, get_telegram_bot, get_settings, get_self_session


def hex_to_portlist(hexstring: str) -> list[int]:
    return [index
            for index, value
            in enumerate(''.join([bin(int(char, 16))[2:].zfill(4) for char in hexstring]), 1)
            if value == '1']


def portlist_to_hex(portlist: list[int], hexlen: int) -> str:
    resultlist = ['1' if i in portlist else '0' for i in range(1, hexlen * 4 + 1)]
    return hex(int(''.join(resultlist), 2))[2:].zfill(hexlen)


async def send_message(bot: Bot, message: str, prefix: str = ''):
    settings = get_settings()
    chat_ids = settings.TELEGRAM_CHAT_IDS
    for chat_id in chat_ids:
        await bot.send_message(chat_id=chat_id, text=prefix+message)


async def get_vlan_table(ip):
    session = get_deviceapi_session()

    async with session.get('/snmp/v2/walk', params={'ip': ip, 'oid': '1.3.6.1.2.1.17.7.1.4.3.1.2'}) as response:
        result_all_ports = await response.json()

    async with session.get('/snmp/v2/walk', params={'ip': ip, 'oid': '1.3.6.1.2.1.17.7.1.4.3.1.4'}) as response:
        result_untagged_ports = await response.json()

    await session.close()

    untagged_ports = {
        int(entry['oid'].split('.')[-1]): hex_to_portlist(entry['value'][2:])
        for entry in result_untagged_ports['response']
    }

    tagged_ports = {
        entry['oid'].split('.')[-1]: hex_to_portlist(entry['value'][2:])
        for entry in result_all_ports['response']
    }
    tagged_ports = {
        int(vlan_id): [port for port in portlist if port not in untagged_ports[int(vlan_id)]]
        for vlan_id, portlist in tagged_ports.items()
    }

    result = {'tagged': tagged_ports, 'untagged': untagged_ports}
    return result


async def get_port_vlan(ip, port):
    vlans = await get_vlan_table(ip)
    result = {
        'tagged': [vlan_id for vlan_id, portlist in vlans['tagged'].items() if port in portlist],
        'untagged': [vlan_id for vlan_id, portlist in vlans['untagged'].items() if port in portlist],
    }
    return result


async def modify_port_vlan(ip,
                           port,
                           vlan,
                           action: Literal['add', 'delete'],
                           mode: Literal['tagged', 'untagged'] = None) -> None:
    vlan_table = await get_vlan_table(ip)
    tagged = vlan_table['tagged'][vlan]
    untagged = vlan_table['untagged'][vlan]

    if action == 'delete':
        if port in tagged:
            tagged.remove(port)
        if port in untagged:
            untagged.remove(port)
    elif action == 'add':
        if mode == 'tagged':
            if port in untagged:
                untagged.remove(port)
            tagged.append(port)
            tagged.sort()
        elif mode == 'untagged':
            if port in tagged:
                tagged.remove(port)
            untagged.append(port)
            untagged.sort()

    all_ = list(set(tagged) | set(untagged))

    session = get_deviceapi_session()

    async with session.get('/snmp/v2/walk', params={'ip': ip, 'oid': '1.3.6.1.2.1.17.7.1.4.3.1.2.1'}) as response:
        answer = await response.json()
    answer = answer['response'][0]['value']
    hexlen = len(answer) - 2

    await session.get('/snmp/v2/set',
                      params={
                          'ip': ip,
                          'oid': '1.3.6.1.2.1.17.7.1.4.3.1.2.' + str(vlan),
                          'value': portlist_to_hex(all_, hexlen),
                      })
    await session.get('/snmp/v2/set',
                      params={
                          'ip': ip,
                          'oid': '1.3.6.1.2.1.17.7.1.4.3.1.4.' + str(vlan),
                          'value': portlist_to_hex(untagged, hexlen),
                      })
    await session.close()


async def ping(ip) -> bool:
    session = get_deviceapi_session()
    async with session.get('/ping/check', params={'ip': ip}) as response:
        result = await response.json()
    await session.close()
    return result['response']['available']


async def check_files_requested(ip) -> tuple[bool, bool]:
    session = await get_ftp_session()
    logfile = ''
    async with session.download_stream('/tftp/tftp.log') as stream:
        async for block in stream.iter_by_block():
            logfile += block.decode('utf-8')
    await session.quit()

    firmware_requested, config_requested = False, False

    logfile = filter(lambda x: x, logfile.split('\n'))
    regex = r'(\d+\.\d+\.\d+\.\d+) filename (\S+)'

    for line in logfile:
        search = re.search(regex, line)
        if not search:
            continue
        ip_, filename = search.groups()
        if ip_ != ip:
            continue
        if 'firmwares' in filename:
            firmware_requested = True
        if 'configs' in filename:
            config_requested = True

    return firmware_requested, config_requested


@current_app.task
def ztp(ip: str,
        autochange_vlan: bool = False,
        parent_switch: str = None,
        parent_port: str = None,
        management_vlan: str = None,
        push_full_config: bool = False,
        full_config_commands: list[str] = None,
        full_config_filename: str = None):
    asyncio.run(async_ztp(ip,
                          autochange_vlan,
                          parent_switch,
                          parent_port,
                          management_vlan,
                          push_full_config,
                          full_config_commands,
                          full_config_filename))


async def async_ztp(ip: str,
                    autochange_vlan: bool = False,
                    parent_switch: str = None,
                    parent_port: int = None,
                    management_vlan: int = None,
                    push_full_config: bool = False,
                    full_config_commands: list[str] = None,
                    full_config_filename: str = None):
    bot = get_telegram_bot()
    message_prefix = f'[{ip}] '
    untagged = None

    await send_message(bot, f'Начали', message_prefix)

    if autochange_vlan:
        await send_message(bot, 'Выбрано автоперевешивание', message_prefix)
        await send_message(bot, f'Свич {parent_switch} порт {parent_port}', message_prefix)
        vlans_on_uplink = await get_port_vlan(parent_switch, parent_port)
        untagged = vlans_on_uplink['untagged']
        if untagged:
            await send_message(bot, 'Запомнили антаг вланы: ' + ', '.join(map(str, untagged)), message_prefix)
            for vlan in untagged:
                await modify_port_vlan(parent_switch, parent_port, vlan, 'delete')
            await send_message(bot, 'Сняли антаг вланы', message_prefix)
        await modify_port_vlan(parent_switch, parent_port, management_vlan, 'add', 'untagged')
        await send_message(bot, f'Навесили управление ({management_vlan}) антагом', message_prefix)

    await send_message(bot, 'Ждем пока запингуется', message_prefix)
    while not (await ping(ip)):
        await asyncio.sleep(1)
    await send_message(bot, 'Начал пинговаться', message_prefix)

    await send_message(bot, 'Ждем пока скачает оба файла и потеряется', message_prefix)
    firmware_requested, config_requested = await check_files_requested(ip)
    available = await ping(ip)
    while not (firmware_requested and config_requested and not available):
        await asyncio.sleep(1)
        firmware_requested, config_requested = await check_files_requested(ip)
        available = await ping(ip)
    await send_message(bot, 'Докачал и ребутается', message_prefix)

    if autochange_vlan:
        await send_message(bot, 'Выбрано автоперевешивание', message_prefix)
        await modify_port_vlan(parent_switch, parent_port, management_vlan, 'add', 'tagged')
        await send_message(bot, f'Добавили управление {management_vlan} тагом', message_prefix)
        if untagged:
            for vlan in untagged:
                await modify_port_vlan(parent_switch, parent_port, vlan, 'add', 'untagged')
            await send_message(bot, 'Вернули антаги: ' + ', '.join(map(str, untagged)), message_prefix)

    await send_message(bot, 'Ждем пока запингуется после перезагрузки', message_prefix)
    while not (await ping(ip)):
        await asyncio.sleep(1)
    await send_message(bot, 'Дождались', message_prefix)

    if push_full_config:
        await send_message(bot, 'Заливаем полный конфиг', message_prefix)
        commands = []
        if full_config_filename:
            session = await get_ftp_session()
            ls = [file[0].name for file in
                  await session.list('/tftp/configs/full')]
            if full_config_filename in ls:
                cfgfile = ''
                async with session.download_stream(f'/tftp/configs/full/{full_config_filename}') as stream:
                    async for block in stream.iter_by_block():
                        cfgfile += block.decode('utf-8')
                commands.extend(cfgfile.split('\n'))
            await session.quit()
        if full_config_commands:
            commands.extend(full_config_commands)
        if commands:
            commands = ['enable command logging', 'disable clipaging'] + \
                       commands + \
                       ['enable clipaging', 'disable command logging']
            session = get_deviceapi_session()
            request_data = {
                'ip_address': ip,
                'connection_mode': 'telnet',
                'commands': commands,
            }
            await session.post('/terminal/send_commands', json=request_data)
            await send_message(bot, 'Готово', message_prefix)
        else:
            await send_message(bot, 'Команд для заливки не нашлось', message_prefix)


    self_session = get_self_session()
    async with self_session.get('/entries/') as response:
        response = await response.json()
        response = list(filter(lambda x: x['ip_address'] == ip, response))[0]
        entry_id = response['id']
    await self_session.patch(f'/entries/{entry_id}', json={
        'status': 'DONE',
        'celery_id': None,
        'finished_at': datetime.datetime.now()
    })

    # TODO изменение документации
