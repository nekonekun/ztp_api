from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks

import ipaddress
import re
import celery

from ztp_api.api import crud, schemas, models
from ztp_api.api.dependencies import get_db, get_us_api, get_netbox_session, get_kea_db, get_settings, \
    get_tftp_session, get_celery
from ztp_api.api.ztp.kea_dhcp import add_dhcp
from ztp_api.api.ztp.ztp import generate_initial_config

entries_router = APIRouter()


@entries_router.get('/', response_model=list[schemas.Entry])
async def entries_list(skip: int = 0, limit: int = 100, db=Depends(get_db)):
    entries = await crud.entry.get_multi(db, skip=skip, limit=limit)
    return entries


@entries_router.post('/', response_model=schemas.Entry)
async def entries_create(req: schemas.EntryCreateRequest,
                         background_tasks: BackgroundTasks,
                         db=Depends(get_db),
                         kea_db=Depends(get_kea_db),
                         us=Depends(get_us_api),
                         nb=Depends(get_netbox_session),
                         tftp=Depends(get_tftp_session),
                         settings=Depends(get_settings)):
    # resp = dict(req.copy())
    new_entry_object = {}
    dirty_mac = req.mac_address
    clean_mac = ''.join([character for character in dirty_mac.lower() if character in '0123456789abcdef'])
    new_entry_object['serial_number'] = req.serial_number
    new_entry_object['node_id'] = req.node_id
    new_entry_object['mac_address'] = clean_mac
    new_entry_object['employee_id'] = req.employee_id
    new_entry_object['node_id'] = req.node_id
    mount_type = req.mount_type
    if mount_type == 'newHouse':
        new_entry_object['task_id'] = req.task_id
        try:
            task_data = await us.task.show(id=req.task_id)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=[
                    {
                        'field': 'taskId',
                        'msg': 'Не получилось найти такое задание',
                    }
                ]
            )
        target_field = list(filter(lambda x: x.id == 266, task_data.additional_data))
        if not target_field:
            raise HTTPException(status_code=422, detail=[
                    {
                        'field': 'taskId',
                        'msg': 'В задании не указано ТЗ от ШПД',
                    }
                ]
            )
        target_field = target_field[0].value
        subnet = re.search(r'mgmt (\d+\.\d+\.\d+\.\d+/\d+)', target_field)
        if not subnet:
            raise HTTPException(status_code=422, detail=[
                    {
                        'field': 'taskId',
                        'msg': 'В ТЗ от ШПД не указана менеджмент сетка',
                    }
                ]
            )
        subnet = subnet.group(1)
        async with nb.get('/api/ipam/prefixes/', params={'prefix': subnet}) as response:
            answer = await response.json()
            if len(answer['results']) != 1:
                raise HTTPException(status_code=422, detail=[
                        {
                            'field': 'taskId',
                            'msg': 'Указанная в заявке менеджмент сетка не ищется в нетбоксе',
                        }
                    ]
                )
            prefix_info = answer['results'][0]
            vlan_info = prefix_info.get('vlan')
            if not vlan_info:
                raise HTTPException(status_code=422, detail=[
                        {
                            'field': 'taskId',
                            'msg': 'К указанной в заявке менеджмент сетке не привязан влан в нетбоксе',
                        }
                    ]
                )
        async with nb.get('/api/ipam/prefixes/', params={'vlan_id': vlan_info['id']}) as response:
            answer = await response.json()
            if not answer.get('results'):
                raise HTTPException(status_code=422, detail=[
                        {
                            'field': 'taskId',
                            'msg': 'Невозможная ошибка: к влану не привязана ни одна сетка',
                        }
                    ]
                )
            available_prefix_ids = [prefix['id'] for prefix in answer['results']]
        new_ip = None
        for prefix_id in available_prefix_ids:
            async with nb.get(f'/api/ipam/prefixes/{prefix_id}/available-ips/') as response:
                answer = await response.json()
                if answer:
                    new_ip = answer[0]['address']
                    new_ip = ipaddress.IPv4Interface(new_ip).ip.exploded
                    break
        if not new_ip:
            raise HTTPException(status_code=422, detail=[
                    {
                        'field': 'taskId',
                        'msg': 'Не получилось выбрать айпишник -- нет свободных.',
                    }
                ]
            )
        new_entry_object['ip_address'] = new_ip
    elif mount_type == 'newSwitch':
        if not req.ip_address:
            raise HTTPException(status_code=422, detail=[
                    {
                        'field': 'ip',
                        'msg': 'Не указан свич, от которого будет подключен новый.',
                    }
                ]
            )
        if not req.parent_port:
            raise HTTPException(status_code=422, detail=[
                    {
                        'field': 'port',
                        'msg': 'Не указан порт, от которого будет подключен новый свич.',
                    }
                ]
            )
        async with nb.get('/api/ipam/prefixes/', params={'contains': req.ip_address.exploded}) as response:
            answer = await response.json()
            if len(answer['results']) != 1:
                raise HTTPException(status_code=422, detail=[
                        {
                            'field': 'ip',
                            'msg': 'Сетка вышестоящего свича не ищется в нетбоксе',
                        }
                    ]
                )
            prefix_info = answer['results'][0]
            vlan_info = prefix_info.get('vlan')
            if not vlan_info:
                raise HTTPException(status_code=422, detail=[
                        {
                            'field': 'ip',
                            'msg': 'К сетке вышестоящего свича не привязан влан в нетбоксе',
                        }
                    ]
                )
        async with nb.get('/api/ipam/prefixes/', params={'vlan_id': vlan_info['id']}) as response:
            answer = await response.json()
            if not answer.get('results'):
                raise HTTPException(status_code=422, detail=[
                        {
                            'field': 'ip',
                            'msg': 'Невозможная ошибка: к влану не привязана ни одна сетка',
                        }
                    ]
                )
            available_prefix_ids = [prefix['id'] for prefix in answer['results']]
        new_ip = None
        for prefix_id in available_prefix_ids:
            async with nb.get(f'/api/ipam/prefixes/{prefix_id}/available-ips/') as response:
                answer = await response.json()
                if answer:
                    new_ip = answer[0]['address']
                    new_ip = ipaddress.IPv4Interface(new_ip).ip.exploded
                    break
        if not new_ip:
            raise HTTPException(status_code=422, detail=[
                    {
                        'field': 'ip',
                        'msg': 'Не получилось выбрать айпишник -- нет свободных.',
                    }
                ]
            )
        new_entry_object['parent_switch'] = req.ip_address.exploded
        new_entry_object['parent_port'] = req.parent_port
        new_entry_object['ip_address'] = new_ip
    elif mount_type == 'changeSwitch':
        try:
            device_id = await us.device.get_device_id(object_type='switch',
                                                      data_typer='ip',
                                                      data_value=req.ip_address.exploded)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=[
                    {
                        'field': 'ip',
                        'msg': 'Ошибка при поиске свича',
                    }
                ]
            )
        try:
            device_data = await us.device.get_data(object_type='switch', object_id=device_id, is_hide_ifaces_data=1)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=[
                    {
                        'field': 'ip',
                        'msg': 'Ошибка при поиске свича',
                    }
                ]
            )
        uplink = device_data[0].uplink_iface
        if len(uplink) == 1:
            for uplink_port in uplink:
                try:
                    commutation_data = await us.commutation.get_data(object_type='switch', object_id=device_id, is_finish_data='1')
                except ValueError as exc:
                    break
                try:
                    uplink_neighbour = commutation_data.commutation[str(uplink_port)]['0']
                except KeyError as exc:
                    break
                parent_port = uplink_neighbour.interface
                try:
                    neighbour_data = await us.device.get_data(object_type='switch', object_id=uplink_neighbour.object_id, is_hide_ifaces_data=1)
                except ValueError as exc:
                    break
                parent_switch = neighbour_data[0].host
                new_entry_object['parent_switch'] = parent_switch
                new_entry_object['parent_port'] = parent_port
        new_entry_object['ip_address'] = req.ip_address.exploded
    new_entry_object['status'] = models.entries.ZTPStatus.WAITING
    try:
        inventory_id = await us.inventory.get_inventory_id(data_typer='serial_number', data_value=new_entry_object['serial_number'])
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=[
                {
                    'field': 'serial',
                    'msg': 'Ошибка при поиске свича',
                }
            ]
        )
    inventory_id = inventory_id['id']
    inventory_data = await us.inventory.get_inventory(id=inventory_id)
    model_name = inventory_data['data']['name']
    models_db = await crud.model.get_multi(db=db)
    model = list(filter(lambda x: x.model == model_name, models_db))
    if not model:
        raise HTTPException(status_code=422, detail=[
                {
                    'field': 'serial',
                    'msg': f'Модель {model_name} ещё не добавлена в ZTP',
                }
            ]
        )
    model = model[0]
    new_entry_object['model_id'] = model.id
    answer = await crud.entry.create(db, obj_in=new_entry_object)
    background_tasks.add_task(add_dhcp, answer, db, kea_db, nb, settings)
    background_tasks.add_task(generate_initial_config, answer, db, nb, tftp, settings)
    return answer


@entries_router.get('/{entry_id}/', response_model=schemas.Entry)
async def entries_read(entry_id: int, db=Depends(get_db)):
    entry = await crud.entry.get(db=db, id=entry_id)
    return entry


@entries_router.patch('/{entry_id}', response_model=schemas.Entry)
async def entries_partial_update(entry_id: int, req: schemas.EntryPatchRequest, db=Depends(get_db), ):
    entry = await crud.entry.get(db=db, id=entry_id)
    answer = await crud.entry.update(db, entry, req)
    return answer


@entries_router.delete('/{entry_id}/')
async def entries_delete(entry_id: int, db=Depends(get_db)):
    answer = await crud.entry.remove(db, id=entry_id)
    return answer


@entries_router.post('/{entry_id}/start_ztp')
async def entries_ztp_start(entry_id: int,
                            db=Depends(get_db),
                            cel=Depends(get_celery),
                            nb=Depends(get_netbox_session)):
    entry = await crud.entry.get(db=db, id=entry_id)
    async with nb.get('/api/ipam/prefixes/', params={'contains': entry.ip_address.exploded}) as response:
        answer = await response.json()
    prefix_info = answer['results'][0]
    vlan_info = prefix_info.get('vlan')
    vlan_id = vlan_info['vid']
    task = cel.send_task('ztp_api.celery.tasks.ztp', (entry.ip_address.exploded, entry.autochange_vlans,
                                                      entry.parent_switch, entry.parent_port, vlan_id))
    answer = await crud.entry.update(db, entry, {'celery_id': task.id})
    return answer


@entries_router.post('/{entry_id}/stop_ztp')
async def entries_ztp_start(entry_id: int,
                            db=Depends(get_db),
                            cel=Depends(get_celery),
                            nb=Depends(get_netbox_session)):
    entry = await crud.entry.get(db=db, id=entry_id)
    celery_task_id = entry.celery_id
    cel.control.revoke(celery_task_id)
    answer = await crud.entry.update(db, entry, {'celery_id': None})
    return answer
