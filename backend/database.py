from pymongo import MongoClient
from pymongo.collection import Collection
import os

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "intentbrain")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

def get_collection(name: str) -> Collection:
    return db[name]
