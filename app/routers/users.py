from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from app.database import get_collection
from app.auth import get_current_active_user
from app.models import User, UserResponse, UserCreate, PyObjectId
from app.utils import get_password_hash
from app.services.subscription_service import SubscriptionService

router = APIRouter()


@router.post("/register", response_model=UserResponse)
async def register_user(user_data: UserCreate):
    """Register a new user"""
    users_collection = get_collection("users")

    # Check if user already exists
    existing_user = await users_collection.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists",
        )

    # Check if meter_id already exists
    existing_meter = await users_collection.find_one({"meter_id": user_data.meter_id})
    if existing_meter:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Meter ID already registered",
        )

    # ⬅️ تم الإضافة: التحقق من صحة الباقة المختارة
    available_plans = await SubscriptionService.get_available_plans()
    if user_data.selected_plan not in [plan.id for plan in available_plans]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid plan selected"
        )

    # Create user
    user = User(
        name=user_data.name,
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        building_type=user_data.building_type,
        preferred_temp=user_data.preferred_temp,
        energy_goal=user_data.energy_goal,
        meter_id=user_data.meter_id,
        selected_plan=user_data.selected_plan,  # ⬅️ تم الإضافة
    )

    result = await users_collection.insert_one(user.dict(by_alias=True))

    # ⬅️ تم التعديل: إنشاء الباقة بناءً على الخطة المختارة
    subscription_success = await SubscriptionService.create_subscription_from_plan(
        user_id=result.inserted_id, plan_id=user_data.selected_plan
    )

    if not subscription_success:
        # If subscription creation fails, delete the user
        await users_collection.delete_one({"_id": result.inserted_id})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create subscription",
        )

    return UserResponse(
        id=str(result.inserted_id),
        name=user.name,
        email=user.email,
        building_type=user.building_type,
        preferred_temp=user.preferred_temp,
        energy_goal=user.energy_goal,
        save_mode=user.save_mode,
        meter_id=user.meter_id,
        selected_plan=user.selected_plan,  # ⬅️ تم الإضافة
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user(current_user: User = Depends(get_current_active_user)):
    """Get current user information"""
    return UserResponse(
        id=str(current_user.id),
        name=current_user.name,
        email=current_user.email,
        building_type=current_user.building_type,
        preferred_temp=current_user.preferred_temp,
        energy_goal=current_user.energy_goal,
        save_mode=current_user.save_mode,
        meter_id=current_user.meter_id,
        selected_plan=current_user.selected_plan,  # ⬅️ تم الإضافة
    )


@router.get("/{user_id}/subscription/percentage")
async def get_subscription_percentage(
    user_id: str, current_user: User = Depends(get_current_active_user)
):
    """Get user's subscription percentage"""
    if current_user.id != PyObjectId(user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this resource",
        )

    percentage = await SubscriptionService.get_subscription_percentage(
        PyObjectId(user_id)
    )
    if percentage is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No active subscription found"
        )

    return {"percentage": percentage}
