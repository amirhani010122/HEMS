from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from app.auth import get_current_active_user
from app.models import User, Alert, PyObjectId
from app.services.alert_service import AlertService

router = APIRouter()

@router.get("/list", response_model=List[Alert])
async def get_alerts(
    read: Optional[bool] = None,
    limit: int = 50,
    current_user: User = Depends(get_current_active_user)
):
    """Get user alerts with optional filters"""
    return await AlertService.get_user_alerts(current_user.id, read, limit)

@router.get("/latest")
async def get_latest_alerts(current_user: User = Depends(get_current_active_user)):
    """Get latest unread alerts"""
    alerts = await AlertService.get_user_alerts(current_user.id, read=False, limit=10)
    unread_count = await AlertService.get_unread_count(current_user.id)
    
    return {
        "alerts": alerts,
        "unread_count": unread_count
    }

@router.post("/mark-as-read/{alert_id}")
async def mark_alert_as_read(
    alert_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Mark a specific alert as read"""
    success = await AlertService.mark_alert_as_read(PyObjectId(alert_id), current_user.id)
    
    if success:
        return {"status": "success", "message": "Alert marked as read"}
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )

@router.post("/mark-all-read")
async def mark_all_alerts_as_read(current_user: User = Depends(get_current_active_user)):
    """Mark all user alerts as read"""
    success = await AlertService.mark_all_alerts_as_read(current_user.id)
    
    if success:
        return {"status": "success", "message": "All alerts marked as read"}
    else:
        return {"status": "success", "message": "No unread alerts"}