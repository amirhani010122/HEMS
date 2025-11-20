from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import httpx
from app.database import get_collection
from app.models import Prediction, PyObjectId, Consumption
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class AIService:
    @staticmethod
    async def get_user_consumption_data(user_id: PyObjectId, hours: int = 24) -> List[Dict[str, Any]]:
        """Get user consumption data for AI analysis"""
        consumptions_collection = get_collection("consumptions")
        
        start_time = datetime.utcnow() - timedelta(hours=hours)
        
        cursor = consumptions_collection.find({
            "user_id": user_id,
            "timestamp": {"$gte": start_time}
        }).sort("timestamp", 1)
        
        data = []
        async for doc in cursor:
            consumption = Consumption(**doc)
            data.append({
                "timestamp": consumption.timestamp.isoformat(),
                "power_usage_kwh": consumption.power_usage_kwh,
                "total_power_watt": consumption.total_power_watt,
                "temperature": consumption.temperature,
                "devices_on": consumption.devices_on,
                "location": consumption.location
            })
        
        return data

    @staticmethod
    async def fetch_ai_prediction(user_id: PyObjectId) -> Optional[Prediction]:
        """Fetch prediction from external AI service"""
        try:
            # Get recent consumption data
            consumption_data = await AIService.get_user_consumption_data(user_id)
            
            if not consumption_data:
                logger.warning(f"No consumption data found for user {user_id}")
                return None
            
            # Prepare request to AI service
            request_data = {
                "user_id": str(user_id),
                "consumption_data": consumption_data,
                "prediction_type": "daily",
                "timestamp": datetime.utcnow().isoformat()
            }
            
            async with httpx.AsyncClient(timeout=settings.AI_SERVICE_TIMEOUT) as client:
                response = await client.post(
                    f"{settings.AI_SERVICE_URL}/predict",
                    json=request_data
                )
                
                if response.status_code == 200:
                    ai_response = response.json()
                    
                    # Store prediction
                    prediction = Prediction(
                        user_id=user_id,
                        prediction_type=ai_response.get("prediction_type", "daily"),
                        suggestions=ai_response.get("suggestions", []),
                        timestamp=datetime.utcnow(),
                        source="external_ai_service"
                    )
                    
                    predictions_collection = get_collection("predictions")
                    await predictions_collection.insert_one(prediction.dict(by_alias=True))
                    
                    logger.info(f"AI prediction stored for user {user_id}")
                    return prediction
                else:
                    logger.error(f"AI service error: {response.status_code} - {response.text}")
                    return None
                    
        except httpx.RequestError as e:
            logger.error(f"AI service request failed: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in AI service: {str(e)}")
            return None

    @staticmethod
    async def get_user_predictions(
        user_id: PyObjectId, 
        limit: int = 10
    ) -> List[Prediction]:
        """Get user prediction history"""
        predictions_collection = get_collection("predictions")
        cursor = predictions_collection.find({"user_id": user_id})\
            .sort("timestamp", -1)\
            .limit(limit)
        
        predictions = []
        async for doc in cursor:
            predictions.append(Prediction(**doc))
        return predictions

    @staticmethod
    async def send_usage_history(user_id: PyObjectId, data: Dict[str, Any]) -> bool:
        """Send usage history to AI service for training/analysis"""
        try:
            request_data = {
                "user_id": str(user_id),
                "usage_data": data,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            async with httpx.AsyncClient(timeout=settings.AI_SERVICE_TIMEOUT) as client:
                response = await client.post(
                    f"{settings.AI_SERVICE_URL}/usage-history",
                    json=request_data
                )
                
                return response.status_code == 200
                
        except Exception as e:
            logger.error(f"Error sending usage history: {str(e)}")
            return False