from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr, validator
from bson import ObjectId
import json


class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")


# ⬇️⬇️⬇️ النماذج الجديدة للباقات ⬇️⬇️⬇️
class Plan(BaseModel):
    id: str  # basic, standard, premium
    name: str
    total_kwh: float
    price: float
    duration_days: int
    features: List[str]


class PlanResponse(BaseModel):
    id: str
    name: str
    total_kwh: float
    price: float
    duration_days: int
    features: List[str]


class User(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    hashed_password: str
    building_type: str
    preferred_temp: float = Field(24.0, ge=15.0, le=30.0)
    energy_goal: Optional[str] = None
    save_mode: bool = False
    save_mode_reason: Optional[str] = None
    meter_id: str = Field(...)
    selected_plan: str = Field(default="basic")  # ⬅️ الجديد

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    building_type: str
    preferred_temp: float = 24.0
    energy_goal: Optional[str] = None
    meter_id: str = Field(...)
    selected_plan: str = Field(default="basic")  # ⬅️ الجديد


class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    building_type: str
    preferred_temp: float
    energy_goal: Optional[str]
    save_mode: bool
    meter_id: str
    selected_plan: str  # ⬅️ الجديد


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None


class Subscription(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId
    plan_id: str  # ⬅️ تحديث: نستخدم plan_id بدل plan_name
    plan_name: str
    total_kwh: float = Field(..., gt=0)
    remaining_kwh: float = Field(..., ge=0)
    price: float = Field(..., ge=0)  # ⬅️ تحديث: سعر الباقة
    start_date: datetime
    end_date: datetime
    status: str

    @validator("status")
    def validate_status(cls, v):
        if v not in ["active", "expired", "cancelled"]:
            raise ValueError("Status must be active, expired, or cancelled")
        return v

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class Consumption(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId
    device_id: str
    power_usage_kwh: float = Field(..., ge=0)
    total_power_watt: float = Field(..., ge=0)
    timestamp: datetime
    temperature: Optional[float] = None
    devices_on: int = Field(..., ge=0)
    devices_off: int = Field(..., ge=0)
    location: str

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class Prediction(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId
    prediction_type: str
    suggestions: List[str]
    timestamp: datetime
    source: str = "external_ai_service"

    @validator("prediction_type")
    def validate_prediction_type(cls, v):
        if v not in ["daily", "weekly", "monthly"]:
            raise ValueError("Prediction type must be daily, weekly, or monthly")
        return v

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class Alert(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId
    alert_type: str
    percentage: float = Field(..., ge=0, le=100)
    message: str
    timestamp: datetime
    read: bool = False
    auto_triggered: bool = True

    @validator("alert_type")
    def validate_alert_type(cls, v):
        if v not in ["WARNING", "CRITICAL", "FINAL"]:
            raise ValueError("Alert type must be WARNING, CRITICAL, or FINAL")
        return v

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class SensorData(BaseModel):
    device_id: str
    meter_id: str
    total_power_watt: float = Field(..., ge=0)
    timestamp: Optional[datetime] = None
    temperature: Optional[float] = None
    devices_on: int = Field(..., ge=0)
    devices_off: int = Field(..., ge=0)
    location: str


class SaveModeCommand(BaseModel):
    action: str = "save_mode"
    devices_to_turn_off: List[str] = ["AC", "Heater", "WaterBoiler"]
    priority: str = "high"


class SaveModeRequest(BaseModel):
    reason: str

    @validator("reason")
    def validate_reason(cls, v):
        if v not in ["manual", "auto_low_package"]:
            raise ValueError("Reason must be manual or auto_low_package")
        return v


class ConsumptionAggregation(BaseModel):
    period: str
    total_consumption_kwh: float
    average_power_watt: float
    timestamp: datetime


# ⬇️⬇️⬇️ نموذج لترقية الباقة ⬇️⬇️⬇️
class UpgradePlanRequest(BaseModel):
    plan_id: str

    @validator("plan_id")
    def validate_plan_id(cls, v):
        if v not in ["basic", "standard", "premium"]:
            raise ValueError("Plan ID must be basic, standard, or premium")
        return v
