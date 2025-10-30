from fastapi import APIRouter, HTTPException
from app.database import get_database
from app.models import Consumption, ConsumptionCreate
from app.ai_agent import ai_agent
from bson import ObjectId
from datetime import datetime, timedelta

router = APIRouter(prefix="/consumptions", tags=["consumptions"])

@router.post("/sensor/data", response_model=dict)
async def receive_sensor_data(consumption: ConsumptionCreate):
    db = get_database()
    
    if not ObjectId.is_valid(consumption.user_id):
        raise HTTPException(status_code=400, detail="Invalid user ID")
    
    # Store consumption data
    consumption_dict = consumption.dict()
    consumption_dict["user_id"] = ObjectId(consumption.user_id)
    
    result = await db.consumptions.insert_one(consumption_dict)
    new_consumption = await db.consumptions.find_one({"_id": result.inserted_id})
    
    # Get recent consumptions for AI analysis
    recent_consumptions = await db.consumptions.find({
        "user_id": ObjectId(consumption.user_id),
        "timestamp": {"$gte": datetime.utcnow() - timedelta(hours=24)}
    }).to_list(100)
    
    consumptions_models = [Consumption(**cons) for cons in recent_consumptions]
    
    # Prepare current data for AI
    current_data = {
        "power_usage_kwh": consumption.power_usage_kwh,
        "total_power_watt": consumption.total_power_watt,
        "devices_on": consumption.devices_on,
        "temperature": consumption.temperature_c,
        "location": consumption.location
    }
    
    # Get AI prediction
    ai_prediction = await ai_agent.analyze_consumption(consumptions_models, current_data)
    
    # Store prediction
    prediction_dict = {
        "user_id": ObjectId(consumption.user_id),
        "timestamp": datetime.utcnow(),
        "predicted_consumption_kwh": ai_prediction.predicted_consumption_kwh,
        "suggestion": ai_prediction.suggestion,
        "risk_level": ai_prediction.risk_level,
        "model_version": ai_prediction.model_version
    }
    
    await db.predictions.insert_one(prediction_dict)
    
    return {
        "status": "success",
        "message": "Data received and analyzed.",
        "prediction": {
            "predicted_consumption_kwh": ai_prediction.predicted_consumption_kwh,
            "suggestion": ai_prediction.suggestion,
            "risk_level": ai_prediction.risk_level
        }
    }

@router.get("/user/{user_id}", response_model=list[Consumption])
async def get_user_consumptions(user_id: str, limit: int = 100):
    db = get_database()
    
    if not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=400, detail="Invalid user ID")
    
    consumptions = await db.consumptions.find(
        {"user_id": ObjectId(user_id)}
    ).sort("timestamp", -1).limit(limit).to_list(limit)
    
    return [Consumption(**consumption) for consumption in consumptions]

@router.get("/user/{user_id}/aggregate")
async def get_aggregated_consumption(user_id: str, period: str = "daily"):
    db = get_database()
    
    if not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=400, detail="Invalid user ID")
    
    # Define aggregation pipeline based on period
    if period == "hourly":
        group_stage = {
            "$group": {
                "_id": {
                    "year": {"$year": "$timestamp"},
                    "month": {"$month": "$timestamp"},
                    "day": {"$dayOfMonth": "$timestamp"},
                    "hour": {"$hour": "$timestamp"}
                },
                "total_consumption": {"$sum": "$power_usage_kwh"},
                "avg_power": {"$avg": "$total_power_watt"},
                "readings_count": {"$sum": 1}
            }
        }
    else:  # daily
        group_stage = {
            "$group": {
                "_id": {
                    "year": {"$year": "$timestamp"},
                    "month": {"$month": "$timestamp"},
                    "day": {"$dayOfMonth": "$timestamp"}
                },
                "total_consumption": {"$sum": "$power_usage_kwh"},
                "avg_power": {"$avg": "$total_power_watt"},
                "readings_count": {"$sum": 1}
            }
        }
    
    pipeline = [
        {"$match": {"user_id": ObjectId(user_id)}},
        {"$sort": {"timestamp": -1}},
        {"$limit": 1000},
        group_stage,
        {"$sort": {"_id": -1}}
    ]
    
    results = await db.consumptions.aggregate(pipeline).to_list(1000)
    return results