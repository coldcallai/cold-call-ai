from crud_base import CRUDBase
from database import get_collection

class CRUDInteraction(CRUDBase):
    pass

interaction_crud = CRUDInteraction(get_collection("interactions"))
