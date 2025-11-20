from typing import List, Dict, Any
from datetime import datetime, timedelta
from app.database import get_collection
from app.models import Consumption, PyObjectId, ConsumptionAggregation
from app.utils import watt_to_kwh
import logging

logger = logging.getLogger(__name__)

class ConsumptionService:
    @staticmethod
    async def create_consumption(consumption: Consumption) -> bool:
        """Store consumption data"""
        consumptions_collection = get_collection("consumptions")
        result = await consumptions_collection.insert_one(consumption.dict(by_alias=True))
        return result.acknowledged

    @staticmethod
    async def get_hourly_consumption(user_id: PyObjectId, date: datetime) -> List[ConsumptionAggregation]:
        """Get hourly consumption aggregation for a specific date"""
        consumptions_collection = get_collection("consumptions")
        
        start_of_day = datetime(date.year, date.month, date.day)
        end_of_day = start_of_day + timedelta(days=1)
        
        pipeline = [
            {
                "$match": {
                    "user_id": user_id,
                    "timestamp": {
                        "$gte": start_of_day,
                        "$lt": end_of_day
                    }
                }
            },
            {
                "$group": {
                    "_id": {
                        "year": {"$year": "$timestamp"},
                        "month": {"$month": "$timestamp"},
                        "day": {"$dayOfMonth": "$timestamp"},
                        "hour": {"$hour": "$timestamp"}
                    },
                    "total_consumption_kwh": {"$sum": "$power_usage_kwh"},
                    "average_power_watt": {"$avg": "$total_power_watt"},
                    "timestamp": {"$first": "$timestamp"}
                }
            },
            {
                "$sort": {"_id.hour": 1}
            }
        ]
        
        aggregations = []
        async for doc in consumptions_collection.aggregate(pipeline):
            aggregations.append(ConsumptionAggregation(
                period=f"{doc['_id']['hour']:02d}:00",
                total_consumption_kwh=doc["total_consumption_kwh"],
                average_power_watt=doc["average_power_watt"],
                timestamp=doc["timestamp"]
            ))
        
        return aggregations

    @staticmethod
    async def get_daily_consumption(user_id: PyObjectId, year: int, month: int) -> List[ConsumptionAggregation]:
        """Get daily consumption aggregation for a specific month"""
        consumptions_collection = get_collection("consumptions")
        
        start_of_month = datetime(year, month, 1)
        if month == 12:
            end_of_month = datetime(year + 1, 1, 1)
        else:
            end_of_month = datetime(year, month + 1, 1)
        
        pipeline = [
            {
                "$match": {
                    "user_id": user_id,
                    "timestamp": {
                        "$gte": start_of_month,
                        "$lt": end_of_month
                    }
                }
            },
            {
                "$group": {
                    "_id": {
                        "year": {"$year": "$timestamp"},
                        "month": {"$month": "$timestamp"},
                        "day": {"$dayOfMonth": "$timestamp"}
                    },
                    "total_consumption_kwh": {"$sum": "$power_usage_kwh"},
                    "average_power_watt": {"$avg": "$total_power_watt"},
                    "timestamp": {"$first": "$timestamp"}
                }
            },
            {
                "$sort": {"_id.day": 1}
            }
        ]
        
        aggregations = []
        async for doc in consumptions_collection.aggregate(pipeline):
            aggregations.append(ConsumptionAggregation(
                period=f"{doc['_id']['year']}-{doc['_id']['month']:02d}-{doc['_id']['day']:02d}",
                total_consumption_kwh=doc["total_consumption_kwh"],
                average_power_watt=doc["average_power_watt"],
                timestamp=doc["timestamp"]
            ))
        
        return aggregations

    @staticmethod
    async def get_monthly_consumption(user_id: PyObjectId, year: int) -> List[ConsumptionAggregation]:
        """Get monthly consumption aggregation for a specific year"""
        consumptions_collection = get_collection("consumptions")
        
        start_of_year = datetime(year, 1, 1)
        end_of_year = datetime(year + 1, 1, 1)
        
        pipeline = [
            {
                "$match": {
                    "user_id": user_id,
                    "timestamp": {
                        "$gte": start_of_year,
                        "$lt": end_of_year
                    }
                }
            },
            {
                "$group": {
                    "_id": {
                        "year": {"$year": "$timestamp"},
                        "month": {"$month": "$timestamp"}
                    },
                    "total_consumption_kwh": {"$sum": "$power_usage_kwh"},
                    "average_power_watt": {"$avg": "$total_power_watt"},
                    "timestamp": {"$first": "$timestamp"}
                }
            },
            {
                "$sort": {"_id.month": 1}
            }
        ]
        
        aggregations = []
        async for doc in consumptions_collection.aggregate(pipeline):
            aggregations.append(ConsumptionAggregation(
                period=f"{doc['_id']['year']}-{doc['_id']['month']:02d}",
                total_consumption_kwh=doc["total_consumption_kwh"],
                average_power_watt=doc["average_power_watt"],
                timestamp=doc["timestamp"]
            ))
        
        return aggregations

    @staticmethod
    async def get_total_consumption_today(user_id: PyObjectId) -> float:
        """Get total consumption for today"""
        consumptions_collection = get_collection("consumptions")
        
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow = today + timedelta(days=1)
        
        pipeline = [
            {
                "$match": {
                    "user_id": user_id,
                    "timestamp": {
                        "$gte": today,
                        "$lt": tomorrow
                    }
                }
            },
            {
                "$group": {
                    "_id": None,
                    "total_consumption": {"$sum": "$power_usage_kwh"}
                }
            }
        ]
        
        result = await consumptions_collection.aggregate(pipeline).to_list(length=1)
        if result:
            return result[0]["total_consumption"]
        return 0.0