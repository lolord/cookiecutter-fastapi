import asyncio
import re
from typing import Dict, List, Optional, Type, TypeAlias, TypeVar, Union

from motor.motor_asyncio import AsyncIOMotorClient
from odmantic.bson import ObjectId
from odmantic.engine import AIOEngine as ODMAIOEngine
from odmantic.model import Model
from odmantic.query import QueryExpression, SortExpression, asc, desc
from pydantic import BaseModel
from pymongo import MongoClient

from {{cookiecutter.project_name}}.schemas import DBTimeoutError, PageResp, Pagination
from {{cookiecutter.project_name}}.settings import settings
from {{cookiecutter.project_name}}.utils.logger import logger

ModelType = TypeVar("ModelType", bound=Model)

QueryType: TypeAlias = Union[BaseModel, QueryExpression, Dict, bool]


async def get_sort_expression(
    model: Type[ModelType], query: QueryType
) -> Optional[SortExpression]:
    sort_by = getattr(query, "sort_by", None)
    sort_order = getattr(query, "sort_order", None)
    sort = None
    if sort_by:
        if sort_order == "descend":
            sort = desc(getattr(model, sort_by))
        elif sort_order == "ascend":
            sort = asc(getattr(model, sort_by))
    return sort


async def get_query_expression(
    query: Optional[QueryType],
    extra_query: Optional[QueryType] = None,
):
    if isinstance(query, BaseModel):
        query_dict = query.model_dump(
            exclude_unset=True,
            exclude_none=True,
            exclude={"page", "page_size", "sort_by", "sort_order"},
        )
    elif isinstance(query, dict):
        query_dict = query
    else:
        query_dict = {}

    if extra_query:
        if isinstance(extra_query, BaseModel):
            query_dict.update(extra_query.model_dump())
        elif isinstance(extra_query, dict):
            query_dict.update(extra_query)
        else:
            raise ValueError(f"Invalid query expression: {query_dict}")
    q = query_dict.pop("q", None)
    keys = query_dict.pop("keys", None)
    if q and keys:
        query_dict["$or"] = []
        for f in keys:
            if f == "_id":
                try:
                    query_dict["$or"].append({f: ObjectId(q.strip())})
                except Exception:
                    """nothing"""
            elif f.startswith("re_"):
                query_dict["$or"].append(
                    {f.replace("re_", "", 1): {"$regex": re.compile(q.strip())}}
                )
            else:
                query_dict["$or"].append({f: q.strip()})

    logger.info(f"query_dict {query_dict}")
    return query_dict


async def get_pagination(
    engine: "AIOEngine",
    model: Type[ModelType],
    query: QueryType,
    extra_query: Optional[QueryType] = None,
):
    page_size = getattr(query, "page_size", 10)
    page = getattr(query, "page", 1)
    query_dict = await get_query_expression(query, extra_query)

    if query_dict:
        coro = engine.client[engine.database_name][+model].count_documents(query_dict)
    else:
        coro = engine.get_collection(model).estimated_document_count()
    try:
        total_count = await asyncio.wait_for(coro, timeout=settings.MONGO_TIMROUT)
    except asyncio.TimeoutError:
        raise DBTimeoutError(f"DBTimeoutError: {model} {query_dict}")

    return Pagination(
        page=page,
        page_size=page_size,
        total_count=total_count,
    )


async def get_instances(
    engine: "AIOEngine",
    model: Type[ModelType],
    query: QueryType,
    extra_query: Optional[QueryType] = None,
    **extra,
) -> List[ModelType]:
    query_dict = await get_query_expression(query, extra_query)
    sort = await get_sort_expression(model, query)
    # sort需要配合修改
    # data = await motor_find(model, query_dict, skip=pagination.start, limit=page_size, sort=sort)
    # find在init里面替换成motor_find
    return await engine.find(model, query_dict, sort=sort, **extra)


async def find_pagination(
    engine: "AIOEngine",
    model: Type[ModelType],
    query: QueryType,
    extra_query: Optional[QueryType] = None,
):
    pagination = await get_pagination(engine, model, query, extra_query)
    data = await get_instances(
        engine,
        model,
        query,
        extra_query,
        skip=(pagination.page - 1) * pagination.page_size,
        limit=pagination.page_size,
    )
    res = PageResp(data=data, pagination=pagination)
    return res


async def paginate_aggregate(
    engine: "AIOEngine", model: Type[ModelType], query, extra_query
) -> PageResp[ModelType]:
    aggregate_pipeline = []
    query_dict = await get_query_expression(query, extra_query)

    if query_dict:
        aggregate_pipeline.append({"$match": query_dict})
    sort = await get_sort_expression(model, query)
    if sort is not None:
        aggregate_pipeline.append({"$sort": sort})

    page_size = getattr(query, "page_size", 10)
    page = getattr(query, "page", 1)

    paginate_data = [{"$skip": page_size * page}, {"$linit": page_size}]

    cursor = engine.get_collection(model).aggregate(
        [
            *aggregate_pipeline,
            {
                "$facet": {
                    "metadata": [{"$count": "total"}],
                    "data": paginate_data,
                }
            },
        ]
    )

    data = (await cursor.to_list(length=None))[0]

    data = data["data"]
    try:
        total = data["metadata"][0]["total"]
    except IndexError:
        total = 0

    pagination = Pagination(
        page=page,
        page_size=page_size,
        total_count=total,
    )

    return PageResp(data=data, pagination=pagination)


class AIOEngine(ODMAIOEngine):
    async def find_pagination(
        self, model: Type[ModelType], query, extra_query=None
    ) -> PageResp[ModelType]:
        return await find_pagination(self, model, query, extra_query)

    async def exists(self, model: Type[ModelType], *queries) -> bool:
        return await self.find_one(model, *queries) is not None

    async def upsert(self, instance: ModelType, *queries) -> ModelType:
        model: Type[ModelType] = type(instance)
        old = await self.find_one(model, *queries)
        if old and instance.id != old.id:
            old.model_update(
                instance.model_dump(exclude={model.__primary_field__, "id"})
            )
            return await self.save(old)
        else:
            return await self.save(instance)


# odmantic for most service with ODM
client = AsyncIOMotorClient(settings.MONGO_URI)
client.get_io_loop = asyncio.get_running_loop
async_db = client[settings.MONGO_DB_NAME]
engine = AIOEngine(client, database=settings.MONGO_DB_NAME)
db = MongoClient(settings.MONGO_URI).get_database(settings.MONGO_DB_NAME)
