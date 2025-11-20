from datetime import datetime, timedelta
from typing import Optional, Any, Dict
from jose import JWTError, jwt
import bcrypt
from app.config import settings
import logging

# Logger setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        # Ensure password is encoded to bytes and check against hash
        return bcrypt.checkpw(
            plain_password.encode('utf-8'), 
            hashed_password.encode('utf-8')
        )
    except Exception as e:
        logger.error(f"Password verification error: {str(e)}")
        return False

def get_password_hash(password: str) -> str:
    try:
        # Encode password to bytes, hash it, and return as string
        password_bytes = password.encode('utf-8')
        
        # Truncate if longer than 72 bytes for bcrypt
        if len(password_bytes) > 72:
            password_bytes = password_bytes[:72]
            logger.warning("Password truncated to 72 bytes for bcrypt")
            
        hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
        return hashed.decode('utf-8')
    except Exception as e:
        logger.error(f"Password hashing error: {str(e)}")
        raise

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None

def watt_to_kwh(watt: float, hours: float = 1.0) -> float:
    """Convert watts to kWh"""
    return (watt * hours) / 1000

def calculate_percentage_remaining(remaining: float, total: float) -> float:
    """Calculate percentage remaining"""
    if total <= 0:
        return 0
    return (remaining / total) * 100

def format_timestamp_for_ai(timestamp: datetime) -> str:
    """Format timestamp for AI service"""
    return timestamp.isoformat()

def log_energy_event(user_id: str, event_type: str, details: str):
    """Log energy-related events"""
    logger.info(f"Energy Event - User: {user_id}, Type: {event_type}, Details: {details}")