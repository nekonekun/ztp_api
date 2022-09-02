from ztp_api.api.crud.base import CRUDBase
from ztp_api.api.models.entries import Entry
from ztp_api.api.schemas.entries import EntryCreateRequest, EntryPatchRequest


class CRUDEntry(CRUDBase[Entry, EntryCreateRequest, EntryPatchRequest]):
    pass


entry = CRUDEntry(Entry)