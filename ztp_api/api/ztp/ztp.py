from ztp_api.api.models.entries import Entry
from ztp_api.api.models.models import Model
import ipaddress
from sqlalchemy.future import select
from jinja2 import Template


async def generate_initial_config(device: Entry, db, nb, tftp, settings):
    stmt = select(Model).where(Model.id == device.model_id)
    response = await db.execute(stmt)
    device_model: Model = response.scalars().one()
    template_filename = device_model.default_initial_config
    templates_folder = settings.TFTP_FOLDER_STRUCTURE['templates_initial']
    template = tftp.download(template_filename, templates_folder)

    async with nb.get('/api/ipam/prefixes/', params={'contains': device.ip_address}) as response:
        results = await response.json()
    prefix = max(results['results'], key=lambda x: int(x['prefix'].split('/')[1]))  # maybe use ip_interface.netmask
    async with nb.get('/api/ipam/ip-addresses/', params={'parent': prefix['prefix'], 'tag': 'gw'}) as response:
        results = await response.json()
    gateway_dummy = results['results'][0]['address']
    configuration_parameters = {
        'configuration_prefix': device_model.configuration_prefix,
        'portcount': device_model.portcount,
        'ip_address': device.ip_address,
        'management_vlan_id': prefix['vlan']['vid'],
        'management_vlan_name': prefix['vlan']['name'].replace(' ', ''),
        'subnet_mask': ipaddress.IPv4Network(prefix['prefix']).netmask.exploded,
        'gateway': ipaddress.IPv4Interface(gateway_dummy).ip.exploded,
    }

    template = Template(template)
    configuration = template.render(**configuration_parameters)

    configuration_filename = device.ip_address + '.cfg'
    configuration_folder = settings.TFTP_FOLDER_STRUCTURE['configs_initial']
    tftp.upload(configuration_filename, configuration, configuration_folder)

# TODO Генерация полного конфига
# TODO Сам процесс
