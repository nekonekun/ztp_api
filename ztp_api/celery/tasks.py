from celery import current_app
from aiogram import Bot
import re
import asyncio
from ztp_api.celery.dependencies import get_deviceapi_session, get_ftp_session, get_telegram_bot, get_settings


def hex_to_portlist(hexstring: str) -> list[int]:
    return [index
            for index, value
            in enumerate(''.join([bin(int(char, 16))[2:].zfill(4) for char in hexstring]), 1)
            if value == '1']


def portlist_to_hex(portlist: list[int], hexlen: int) -> str:
    resultlist = ['1' if i in portlist else '0' for i in range(1, hexlen * 4 + 1)]
    return hex(int(''.join(resultlist), 2))[2:].zfill(hexlen)


async def send_message(bot: Bot, message: str):
    settings = get_settings()
    chat_ids = settings.TELEGRAM_CHAT_IDS
    for chat_id in chat_ids:
        await bot.send_message(chat_id=chat_id, text=message)


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
        int(vlan_id): [port for port in portlist if port not in untagged_ports[vlan_id]]
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


async def modify_port_vlan(ip, port, vlan, action, mode=None) -> None:
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
    async with session.download_stream('/tftp/test.log') as stream:
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
        pull_full_config: bool = False,
        full_config_commands: list[str] = None,
        full_config_filename: str = None):
    asyncio.run(async_ztp(ip, autochange_vlan, parent_switch, parent_port, management_vlan, pull_full_config, full_config_commands, full_config_filename))


async def async_ztp(ip: str,
                    autochange_vlan: bool = False,
                    parent_switch: str = None,
                    parent_port: str = None,
                    management_vlan: str = None,
                    pull_full_config: bool = False,
                    full_config_commands: list[str] = None,
                    full_config_filename: str = None):
    bot = get_telegram_bot()
    await send_message(bot, 'Началось')

    # TODO Сменить влан на вышестоящем (optional)
    if autochange_vlan:
        await send_message(bot, 'Выбрано автоперевешивание')
        await send_message(bot, 'Запомнили антаг вланы')
        await send_message(bot, 'Сняли антаг вланы')
        await send_message(bot, 'Навесили управление антагом')

    # TODO Дождаться пока начнет пинговаться
    await send_message(bot, 'Ждем пока запингуется')
    await send_message(bot, 'Начал пинговаться')

    # TODO Дождаться пока скачает оба файла и перестанет пинговаться
    await send_message(bot, 'Ждем пока скачает оба файла и потеряется')
    await send_message(bot, 'Дождались')

    # TODO Сменить влан на вышестоящем (optional)
    if autochange_vlan:
        await send_message(bot, 'Выбрано автоперевешивание')
        await send_message(bot, 'Добавили управление тагом')
        await send_message(bot, 'Вернули антаги')

    # TODO Дождаться пока начнет пинговаться
    await send_message(bot, 'Ждем пока запингуется после перезагрузки')
    await send_message(bot, 'Дождались')

    # TODO Залить полный конфиг (optional)
    await send_message(bot, 'Заливаем полный конфиг')
