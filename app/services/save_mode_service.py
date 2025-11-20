from typing import Optional, Dict, Any
from datetime import datetime
from app.database import get_collection
from app.models import User, PyObjectId, SaveModeCommand
from app.utils import log_energy_event
import logging
from typing import List


logger = logging.getLogger(__name__)

class SaveModeService:
    @staticmethod
    async def enable_save_mode(user_id: PyObjectId, reason: str) -> bool:
        """Enable save mode for user"""
        users_collection = get_collection("users")
        result = await users_collection.update_one(
            {"_id": user_id},
            {"$set": {
                "save_mode": True,
                "save_mode_reason": reason,
                "save_mode_activated_at": datetime.utcnow()
            }}
        )
        
        if result.modified_count > 0:
            log_energy_event(str(user_id), "SAVE_MODE_ENABLED", f"Reason: {reason}")
            logger.info(f"Save mode enabled for user {user_id}, reason: {reason}")
            return True
        return False

    @staticmethod
    async def disable_save_mode(user_id: PyObjectId) -> bool:
        """Disable save mode for user"""
        users_collection = get_collection("users")
        result = await users_collection.update_one(
            {"_id": user_id},
            {"$set": {
                "save_mode": False,
                "save_mode_reason": None
            }}
        )
        
        if result.modified_count > 0:
            log_energy_event(str(user_id), "SAVE_MODE_DISABLED", "Manual disable")
            logger.info(f"Save mode disabled for user {user_id}")
            return True
        return False

    @staticmethod
    async def get_save_mode_status(user_id: PyObjectId) -> Dict[str, Any]:
        """Get save mode status and commands"""
        users_collection = get_collection("users")
        user_data = await users_collection.find_one({"_id": user_id})
        
        if not user_data:
            return {"save_mode": False, "command": None}
        
        user = User(**user_data)
        
        if user.save_mode:
            command = SaveModeCommand(
                devices_to_turn_off=SaveModeService._get_devices_to_turn_off(user)
            )
            return {
                "save_mode": True,
                "reason": user.save_mode_reason,
                "command": command.dict()
            }
        else:
            return {"save_mode": False, "command": None}

    @staticmethod
    def _get_devices_to_turn_off(user: User) -> List[str]:
        """Determine which devices to turn off based on user preferences"""
        base_devices = ["AC", "Heater", "WaterBoiler"]
        
        # Adjust based on user preferences
        if user.preferred_temp > 22:
            # If user prefers warmer temps, don't turn off heater
            base_devices = [device for device in base_devices if device != "Heater"]
        else:
            # If user prefers cooler temps, don't turn off AC
            base_devices = [device for device in base_devices if device != "AC"]
            
        return base_devices

    @staticmethod
    async def process_low_energy_save_mode(user_id: PyObjectId, percentage: float) -> bool:
        """Automatically enable save mode for low energy"""
        from app.config import settings
        
        if percentage <= settings.CRITICAL_THRESHOLD * 100:
            return await SaveModeService.enable_save_mode(
                user_id, 
                "auto_low_package"
            )
        return False