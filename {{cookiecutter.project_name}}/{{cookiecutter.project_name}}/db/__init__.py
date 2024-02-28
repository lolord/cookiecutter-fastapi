import asyncio

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from settings import settings

from .mongodb import (
    AIOEngine,
    get_instances,
    get_pagination,
    get_query_expression,
    get_sort_expression,
)

# odmantic for most service with ODM
client = AsyncIOMotorClient(settings.MONGO_URI)
client.get_io_loop = asyncio.get_running_loop
async_db = client[settings.MONGO_DB_NAME]
engine = AIOEngine(client, database=settings.MONGO_DB_NAME)
db = MongoClient(settings.MONGO_URI).get_database(settings.MONGO_DB_NAME)

__all__ = (
    "AIOEngine",
    "get_sort_expression",
    "get_query_expression",
    "get_pagination",
    "get_instances",
)
