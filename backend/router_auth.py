from fastapi import APIRouter, HTTPException
from fastapi import Depends
from datetime import datetime, timedelta
from jose import jwt
from passlib.context import CryptContext

from models.auth import LoginRequest, SignupRequest, TokenResponse
from crud_user import user_crud

SECRET_KEY = "CHANGE_THIS_SECRET"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

router = APIRouter(prefix="/auth", tags=["auth"])

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

@router.post("/signup", response_model=TokenResponse)
def signup(payload: SignupRequest):
    existing = user_crud.collection.find_one({"email": payload.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_pw = pwd_context.hash(payload.password)
    user = user_crud.create({
        "email": payload.email,
        "name": payload.name,
        "team_id": payload.team_id,
        "password": hashed_pw,
        "role": "owner" if user_crud.collection.count_documents({}) == 0 else "sales"
    })

    token = create_access_token({"sub": str(user["_id"])})
    return TokenResponse(access_token=token)

@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest):
    user = user_crud.collection.find_one({"email": payload.email})
    if not user:
        raise HTTPException(status_code=400, detail="Invalid credentials")

    if not pwd_context.verify(payload.password, user["password"]):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    token = create_access_token({"sub": str(user["_id"])})
    return TokenResponse(access_token=token)
