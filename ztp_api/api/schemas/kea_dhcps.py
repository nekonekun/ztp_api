from pydantic import BaseModel


class KeaHostCreateRequest(BaseModel):
    dhcp_identifier: bytes
    dhcp_identifier_type: int
    dhcp4_subnet_id: int | None = None
    dhcp6_subnet_id: int | None = None
    ipv4_address: int | None = None
    hostname: str | None = ''
    dhcp4_client_classes: str | None = ''
    dhcp6_client_classes: str | None = ''
    dhcp4_next_server: int | None = None
    dhcp4_server_hostname: str | None = ''
    dhcp4_boot_file_name: str | None = ''
    user_context: str | None = None
    auth_key: str | None = ''

    class Config:
        orm_mode = True


class KeaHostPatchRequest(BaseModel):
    dhcp_identifier: bytes | None = None
    dhcp_identifier_type: int | None = None
    dhcp4_subnet_id: int | None = None
    dhcp6_subnet_id: int | None = None
    ipv4_address: int | None = None
    hostname: str | None = None
    dhcp4_client_classes: str | None = None
    dhcp6_client_classes: str | None = None
    dhcp4_next_server: int | None = None
    dhcp4_server_hostname: str | None = None
    dhcp4_boot_file_name: str | None = None
    user_context: str | None = None
    auth_key: str | None = None

    class Config:
        orm_mode = True


class KeaHost(KeaHostCreateRequest):
    host_id: int

    class Config:
        orm_mode = True


class KeaDHCPOptionCreateRequest(BaseModel):
    code: int
    value: bytes | None = None
    formatted_value: str | None = None
    space: str | None = ''
    persistent: bool
    dhcp_client_class: str | None = ''
    dhcp4_subnet_id: int | None = None
    host_id: int | None = None
    scope_id: int
    user_context: str | None = None

    class Config:
        orm_mode = True


class KeaDHCPOptionPatchRequest(BaseModel):
    code: int | None = None
    value: bytes | None = None
    formatted_value: str | None = None
    space: str | None = None
    persistent: bool | None = None
    dhcp_client_class: str | None = None
    dhcp4_subnet_id: int | None = None
    host_id: int | None = None
    scope_id: int | None = None
    user_context: str | None = None

    class Config:
        orm_mode = True


class KeaDHCPOption(KeaDHCPOptionCreateRequest):
    option_id: int

    class Config:
        orm_mode = True
