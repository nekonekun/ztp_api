from ztp_api.api.crud.base import CRUDBase
from ztp_api.api.models.models import Model
from ztp_api.api.schemas.models import ModelCreateRequest, ModelPatchRequest


class CRUDEntry(CRUDBase[Model, ModelCreateRequest, ModelPatchRequest]):
    pass


model = CRUDEntry(Model)