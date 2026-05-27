import os
import redis.asyncio as aioredis

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

redis: aioredis.Redis = None


async def init_db():
    global redis
    redis = aioredis.from_url(REDIS_URL, decode_responses=True)
    await redis.ping()
    print("Redis connected")


async def close_db():
    if redis:
        await redis.close()


def get_redis() -> aioredis.Redis:
    return redis
