from fastapi import APIRouter, HTTPException
from app.database import get_database
from app.models import Environment, EnvironmentCreate
from bson import ObjectId

router = APIRouter(prefix="/environment", tags=["environment"])

@router.post("/sensor/data", response_model=Environment)
async def receive_environment_data(env_data: EnvironmentCreate):
    db = get_database()
    
    if not ObjectId.is_valid(env_data.user_id):
        raise HTTPException(status_code=400, detail="Invalid user ID")
    
    env_dict = env_data.dict()
    env_dict["user_id"] = ObjectId(env_data.user_id)
    
    result = await db.environment.insert_one(env_dict)
    new_env = await db.environment.find_one({"_id": result.inserted_id})
    
    return Environment(**new_env)

@router.get("/user/{user_id}/latest", response_model=Environment)
async def get_latest_environment(user_id: str):
    db = get_database()
    
    if not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=400, detail="Invalid user ID")
    
    env_data = await db.environment.find(
        {"user_id": ObjectId(user_id)}
    ).sort("timestamp", -1).limit(1).to_list(1)
    
    if not env_data:
        raise HTTPException(status_code=404, detail="No environment data found")
    
    return Environment(**env_data[0])

@router.get("/user/{user_id}", response_model=list[Environment])
async def get_environment_history(user_id: str, limit: int = 100):
    db = get_database()
    
    if not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=400, detail="Invalid user ID")
    
    env_data = await db.environment.find(
        {"user_id": ObjectId(user_id)}
    ).sort("timestamp", -1).limit(limit).to_list(limit)
    
    return [Environment(**env) for env in env_data]