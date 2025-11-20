from typing import List, Optional
from datetime import datetime
from app.database import get_collection
from app.models import Alert, PyObjectId
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class AlertService:
    _triggered_thresholds = {}  # Track triggered alerts per user

    @staticmethod
    async def create_alert(
        user_id: PyObjectId,
        alert_type: str,
        percentage: float,
        message: str,
        auto_triggered: bool = True,
    ) -> bool:
        """Create a new alert"""
        alerts_collection = get_collection("alerts")

        alert = Alert(
            user_id=user_id,
            alert_type=alert_type,
            percentage=percentage,
            message=message,
            timestamp=datetime.utcnow(),
            auto_triggered=auto_triggered,
        )

        result = await alerts_collection.insert_one(alert.dict(by_alias=True))

        if result.acknowledged:
            logger.info(f"Alert created for user {user_id}: {alert_type} - {message}")
            return True
        return False

    @staticmethod
    async def check_and_create_alerts(
        user_id: PyObjectId, percentage: float
    ) -> List[str]:
        """Check thresholds and create alerts if needed"""
        from app.services.subscription_service import SubscriptionService

        triggered_alerts = []
        user_key = str(user_id)

        # Check each threshold
        thresholds = [
            (
                settings.WARNING_THRESHOLD * 100,
                "WARNING",
                "Energy package at 20% remaining",
            ),
            (
                settings.CRITICAL_THRESHOLD * 100,
                "CRITICAL",
                "Energy package at 10% remaining - Save Mode activated",
            ),
            (
                settings.FINAL_THRESHOLD * 100,
                "FINAL",
                "Energy package at 5% remaining - Immediate action required",
            ),
        ]

        for threshold, alert_type, message in thresholds:
            if (
                percentage <= threshold
                and user_key
                not in AlertService._triggered_thresholds.get(alert_type, set())
            ):

                await AlertService.create_alert(
                    user_id, alert_type, percentage, message
                )
                triggered_alerts.append(alert_type)

                # Mark this threshold as triggered for this user
                if alert_type not in AlertService._triggered_thresholds:
                    AlertService._triggered_thresholds[alert_type] = set()
                AlertService._triggered_thresholds[alert_type].add(user_key)

        return triggered_alerts

    @staticmethod
    async def get_user_alerts(
        user_id: PyObjectId, read: Optional[bool] = None, limit: int = 50
    ) -> List[Alert]:
        """Get user alerts with optional filters"""
        alerts_collection = get_collection("alerts")
        query = {"user_id": user_id}
        if read is not None:
            query["read"] = read

        cursor = alerts_collection.find(query).sort("timestamp", -1).limit(limit)
        alerts = []
        async for doc in cursor:
            alerts.append(Alert(**doc))
        return alerts

    @staticmethod
    async def mark_alert_as_read(alert_id: PyObjectId, user_id: PyObjectId) -> bool:
        """Mark an alert as read"""
        alerts_collection = get_collection("alerts")
        result = await alerts_collection.update_one(
            {"_id": alert_id, "user_id": user_id}, {"$set": {"read": True}}
        )
        return result.modified_count > 0

    @staticmethod
    async def mark_all_alerts_as_read(user_id: PyObjectId) -> bool:
        """Mark all user alerts as read"""
        alerts_collection = get_collection("alerts")
        result = await alerts_collection.update_many(
            {"user_id": user_id, "read": False}, {"$set": {"read": True}}
        )
        return result.modified_count > 0

    @staticmethod
    async def get_unread_count(user_id: PyObjectId) -> int:
        """Get count of unread alerts"""
        alerts_collection = get_collection("alerts")
        return await alerts_collection.count_documents(
            {"user_id": user_id, "read": False}
        )
