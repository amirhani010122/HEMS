import asyncio
from database import connect_to_mongo, get_database

async def main():
    # 1. اتصل بقاعدة البيانات
    await connect_to_mongo()
    
    # 2. خذ قاعدة البيانات
    db = get_database()
    
    # 3. اختار collection
    users_collection = db.sonsubtion
    
    # 4. أضف مستند جديد
    await users_collection.insert_one({"name": "karin"})
    # print("Inserted ID:", result.inserted_id)

asyncio.run(main())


