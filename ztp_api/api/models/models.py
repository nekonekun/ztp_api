from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship

from ztp_api.api.db.base import Base


class Model(Base):
    __tablename__ = 'models'
    id = Column(Integer, primary_key=True)
    model = Column(String)
    portcount = Column(Integer)
    configuration_prefix = Column(String)
    default_initial_config = Column(String)
    default_full_config = Column(String)
    firmware = Column(String)