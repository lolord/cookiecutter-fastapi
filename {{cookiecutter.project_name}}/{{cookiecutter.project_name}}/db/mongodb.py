import asyncio
from typing import Any, Dict, List, Optional, Type, TypeAlias, Union

from anyio import fail_after
from motor.motor_asyncio import AsyncIOMotorClient
from odmantic.engine import AIOEngine as ODMAIOEngine
from odmantic.engine import AIOSessionType, ModelType
from odmantic.query import QueryExpression, SortExpression, asc, desc, or_
from odmantic.query import match as match_
from pydantic import BaseModel
from pymongo import MongoClient
from pymongo.database import Database

from {{cookiecutter.project_name}}.schemas import (
    PageResp,
    Pagination,
    QueryTimeoutError,
)
from {{cookiecutter.project_name}}.schemas.errors import DataInvalidError, DataNotFoundError
from {{cookiecutter.project_name}}.schemas.request import PaginationQuery
from {{cookiecutter.project_name}}.settings import settings
from {{cookiecutter.project_name}}.utils.logger import logger

QueryType: TypeAlias = Union[BaseModel, QueryExpression, Dict, bool]
ExtraQueryType: TypeAlias = Union[BaseModel, Dict]


def get_field(model: Type[ModelType], name: str) -> Optional[Any]:
    """
    Get a field from the model by its name.
    """
    if hasattr(model, name):
        return getattr(model, name)
    raise DataInvalidError(f"{name} attribute of {+model}")


async def get_sort_expression(model: Type[ModelType], query: QueryType) -> Optional[SortExpression]:
    sort_by = getattr(query, "sort_by", None)
    sort_order = getattr(query, "sort_order", None)
    sort = None
    if sort_by:
        field = get_field(model, sort_by)
        if sort_order == "descend":
            sort = desc(field)
        elif sort_order == "ascend":
            sort = asc(field)
        else:
            raise DataInvalidError("sort_order must be 'ascend' or 'descend'")
    return sort


async def advanced_query(model: Type[ModelType], query: PaginationQuery) -> dict:
    queries = []
    q = getattr(query, "q", None)
    keys = getattr(query, "keys", None)
    if q and keys:
        for field_name in keys:
            if field_name.startswith("re_"):
                field = get_field(model, field_name.replace("re_", "", 1))
                queries.append(match_(field, q.strip()))
            else:
                queries.append(get_field(model, field_name) == q.strip())
        if len(queries) == 1:
            return queries[0]
        return or_(*queries)
    return {}


async def get_query_expression(
    model: Type[ModelType],
    query: QueryType | None,
    extra_query: Optional[ExtraQueryType] = None,
) -> dict:
    if isinstance(query, BaseModel):
        query_dict = query.model_dump(
            exclude_unset=True,
            exclude_none=True,
            exclude={"page", "page_size", "sort_by", "sort_order", "q", "keys"},
        )
        if isinstance(query, PaginationQuery):
            query_dict.update(await advanced_query(model, query))
    elif isinstance(query, dict):
        query_dict = query
    else:
        query_dict = {}

    if extra_query:
        if isinstance(extra_query, BaseModel):
            query_dict.update(extra_query.model_dump())
        if isinstance(extra_query, dict):
            query_dict.update(extra_query)

    return query_dict


async def _get_count(engine: "AIOEngine", model: Type[ModelType], query_dict: dict) -> int:
    if query_dict:
        return await engine.client[engine.database_name][+model].count_documents(query_dict)
    else:
        return await engine.get_collection(model).estimated_document_count()


async def get_pagination(
    engine: "AIOEngine",
    model: Type[ModelType],
    query: QueryType,
    extra_query: Optional[ExtraQueryType] = None,
) -> Pagination:
    page_size = getattr(query, "page_size", 10)
    page = getattr(query, "page", 1)
    query_dict = await get_query_expression(model, query, extra_query)

    try:
        with fail_after(settings.MONGO_QUERY_TIMEOUT):
            total_count = await _get_count(engine, model, query_dict)
    except TimeoutError:
        raise QueryTimeoutError(f"collection={+model} query={query_dict}")

    return Pagination(page=page, page_size=page_size, total_count=total_count)


async def _get_instances(
    engine: "AIOEngine",
    model: Type[ModelType],
    query_dict: dict,
    sort: Optional[SortExpression] = None,
    skip: int = 0,
    limit: Optional[int] = None,
    session: AIOSessionType = None,
) -> List[ModelType]:
    return await engine.find(model, query_dict, sort=sort, skip=skip, limit=limit, session=session)


async def get_instances(
    engine: "AIOEngine",
    model: Type[ModelType],
    query: QueryType,
    extra_query: Optional[ExtraQueryType] = None,
    skip: int = 0,
    limit: Optional[int] = None,
    session: AIOSessionType = None,
) -> List[ModelType]:
    query_dict = await get_query_expression(model, query, extra_query)
    sort = await get_sort_expression(model, query)
    logger.info(f"query_dict {query_dict}")
    logger.info(f"sort {sort}")
    try:
        with fail_after(settings.MONGO_QUERY_TIMEOUT):
            return await _get_instances(engine, model, query_dict, sort=sort, skip=skip, limit=limit, session=session)
    except TimeoutError:
        raise QueryTimeoutError(f"collection={+model} query={query_dict} {sort=} {skip=} {limit=}")


async def find_pagination(
    engine: "AIOEngine",
    model: Type[ModelType],
    query: QueryType,
    extra_query: Optional[ExtraQueryType] = None,
) -> PageResp[ModelType]:
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
    engine: "AIOEngine",
    model: Type[ModelType],
    query: QueryType,
    extra_query: ExtraQueryType | None = None,
) -> PageResp[ModelType]:  # pragma: no cover
    aggregate_pipeline = []
    query_dict = await get_query_expression(model, query, extra_query)

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
        self, model: Type[ModelType], query: QueryType, extra_query: dict | None = None
    ) -> PageResp[ModelType]:
        resp: PageResp[ModelType] = await find_pagination(self, model, query, extra_query)
        return resp

    async def exists(self, model: Type[ModelType], *queries: QueryExpression | Dict | bool) -> bool:
        return await self.find_one(model, *queries) is not None

    async def upsert_one(self, instance: ModelType, *queries: QueryExpression | Dict | bool) -> ModelType:
        model: Type[ModelType] = type(instance)
        old = await self.find_one(model, *queries)
        if old and instance.id != old.id:
            old.model_update(instance.model_dump(exclude={model.__primary_field__, "id"}))
            return await self.save(old)
        else:
            return await self.save(instance)

    async def must_find_one(
        self,
        model: Type[ModelType],
        sort: Optional[Any] = None,
        session: AIOSessionType = None,
        **queries: Any,
    ) -> ModelType:
        _queries = [getattr(model, k) == v for k, v in queries.items()]
        data = await self.find_one(model, *_queries, sort=sort, session=session)
        if data is None:
            name = model.__name__
            args = ", ".join(f"{k}={v}" for k, v in queries.items())
            raise DataNotFoundError(data=f"{name}({args})")
        return data


# odmantic for most service with ODM
client: AsyncIOMotorClient = AsyncIOMotorClient(settings.MONGO_URI)
client.get_io_loop = asyncio.get_running_loop  # type: ignore
async_db = client[settings.MONGO_DB_NAME]
engine: AIOEngine = AIOEngine(client, database=settings.MONGO_DB_NAME)
db: Database = MongoClient(settings.MONGO_URI).get_database(settings.MONGO_DB_NAME)
