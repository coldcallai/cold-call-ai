from crud_base import CRUDBase
from database import get_collection

class CRUDScript(CRUDBase):
    pass

script_crud = CRUDScript(get_collection("scripts"))
