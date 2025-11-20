import secrets
from typing import List, Optional
from datetime import datetime
from app.database import get_collection
from app.models import Device, PyObjectId
import logging

logger = logging.getLogger(__name__)


class DeviceService:
    @staticmethod
    def generate_api_key() -> str:
        """توليد مفتاح API عشوائي وآمن"""
        return f"HEMS_{secrets.token_urlsafe(24)}"

    @staticmethod
    async def create_device(device: Device) -> bool:
        """تسجيل جهاز جديد في النظام"""
        devices_collection = get_collection("devices")

        # التحقق من أن device_id غير مستخدم لنفس المستخدم
        existing_device = await devices_collection.find_one(
            {"device_id": device.device_id, "user_id": device.user_id}
        )

        if existing_device:
            return False

        result = await devices_collection.insert_one(device.dict(by_alias=True))
        return result.acknowledged

    @staticmethod
    async def get_device_by_api_key(api_key: str) -> Optional[Device]:
        """الحصول على بيانات الجهاز باستخدام API Key"""
        devices_collection = get_collection("devices")
        device_data = await devices_collection.find_one(
            {"api_key": api_key, "is_active": True}
        )

        if device_data:
            return Device(**device_data)
        return None

    @staticmethod
    async def get_user_devices(user_id: PyObjectId) -> List[Device]:
        """الحصول على جميع أجهزة المستخدم"""
        devices_collection = get_collection("devices")
        cursor = devices_collection.find({"user_id": user_id})

        devices = []
        async for doc in cursor:
            devices.append(Device(**doc))
        return devices

    @staticmethod
    async def deactivate_device(device_id: str, user_id: PyObjectId) -> bool:
        """إبطال جهاز (حذف منطقي)"""
        devices_collection = get_collection("devices")
        result = await devices_collection.update_one(
            {"device_id": device_id, "user_id": user_id}, {"$set": {"is_active": False}}
        )
        return result.modified_count > 0
