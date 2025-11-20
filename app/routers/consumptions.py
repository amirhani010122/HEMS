from typing import List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from app.database import get_collection
from app.auth import get_current_active_user
from app.models import User, Consumption, SensorData, ConsumptionAggregation, PyObjectId
from app.utils import watt_to_kwh
from app.services.consumption_service import ConsumptionService
from app.services.subscription_service import SubscriptionService
from app.services.alert_service import AlertService
from app.services.save_mode_service import SaveModeService
from app.services.ai_service import AIService
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/sensor/data")
async def receive_sensor_data(sensor_data: SensorData):
    """استقبال بيانات الاستهلاك من العداد باستخدام meter_id فقط"""
    try:
        # البحث عن المستخدم باستخدام meter_id فقط
        users_collection = get_collection("users")
        user_data = await users_collection.find_one({"meter_id": sensor_data.meter_id})

        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Meter ID not registered"
            )

        user = User(**user_data)

        # Convert watt to kWh (assuming 1 hour measurement)
        power_usage_kwh = watt_to_kwh(sensor_data.total_power_watt)

        # Create consumption record
        consumption = Consumption(
            user_id=user.id,
            device_id=sensor_data.device_id,
            power_usage_kwh=power_usage_kwh,
            total_power_watt=sensor_data.total_power_watt,
            timestamp=sensor_data.timestamp or datetime.utcnow(),
            temperature=sensor_data.temperature,
            devices_on=sensor_data.devices_on,
            devices_off=sensor_data.devices_off,  # ⬅️ تم الإضافة
            location=sensor_data.location,
        )

        # Store consumption
        await ConsumptionService.create_consumption(consumption)

        # Deduct from subscription
        deduction_success = await SubscriptionService.deduct_energy(
            user.id, power_usage_kwh
        )

        if not deduction_success:
            logger.warning(f"Failed to deduct energy for user {user.id}")

        # Check subscription percentage and trigger alerts
        percentage = await SubscriptionService.get_subscription_percentage(user.id)
        if percentage is not None:
            # Check and create alerts
            triggered_alerts = await AlertService.check_and_create_alerts(
                user.id, percentage
            )

            # Auto-enable save mode if critical threshold reached
            if "CRITICAL" in triggered_alerts:
                await SaveModeService.process_low_energy_save_mode(user.id, percentage)

        # Trigger AI prediction (async - don't wait for response)
        import asyncio

        asyncio.create_task(AIService.fetch_ai_prediction(user.id))

        return {
            "status": "success",
            "message": "Sensor data processed successfully",
            "kwh_used": power_usage_kwh,
            "user_id": str(user.id),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing sensor data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing sensor data",
        )


@router.get("/user/{user_id}/hourly", response_model=List[ConsumptionAggregation])
async def get_hourly_consumption(
    user_id: str, date: datetime, current_user: User = Depends(get_current_active_user)
):
    """Get hourly consumption for a specific date"""
    if current_user.id != PyObjectId(user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this resource",
        )

    return await ConsumptionService.get_hourly_consumption(PyObjectId(user_id), date)


@router.get("/user/{user_id}/daily", response_model=List[ConsumptionAggregation])
async def get_daily_consumption(
    user_id: str,
    year: int,
    month: int,
    current_user: User = Depends(get_current_active_user),
):
    """Get daily consumption for a specific month"""
    if current_user.id != PyObjectId(user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this resource",
        )

    return await ConsumptionService.get_daily_consumption(
        PyObjectId(user_id), year, month
    )


@router.get("/user/{user_id}/monthly", response_model=List[ConsumptionAggregation])
async def get_monthly_consumption(
    user_id: str, year: int, current_user: User = Depends(get_current_active_user)
):
    """Get monthly consumption for a specific year"""
    if current_user.id != PyObjectId(user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this resource",
        )

    return await ConsumptionService.get_monthly_consumption(PyObjectId(user_id), year)


@router.get("/user/{user_id}/today")
async def get_today_consumption(
    user_id: str, current_user: User = Depends(get_current_active_user)
):
    """Get today's total consumption"""
    if current_user.id != PyObjectId(user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this resource",
        )

    total_consumption = await ConsumptionService.get_total_consumption_today(
        PyObjectId(user_id)
    )
    return {"total_consumption_kwh": total_consumption}
