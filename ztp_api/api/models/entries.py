from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Enum, DateTime
from sqlalchemy.dialects.postgresql import INET, JSONB, MACADDR
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from ztp_api.api.db.base import Base
from ztp_api.api.models.models import Model


@enum.unique
class ZTPStatus(enum.Enum):
    WAITING = 'WAITING'
    IN_PROGRESS = 'IN_PROGRESS'
    DONE = 'DONE'


class Entry(Base):
    __tablename__ = 'entries'
    id = Column('id', Integer, primary_key=True, nullable=False)
    created_at = Column('created_at', DateTime, server_default=func.now())
    started_at = Column('started_at', DateTime, nullable=True)
    finished_at = Column('finished_at', DateTime, nullable=True)
    status = Column('status', Enum(ZTPStatus, name='ztp_status'))
    celery_id = Column('celery_id', String, nullable=True)
    employee_id = Column('employee_id', Integer, nullable=False)
    node_id = Column('node_id', Integer, nullable=True)
    serial_number = Column('serial_number', String, nullable=False)
    model_id = Column('model_id', ForeignKey(Model.id), nullable=False)
    model = relationship('Model')
    mac_address = Column('mac_address', MACADDR, nullable=False)
    ip_address = Column('ip_address', INET, nullable=False)
    task_id = Column('task_id', Integer, nullable=True)
    parent_switch = Column('parent_switch', INET, nullable=True)
    parent_port = Column('parent_port', Integer, nullable=True)
    autochange_vlans = Column('autochange_vlans', Boolean, nullable=False, default=False)
    original_port_settings = Column('original_port_settings', JSONB, nullable=True)
    port_movements = Column('port_movements', JSONB, nullable=True)
    modified_port_settings = Column('modified_port_settings', JSONB, nullable=True)
    vlan_settings = Column('vlan_settings', JSONB, nullable=True)
    modified_vlan_settings = Column('modified_vlan_settings', JSONB, nullable=True)
    __mapper_args__ = {"eager_defaults": True}