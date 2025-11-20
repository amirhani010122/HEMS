from fastapi import APIRouter, Depends, HTTPException, status
from app.auth import get_current_active_user
from app.models import User, SaveModeRequest
from app.services.save_mode_service import SaveModeService

router = APIRouter()


# -----------------------------
# Save Mode endpoints only
# -----------------------------
@router.post("/save_mode")
async def toggle_save_mode(
    request: SaveModeRequest, current_user: User = Depends(get_current_active_user)
):
    success = await SaveModeService.enable_save_mode(current_user.id, request.reason)
    if success:
        return {"status": "success", "message": f"Save mode enabled: {request.reason}"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to enable save mode",
        )


@router.delete("/save_mode")
async def disable_save_mode(current_user: User = Depends(get_current_active_user)):
    success = await SaveModeService.disable_save_mode(current_user.id)
    if success:
        return {"status": "success", "message": "Save mode disabled"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to disable save mode",
        )


@router.get("/save_mode/status")
async def get_save_mode_status(current_user: User = Depends(get_current_active_user)):
    status_info = await SaveModeService.get_save_mode_status(current_user.id)
    return status_info


@router.get("/get_commands")
async def get_device_commands(current_user: User = Depends(get_current_active_user)):
    status_info = await SaveModeService.get_save_mode_status(current_user.id)
    if status_info["save_mode"]:
        return {
            "commands": [status_info["command"]],
            "timestamp": status_info.get("activated_at"),
        }
    else:
        return {"commands": []}
