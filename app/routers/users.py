from fastapi import APIRouter, Depends, HTTPException, status
from app.database import get_database
from app.models import User, UserCreate, UserInDB, Token
from app.auth import get_password_hash, verify_password, create_access_token
from bson import ObjectId
from datetime import timedelta
from app.config import settings

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/register", response_model=User)
async def register_user(user: UserCreate):
    db = get_database()
    
    # Check if user already exists
    existing_user = await db.users.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user document
    user_dict = user.dict()
    user_dict["hashed_password"] = get_password_hash(user.password)
    del user_dict["password"]
    
    result = await db.users.insert_one(user_dict)
    new_user = await db.users.find_one({"_id": result.inserted_id})
    
    return User(**new_user)

@router.post("/login", response_model=Token)
async def login_user(email: str, password: str):
    db = get_database()
    
    user = await db.users.find_one({"email": email})
    if not user or not verify_password(password, user.get("hashed_password", "")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    access_token = create_access_token(
        data={"sub": user["email"]},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/{user_id}", response_model=User)
async def get_user(user_id: str):
    db = get_database()
    
    if not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=400, detail="Invalid user ID")
    
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return User(**user)

@router.put("/{user_id}", response_model=User)
async def update_user(user_id: str, user_update: dict):
    db = get_database()
    
    if not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=400, detail="Invalid user ID")
    
    # Remove password field if present
    if "password" in user_update:
        del user_update["password"]
    
    await db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": user_update}
    )
    
    updated_user = await db.users.find_one({"_id": ObjectId(user_id)})
    return User(**updated_user)