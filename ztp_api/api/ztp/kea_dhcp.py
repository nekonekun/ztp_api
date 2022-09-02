from fastapi import Depends
from ztp_api.api.models.kea_dhcp import Hosts, DHCPOptions
from ztp_api.api.models.entries import Entry
from ztp_api.api.dependencies import get_us_api, get_netbox_session, get_kea_db, get_settings
from sqlalchemy.dialects.postgresql import BYTEA
from sqlalchemy import func
import ipaddress
import binascii


# FIXME
def get_subnet_id(ip_address):
    truly_ip_address = ipaddress.IPv4Address(ip_address)
    if truly_ip_address in ipaddress.IPv4Network('172.22.0.0/16'):
        return 1
    elif truly_ip_address in ipaddress.IPv4Network('10.10.0.0/16'):
        return 2
    elif truly_ip_address in ipaddress.IPv4Network('10.0.0.0/16'):
        return 3
    raise ValueError(f'No suitable subnet for IP {ip_address}')


def hexstr_to_bytea(mac: str) -> bytes:
    return bytes([int(mac[i:i + 2], 16) for i in range(0, len(mac), 2)])


def ipmask_to_bytea(netmask: str) -> bytes:
    return bytes([int(octet) for octet in netmask.split('.')])


def generate_option_125(firmware_filename: str):
    dlink_id = '000000AB'
    suboption_length = hex(1 + 1 + len(firmware_filename))[2:].upper().zfill(2)
    suboption_code = '01'
    filename_length = hex(len(firmware_filename))[2:].upper().zfill(2)
    hex_filename = ''.join([hex(ord(letter))[2:].upper().zfill(2) for letter in firmware_filename])
    return dlink_id + suboption_length + suboption_code + filename_length + hex_filename


async def add_dhcp(device: Entry, kea_db, nb, settings):
    print(settings)
    values = {
        'dhcp_identifier': hexstr_to_bytea(device.mac_address),
        'dhcp_identifier_type': 0,
        'dhcp4_subnet_id': get_subnet_id(device.ip_address),
        'ipv4_address': int(ipaddress.IPv4Address(device.ip_address)),
    }
    new_dhcp_row = Hosts(**values)
    kea_db.add(new_dhcp_row)
    await kea_db.flush()

    # TODO Вытащить из нетбокса маску сети, добавить опцию
    async with nb.get('/api/ipam/prefixes/', params={'contains': device.ip_address}) as response:
        results = await response.json()
    results = results['results']
    results.sort(key=lambda x: x['prefix'].split('/')[1], reverse=True)
    prefix = results[0]['prefix']
    netmask = bytes(str(int(ipaddress.IPv4Interface(results[0]['prefix']).netmask)), 'utf-8')
    values = {
        'code': 1,
        'value': netmask,
        'space': 'dhcp4',
        'host_id': new_dhcp_row.host_id,
        'scope_id': 3,
        'persistent': False,
    }
    new_option = DHCPOptions(**values)
    print(new_option)
    kea_db.add(new_option)
    await kea_db.flush()

    # TODO Вытащить из нетбокса шлюз, добавить опцию
    async with nb.get('/api/ipam/ip-addresses/', params={'parent': prefix, 'tag': 'gw'}) as response:
        results = await response.json()
    results = results['results']
    gateway = hex(int(ipaddress.IPv4Interface(results[0]['address']).ip))[2:].zfill(8)
    values = {
        'code': 3,
        'value': hexstr_to_bytea(gateway),
        'space': 'dhcp4',
        'host_id': new_dhcp_row.host_id,
        'scope_id': 3,
        'persistent': False,
    }
    new_option = DHCPOptions(**values)
    print(new_option)
    kea_db.add(new_option)
    await kea_db.flush()

    # TODO Добавить адрес тфтп сервера с конфигом в опцию
    values = {
        'code': 66,
        'value': bytes(settings.TFTP_SERVER, 'utf-8'),
        'space': 'dhcp4',
        'host_id': new_dhcp_row.host_id,
        'scope_id': 3,
        'persistent': False,
    }
    new_option = DHCPOptions(**values)
    print(new_option)
    kea_db.add(new_option)
    await kea_db.flush()

    # TODO Добавить адрес файла с конфигом в опцию
    filename = settings.TFTP_FOLDER_STRUCTURE['configs_initial'] + device.ip_address + '.cfg'
    values = {
        'code': 67,
        'value': bytes(filename, 'utf-8'),
        'space': 'dhcp4',
        'host_id': new_dhcp_row.host_id,
        'scope_id': 3,
        'persistent': False,
    }
    new_option = DHCPOptions(**values)
    print(new_option)
    kea_db.add(new_option)
    await kea_db.flush()

    # TODO Добавить адрес тфтп сервера с прошивкой в опцию
    tftp_ip = hex(int(ipaddress.IPv4Interface(settings.TFTP_SERVER).ip))[2:].zfill(8)
    values = {
        'code': 150,
        'value': hexstr_to_bytea(tftp_ip),
        'space': 'dhcp4',
        'host_id': new_dhcp_row.host_id,
        'scope_id': 3,
        'persistent': False,
    }
    new_option = DHCPOptions(**values)
    print(new_option)
    kea_db.add(new_option)
    await kea_db.flush()

    # TODO Добавить адрес файла с прошивкой в опцию
    filename = settings.TFTP_FOLDER_STRUCTURE['firmwares'] + device.model.firmware
    values = {
        'code': 125,
        'value': hexstr_to_bytea(generate_option_125(filename)),
        'space': 'dhcp4',
        'host_id': new_dhcp_row.host_id,
        'scope_id': 3,
        'persistent': False,
    }
    new_option = DHCPOptions(**values)
    print(new_option)
    kea_db.add(new_option)
    await kea_db.flush()

    await kea_db.commit()
