from crud_base import CRUDBase
from database import get_collection

class CRUDNote(CRUDBase):
    pass

note_crud = CRUDNote(get_collection("notes"))
