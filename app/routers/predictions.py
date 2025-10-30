from fastapi import APIRouter, HTTPException
from app.database import get_database
from app.models import Prediction
from bson import ObjectId

router = APIRouter(prefix="/predictions", tags=["predictions"])

@router.get("/user/{user_id}/latest", response_model=Prediction)
async def get_latest_prediction(user_id: str):
    db = get_database()
    
    if not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=400, detail="Invalid user ID")
    
    prediction = await db.predictions.find(
        {"user_id": ObjectId(user_id)}
    ).sort("timestamp", -1).limit(1).to_list(1)
    
    if not prediction:
        raise HTTPException(status_code=404, detail="No predictions found")
    
    return Prediction(**prediction[0])

@router.get("/user/{user_id}", response_model=list[Prediction])
async def get_prediction_history(user_id: str, limit: int = 50):
    db = get_database()
    
    if not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=400, detail="Invalid user ID")
    
    predictions = await db.predictions.find(
        {"user_id": ObjectId(user_id)}
    ).sort("timestamp", -1).limit(limit).to_list(limit)
    
    return [Prediction(**pred) for pred in predictions]