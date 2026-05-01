from crud_base import CRUDBase
from database import get_collection

class CRUDEvent(CRUDBase):
    pass

event_crud = CRUDEvent(get_collection("events"))
