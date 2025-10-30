from fastapi import APIRouter, HTTPException
from app.database import get_database
from app.models import Device, DeviceCreate, DeviceStatus
from bson import ObjectId

router = APIRouter(prefix="/devices", tags=["devices"])

@router.post("/", response_model=Device)
async def create_device(device: DeviceCreate):
    db = get_database()
    
    if not ObjectId.is_valid(device.user_id):
        raise HTTPException(status_code=400, detail="Invalid user ID")
    
    device_dict = device.dict()
    device_dict["user_id"] = ObjectId(device.user_id)
    
    result = await db.devices.insert_one(device_dict)
    new_device = await db.devices.find_one({"_id": result.inserted_id})
    
    return Device(**new_device)

@router.get("/user/{user_id}", response_model=list[Device])
async def get_user_devices(user_id: str):
    db = get_database()
    
    if not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=400, detail="Invalid user ID")
    
    devices = await db.devices.find({"user_id": ObjectId(user_id)}).to_list(1000)
    return [Device(**device) for device in devices]

@router.put("/{device_id}/status", response_model=Device)
async def update_device_status(device_id: str, status: DeviceStatus):
    db = get_database()
    
    if not ObjectId.is_valid(device_id):
        raise HTTPException(status_code=400, detail="Invalid device ID")
    
    await db.devices.update_one(
        {"_id": ObjectId(device_id)},
        {"$set": {"status": status, "last_updated": ObjectId(device_id).generation_time}}
    )
    
    updated_device = await db.devices.find_one({"_id": ObjectId(device_id)})
    if not updated_device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    return Device(**updated_device)

@router.delete("/{device_id}")
async def delete_device(device_id: str):
    db = get_database()
    
    if not ObjectId.is_valid(device_id):
        raise HTTPException(status_code=400, detail="Invalid device ID")
    
    result = await db.devices.delete_one({"_id": ObjectId(device_id)})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Device not found")
    
    return {"message": "Device deleted successfully"}