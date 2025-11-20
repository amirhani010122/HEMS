from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from app.auth import get_current_active_user
from app.models import User, Prediction
from app.services.ai_service import AIService

router = APIRouter()

@router.get("/my-predictions", response_model=List[Prediction])
async def get_my_predictions(current_user: User = Depends(get_current_active_user)):
    """Get user's prediction history"""
    return await AIService.get_user_predictions(current_user.id)

@router.post("/refresh")
async def refresh_prediction(current_user: User = Depends(get_current_active_user)):
    """Trigger a new prediction from AI service"""
    prediction = await AIService.fetch_ai_prediction(current_user.id)
    
    if prediction:
        return {
            "status": "success", 
            "message": "Prediction generated",
            "prediction_id": str(prediction.id)
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate prediction"
        )