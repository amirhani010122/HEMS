from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime
from bson import ObjectId
from enum import Enum

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

class UserBase(BaseModel):
    name: str
    email: EmailStr
    building_type: str = "Residential"
    preferred_temp: float = 24.0
    energy_goal: str = "Save 10%"

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}

class UserInDB(User):
    hashed_password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class DeviceStatus(str, Enum):
    ON = "ON"
    OFF = "OFF"

class DeviceBase(BaseModel):
    device_name: str
    room: str
    power_rating_watt: float
    status: DeviceStatus = DeviceStatus.OFF
    usage_duration_min: int = 0

class DeviceCreate(DeviceBase):
    user_id: str

class Device(DeviceBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId
    last_updated: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}

class ConsumptionBase(BaseModel):
    device_id: str
    power_usage_kwh: float
    total_power_watt: float
    devices_on: int
    temperature_c: float
    location: str

class ConsumptionCreate(ConsumptionBase):
    user_id: str

class Consumption(ConsumptionBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}

class EnvironmentBase(BaseModel):
    temperature_c: float
    humidity_percent: float
    light_intensity: float

class EnvironmentCreate(EnvironmentBase):
    user_id: str

class Environment(EnvironmentBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}

class PredictionBase(BaseModel):
    predicted_consumption_kwh: float
    suggestion: str
    risk_level: str
    model_version: str = "v1.0"

class PredictionCreate(PredictionBase):
    user_id: str

class Prediction(PredictionBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}

class AIResponse(BaseModel):
    predicted_consumption_kwh: float
    suggestion: str
    risk_level: str
    model_version: str