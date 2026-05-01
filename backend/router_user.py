from fastapi import APIRouter, HTTPException, Depends
from bson import ObjectId

from crud_user import user_crud
from models.user import User
from router_auth import create_access_token
from fastapi import status

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/", response_model=list[User])
def list_users():
    return user_crud.list()

@router.get("/{user_id}", response_model=User)
def get_user(user_id: str):
    user = user_crud.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.put("/{user_id}", response_model=User)
def update_user(user_id: str, payload: dict):
    user = user_crud.update(user_id, payload)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: str):
    deleted = user_crud.delete(user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="User not found")
    return None
