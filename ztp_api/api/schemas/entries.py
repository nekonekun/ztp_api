from pydantic import BaseModel
from typing import Literal, Any
import ipaddress
import enum


class NewHouseData(BaseModel):
    task_id: int = None


class NewSwitchData(BaseModel):
    parent_switch: ipaddress.IPv4Address = None
    parent_port: int = None


class ChangeSwitchData(BaseModel):
    ip_address: ipaddress.IPv4Address = None


class EntryCreateRequestData(NewHouseData, NewSwitchData, ChangeSwitchData):
    pass


class EntryCreateRequest(BaseModel):
    employee_id: int
    node_id: int
    serial_number: str
    mac_address: str
    mountType: Literal['newHouse', 'newSwitch', 'changeSwitch']
    data: EntryCreateRequestData

    class Config:
        orm_mode = True


class EntryPatchRequest(BaseModel):
    employee_id: int = None
    node_id: int = None
    serial_number: str = None
    mac_address: str = None
    ip_address: ipaddress.IPv4Address = None

    class Config:
        orm_mode = True


class Entry(BaseModel):
    id: int
    status: Any = None
    celery_id: str = None
    employee_id: int
    node_id: int
    serial_number: str
    model_id: int
    mac_address: str
    ip_address: ipaddress.IPv4Address
    task_id: int = None
    parent_switch: ipaddress.IPv4Address = None
    parent_port: int = None
    autochange_vlans: bool = False
    original_port_settings: dict = None
    port_movements: dict = None
    modified_port_settings: dict = None
    vlan_settings: dict = None
    modified_vlan_settings: dict = None

    class Config:
        orm_mode = True

