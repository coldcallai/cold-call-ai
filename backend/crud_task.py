from crud_base import CRUDBase
from database import get_collection

class CRUDTask(CRUDBase):
    pass

task_crud = CRUDTask(get_collection("tasks"))
