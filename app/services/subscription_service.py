from typing import Optional, List
from datetime import datetime, timedelta
from app.database import get_collection
from app.models import Subscription, PyObjectId, Plan, PlanResponse
from app.utils import calculate_percentage_remaining, log_energy_event
import logging

logger = logging.getLogger(__name__)


class SubscriptionService:
    @staticmethod
    def get_available_plans() -> List[PlanResponse]:
        """Get available subscription plans"""
        return [
            PlanResponse(
                id="basic",
                name="Basic Plan",
                total_kwh=50,
                price=10.0,
                duration_days=30,
                features=["Basic consumption reports", "Daily consumption monitoring"],
            ),
            PlanResponse(
                id="standard",
                name="Standard Plan",
                total_kwh=100,
                price=18.0,
                duration_days=30,
                features=[
                    "Basic consumption reports",
                    "Daily consumption monitoring",
                    "Consumption alerts",
                    "Auto save mode",
                ],
            ),
            PlanResponse(
                id="premium",
                name="Premium Plan",
                total_kwh=200,
                price=30.0,
                duration_days=30,
                features=[
                    "Basic consumption reports",
                    "Daily consumption monitoring",
                    "Consumption alerts",
                    "Auto save mode",
                    "AI predictions",
                    "Premium support",
                ],
            ),
        ]

    @staticmethod
    async def create_subscription_from_plan(user_id: PyObjectId, plan_id: str) -> bool:
        """Create a new subscription from a plan"""
        available_plans = SubscriptionService.get_available_plans()
        selected_plan = next(
            (plan for plan in available_plans if plan.id == plan_id), None
        )

        if not selected_plan:
            return False

        subscriptions_collection = get_collection("subscriptions")

        # حساب تاريخ الانتهاء بناءً على مدة الباقة
        start_date = datetime.utcnow()
        end_date = start_date + timedelta(days=selected_plan.duration_days)

        subscription = Subscription(
            user_id=user_id,
            plan_id=selected_plan.id,
            plan_name=selected_plan.name,
            total_kwh=selected_plan.total_kwh,
            remaining_kwh=selected_plan.total_kwh,
            price=selected_plan.price,
            start_date=start_date,
            end_date=end_date,
            status="active",
        )

        result = await subscriptions_collection.insert_one(
            subscription.dict(by_alias=True)
        )
        return result.acknowledged

    @staticmethod
    async def upgrade_plan(user_id: PyObjectId, new_plan_id: str) -> bool:
        """Upgrade user's subscription to a new plan"""
        available_plans = SubscriptionService.get_available_plans()
        new_plan = next(
            (plan for plan in available_plans if plan.id == new_plan_id), None
        )

        if not new_plan:
            return False

        subscriptions_collection = get_collection("subscriptions")

        # إلغاء تفعيل الباقة الحالية
        await subscriptions_collection.update_many(
            {"user_id": user_id, "status": "active"}, {"$set": {"status": "expired"}}
        )

        # إنشاء باقة جديدة
        start_date = datetime.utcnow()
        end_date = start_date + timedelta(days=new_plan.duration_days)

        new_subscription = Subscription(
            user_id=user_id,
            plan_id=new_plan.id,
            plan_name=new_plan.name,
            total_kwh=new_plan.total_kwh,
            remaining_kwh=new_plan.total_kwh,
            price=new_plan.price,
            start_date=start_date,
            end_date=end_date,
            status="active",
        )

        result = await subscriptions_collection.insert_one(
            new_subscription.dict(by_alias=True)
        )

        if result.acknowledged:
            log_energy_event(
                str(user_id),
                "PLAN_UPGRADED",
                f"Upgraded to {new_plan.name} with {new_plan.total_kwh}kWh",
            )
            return True
        return False

    # ⬅️ الطرق الحالية تبقى كما هي مع تعديلات بسيطة
    @staticmethod
    async def get_active_subscription(user_id: PyObjectId) -> Optional[Subscription]:
        """Get user's active subscription"""
        subscriptions_collection = get_collection("subscriptions")
        subscription_data = await subscriptions_collection.find_one(
            {
                "user_id": user_id,
                "status": "active",
                "end_date": {"$gte": datetime.utcnow()},
            }
        )

        if subscription_data:
            return Subscription(**subscription_data)
        return None

    @staticmethod
    async def deduct_energy(user_id: PyObjectId, kwh_used: float) -> bool:
        """Deduct energy consumption from subscription"""
        subscription = await SubscriptionService.get_active_subscription(user_id)
        if not subscription:
            logger.warning(f"No active subscription found for user {user_id}")
            return False

        if subscription.remaining_kwh < kwh_used:
            logger.warning(f"Insufficient energy for user {user_id}")
            return False

        subscriptions_collection = get_collection("subscriptions")
        result = await subscriptions_collection.update_one(
            {"_id": subscription.id}, {"$inc": {"remaining_kwh": -kwh_used}}
        )

        if result.modified_count > 0:
            new_remaining = subscription.remaining_kwh - kwh_used
            percentage = calculate_percentage_remaining(
                new_remaining, subscription.total_kwh
            )

            log_energy_event(
                str(user_id),
                "ENERGY_DEDUCTED",
                f"Deducted {kwh_used}kWh, remaining: {new_remaining}kWh ({percentage:.1f}%)",
            )

            return True

        return False

    @staticmethod
    async def get_subscription_percentage(user_id: PyObjectId) -> Optional[float]:
        """Get percentage of remaining energy"""
        subscription = await SubscriptionService.get_active_subscription(user_id)
        if not subscription:
            return None

        return calculate_percentage_remaining(
            subscription.remaining_kwh, subscription.total_kwh
        )

    @staticmethod
    async def get_user_subscriptions(user_id: PyObjectId) -> List[Subscription]:
        """Get all user subscriptions"""
        subscriptions_collection = get_collection("subscriptions")
        cursor = subscriptions_collection.find({"user_id": user_id}).sort(
            "start_date", -1
        )
        subscriptions = []
        async for doc in cursor:
            subscriptions.append(Subscription(**doc))
        return subscriptions

    @staticmethod
    async def create_subscription(subscription: Subscription) -> bool:
        """Create a new subscription (للتوافق مع الكود القديم)"""
        subscriptions_collection = get_collection("subscriptions")
        result = await subscriptions_collection.insert_one(
            subscription.dict(by_alias=True)
        )
        return result.acknowledged
