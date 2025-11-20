from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.database import get_collection
from app.utils import verify_token
from app.models import User

security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = verify_token(credentials.credentials)
    if payload is None:
        raise credentials_exception
        
    email = payload.get("sub")
    if email is None:
        raise credentials_exception
    
    users_collection = get_collection("users")
    user_data = await users_collection.find_one({"email": email})
    if user_data is None:
        raise credentials_exception
        
    return User(**user_data)

async def get_current_active_user(current_user: User = Depends(get_current_user)):
    return current_user