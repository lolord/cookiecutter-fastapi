import aioredis
import redis
from settings import settings

aio_redis: aioredis.Redis = aioredis.from_url(settings.REDIS_URI)  # type: ignore[no-untyped-call]
redis_db: redis.Redis = redis.from_url(settings.REDIS_URI)
