from crud_base import CRUDBase
from database import get_collection

class CRUDCampaign(CRUDBase):
    pass

campaign_crud = CRUDCampaign(get_collection("campaigns"))
