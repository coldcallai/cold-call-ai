from typing import Any, Dict, List, Optional
from pymongo.collection import Collection
from bson import ObjectId
from datetime import datetime

class CRUDBase:
    def __init__(self, collection: Collection):
        self.collection = collection

    def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        data["created_at"] = datetime.utcnow()
        data["updated_at"] = datetime.utcnow()
        result = self.collection.insert_one(data)
        return self.get(str(result.inserted_id))

    def get(self, id: str) -> Optional[Dict[str, Any]]:
        return self.collection.find_one({"_id": ObjectId(id)})

    def list(self, filters: Dict[str, Any] = None, limit: int = 50, skip: int = 0) -> List[Dict[str, Any]]:
        filters = filters or {}
        return list(self.collection.find(filters).skip(skip).limit(limit))

    def update(self, id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        data["updated_at"] = datetime.utcnow()
        self.collection.update_one({"_id": ObjectId(id)}, {"$set": data})
        return self.get(id)

    def delete(self, id: str) -> bool:
        result = self.collection.delete_one({"_id": ObjectId(id)})
        return result.deleted_count == 1
