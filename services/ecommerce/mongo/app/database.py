import os
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie

MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.getenv("MONGO_DB", "benchmark_db")

client: AsyncIOMotorClient = None


async def init_db(document_models: list):
    global client
    client = AsyncIOMotorClient(
        MONGO_URL,
        maxPoolSize=100,       
        minPoolSize=10,         
        waitQueueTimeoutMS=5000 
    )
    await init_beanie(database=client[DB_NAME], document_models=document_models)


async def close_db():
    if client:
        client.close()