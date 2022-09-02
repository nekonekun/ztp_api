from pydantic import BaseModel


class ModelCreateRequest(BaseModel):
    model: str
    portcount: int
    configuration_prefix: str
    default_initial_config: str
    default_full_config: str
    firmware: str = None

    class Config:
        orm_mode = True


class ModelPatchRequest(BaseModel):
    model: str = None
    portcount: int = None
    configuration_prefix: str = None
    default_initial_config: str = None
    default_full_config: str = None
    firmware: str = None

    class Config:
        orm_mode = True


class Model(BaseModel):
    id: int
    model: str
    portcount: int
    configuration_prefix: str
    default_initial_config: str
    default_full_config: str
    firmware: str

    class Config:
        orm_mode = True

