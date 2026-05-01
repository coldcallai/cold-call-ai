from crud_base import CRUDBase
from database import get_collection

class CRUDLead(CRUDBase):
    pass

lead_crud = CRUDLead(get_collection("leads"))
