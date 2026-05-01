from crud_base import CRUDBase
from database import get_collection

class CRUDAgent(CRUDBase):
    pass

agent_crud = CRUDAgent(get_collection("agents"))
