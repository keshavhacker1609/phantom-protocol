import redis.asyncio as aioredis
from core.config import settings
from utils.logger import get_logger

logger = get_logger(__name__)

_redis_client: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
            max_connections=20,
        )
    return _redis_client


async def close_redis():
    global _redis_client
    if _redis_client:
        await _redis_client.aclose()
        _redis_client = None
        logger.info("Redis connection closed")


async def publish_event(channel: str, message: str) -> int:
    r = await get_redis()
    return await r.publish(channel, message)


async def set_with_ttl(key: str, value: str, ttl: int = 300):
    r = await get_redis()
    await r.setex(key, ttl, value)


async def get_value(key: str) -> str | None:
    r = await get_redis()
    return await r.get(key)


async def delete_key(key: str):
    r = await get_redis()
    await r.delete(key)


async def increment(key: str, ttl: int = 86400) -> int:
    r = await get_redis()
    pipe = r.pipeline()
    await pipe.incr(key)
    await pipe.expire(key, ttl)
    results = await pipe.execute()
    return results[0]
