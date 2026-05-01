from crud_base import CRUDBase
from database import get_collection

class CRUDUser(CRUDBase):
    pass

user_crud = CRUDUser(get_collection("users"))
