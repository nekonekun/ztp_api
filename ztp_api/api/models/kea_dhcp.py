from sqlalchemy import Column, Integer, Boolean
from sqlalchemy.dialects.postgresql import BYTEA, TEXT, SMALLINT, BIGINT, VARCHAR

from ztp_api.api.db.base import Base


class Hosts(Base):
    __tablename__ = 'hosts'
    host_id = Column('host_id', Integer, primary_key=True, nullable=False, autoincrement=True)
    dhcp_identifier = Column('dhcp_identifier', BYTEA, nullable=False)
    dhcp_identifier_type = Column('dhcp_identifier_type', SMALLINT, nullable=False)
    dhcp4_subnet_id = Column('dhcp4_subnet_id', BIGINT)
    dhcp6_subnet_id = Column('dhcp6_subnet_id', BIGINT)
    ipv4_address = Column('ipv4_address', BIGINT)
    hostname = Column('hostname', VARCHAR(255))
    dhcp4_client_classes = Column('dhcp4_client_classes', VARCHAR(255))
    dhcp6_client_classes = Column('dhcp6_client_classes', VARCHAR(255))
    dhcp4_next_server = Column('dhcp4_next_server', BIGINT)
    dhcp4_server_hostname = Column('dhcp4_server_hostname', VARCHAR(64))
    dhcp4_boot_file_name = Column('dhcp4_boot_file_name', VARCHAR(128))
    user_context = Column('user_context', TEXT)
    auth_key = Column('auth_key', VARCHAR(32))


class DHCPOptions(Base):
    __tablename__ = 'dhcp4_options'
    option_id = Column('option_id', Integer, primary_key=True, nullable=False, autoincrement=True)
    code = Column('code', SMALLINT, nullable=False)
    value = Column('value', BYTEA)
    formatted_value = Column('formatted_value', TEXT)
    space = Column('space', VARCHAR(128))
    persistent = Column('persistent', Boolean, nullable=False)
    dhcp_client_class = Column('dhcp_client_class', VARCHAR(128))
    dhcp4_subnet_id = Column('dhcp4_subnet_id', BIGINT)
    host_id = Column('host_id', Integer)
    scope_id = Column('scope_id', SMALLINT, nullable=False)
    user_context = Column('user_context', TEXT)
