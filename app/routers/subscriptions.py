from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from app.auth import get_current_active_user
from app.models import User, Subscription, PlanResponse, UpgradePlanRequest
from app.services.subscription_service import SubscriptionService
from app.database import get_collection

router = APIRouter()


@router.get("/plans", response_model=List[PlanResponse])
async def get_available_plans():
    """Get available subscription plans"""
    return SubscriptionService.get_available_plans()  # ⬅️ بدون await


@router.get("/my-subscriptions", response_model=List[Subscription])
async def get_my_subscriptions(current_user: User = Depends(get_current_active_user)):
    """Get current user's subscriptions"""
    return await SubscriptionService.get_user_subscriptions(current_user.id)


@router.get("/active")
async def get_active_subscription(
    current_user: User = Depends(get_current_active_user),
):
    """Get user's active subscription"""
    subscription = await SubscriptionService.get_active_subscription(current_user.id)

    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No active subscription found"
        )

    return subscription


@router.post("/upgrade")
async def upgrade_plan(
    upgrade_request: UpgradePlanRequest,
    current_user: User = Depends(get_current_active_user),
):
    """Upgrade user's subscription plan"""
    # التحقق من صحة الباقة المختارة
    available_plans = SubscriptionService.get_available_plans()  # ⬅️ بدون await
    if upgrade_request.plan_id not in [plan.id for plan in available_plans]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid plan ID"
        )

    # ترقية الباقة
    success = await SubscriptionService.upgrade_plan(
        user_id=current_user.id, new_plan_id=upgrade_request.plan_id
    )

    if success:
        # تحديث الباقة المختارة في بيانات المستخدم
        users_collection = get_collection("users")
        await users_collection.update_one(
            {"_id": current_user.id},
            {"$set": {"selected_plan": upgrade_request.plan_id}},
        )

        return {
            "status": "success",
            "message": f"Plan upgraded to {upgrade_request.plan_id}",
            "new_plan": upgrade_request.plan_id,
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upgrade plan",
        )


@router.get("/my-plan")
async def get_my_plan(current_user: User = Depends(get_current_active_user)):
    """Get current user's active plan details"""
    active_subscription = await SubscriptionService.get_active_subscription(
        current_user.id
    )
    if not active_subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No active subscription found"
        )

    # الحصول على تفاصيل الباقة
    available_plans = SubscriptionService.get_available_plans()  # ⬅️ بدون await
    plan_details = next(
        (plan for plan in available_plans if plan.id == active_subscription.plan_id),
        None,
    )

    if not plan_details:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Plan details not found"
        )

    return {"subscription": active_subscription, "plan_details": plan_details}
