from pydantic import BaseModel, Field
from typing import Literal, Any, Optional
import ipaddress
import datetime

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
    employee_id: int = Field(..., alias='employeeId')
    node_id: int = Field(..., alias='nodeId')
    serial_number: str = Field(..., alias='serial')
    mac_address: str = Field(..., alias='mac')
    mount_type: Literal['newHouse', 'newSwitch', 'changeSwitch'] = Field(..., alias='mountType')

    ip_address: Optional[ipaddress.IPv4Address] = Field(alias='ip')

    parent_port: Optional[int] = Field(alias='port')

    task_id: Optional[int] = Field(alias='taskId')

    class Config:
        orm_mode = True


class EntryPatchRequest(BaseModel):
    started_at: datetime.datetime = None
    finished_at: datetime.datetime = None
    celery_id: str = None
    status: Any = None
    employee_id: int = None
    node_id: int = None
    mac_address: str = None
    ip_address: ipaddress.IPv4Address = None
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


class Entry(BaseModel):
    id: int
    created_at: datetime.datetime
    started_at: datetime.datetime = None
    finished_at: datetime.datetime = None
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

