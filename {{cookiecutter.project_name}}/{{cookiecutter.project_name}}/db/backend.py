import aioredis
from redis import from_url
from settings import settings

redis = aioredis.from_url(settings.REDIS_URI)
redis_db = from_url(settings.REDIS_URI)
