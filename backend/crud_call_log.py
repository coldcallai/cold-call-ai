from crud_base import CRUDBase
from database import get_collection

class CRUDCallLog(CRUDBase):
    pass

call_log_crud = CRUDCallLog(get_collection("call_logs"))
