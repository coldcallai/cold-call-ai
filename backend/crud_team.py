from crud_base import CRUDBase
from database import get_collection

class CRUDTeam(CRUDBase):
    pass

team_crud = CRUDTeam(get_collection("teams"))
