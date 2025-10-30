from motor.motor_asyncio import AsyncIOMotorClient
from config import settings

class MongoDB:
    client: AsyncIOMotorClient = None
    database = None

mongodb = MongoDB()

async def connect_to_mongo():
    mongodb.client = AsyncIOMotorClient(settings.MONGO_URI)
    mongodb.database = mongodb.client.get_database()
    print("Connected to MongoDB")
async def close_mongo_connection():
    mongodb.client.close()
    print("Disconnected from MongoDB")

def get_database():
    return mongodb.database