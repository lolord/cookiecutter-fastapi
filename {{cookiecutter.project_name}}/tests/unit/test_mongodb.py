import re

import pytest
from inline_snapshot import snapshot
from odmantic.query import QueryExpression
from pydantic import BaseModel

from {{cookiecutter.project_name}}.db.mongodb import advanced_query, get_field, get_query_expression, get_sort_expression
from {{cookiecutter.project_name}}.models.user import User
from {{cookiecutter.project_name}}.schemas.errors import DataInvalidError
from {{cookiecutter.project_name}}.schemas.request import PaginationQuery


class TestQueryModel(BaseModel):
    email: str | None = None
    nickname: str | None = None


class TestPaginationQuery(PaginationQuery):
    email: str | None = None
    nickname: str | None = None


def test_get_field():
    field = get_field(User, "email")
    assert field == User.email


def test_get_field_invalid():
    with pytest.raises(DataInvalidError, match=f"Data Invalid: pet attribute of {+User}"):
        get_field(User, "pet")


@pytest.mark.asyncio
async def test_get_sort_expression():
    query = PaginationQuery(sort_by="email", sort_order="ascend")
    sort_expression = await get_sort_expression(User, query)
    assert str(sort_expression) == snapshot("SortExpression({'email': 1})")


@pytest.mark.asyncio
async def test_get_sort_expression_descend():
    query = PaginationQuery(sort_by="email", sort_order="descend")
    sort_expression = await get_sort_expression(User, query)
    assert str(sort_expression) == snapshot("SortExpression({'email': -1})")


@pytest.mark.asyncio
async def test_get_sort_expression_no_sort():
    query = PaginationQuery()
    sort_expression = await get_sort_expression(User, query)
    assert sort_expression is None


@pytest.mark.asyncio
async def test_get_sort_expression_invalid_field():
    query = PaginationQuery(sort_by="pet", sort_order="descend")
    with pytest.raises(DataInvalidError, match=f"Data Invalid: pet attribute of {+User}"):
        await get_sort_expression(User, query)


@pytest.mark.asyncio
async def test_get_sort_expression_invalid_order():
    query = PaginationQuery(sort_by="email", sort_order="asc")
    with pytest.raises(DataInvalidError, match="sort_order must be 'ascend' or 'descend'"):
        await get_sort_expression(User, query)


@pytest.mark.asyncio
async def test_advanced_query():
    query = PaginationQuery(q="test", keys=["email", "nickname"])
    result = await advanced_query(User, query)
    assert result == snapshot(
        QueryExpression(
            {"$or": (QueryExpression({"email": {"$eq": "test"}}), QueryExpression({"nickname": {"$eq": "test"}}))}
        )
    )


@pytest.mark.asyncio
async def test_advanced_query_re():
    query = PaginationQuery(q="test", keys=["re_email"])
    result = await advanced_query(User, query)
    assert result == snapshot(QueryExpression({"email": re.compile("test")}))


@pytest.mark.asyncio
async def test_advanced_query_no_keys():
    query = PaginationQuery(q="test", keys=["pet"])
    with pytest.raises(DataInvalidError, match=f"Data Invalid: pet attribute of {+User}"):
        await advanced_query(User, query)


@pytest.mark.asyncio
async def test_advanced_query_empty():
    query = PaginationQuery()
    result = await advanced_query(User, query)
    assert result == {}


@pytest.mark.asyncio
async def test_get_query_expression_base_model():
    query = TestQueryModel(email="test@test.com", nickname="test")
    result = await get_query_expression(User, query)
    assert result == snapshot({"email": "test@test.com", "nickname": "test"})


@pytest.mark.asyncio
async def test_get_query_expression_dict():
    query = {"email": "test@test.com", "nickname": "test"}
    result = await get_query_expression(User, query)
    assert result == query


@pytest.mark.asyncio
async def test_get_query_expression_pagination_query():
    query = TestPaginationQuery(email="test@test.com", nickname="test")
    result = await get_query_expression(User, query)
    assert result == snapshot({"email": "test@test.com", "nickname": "test"})


@pytest.mark.asyncio
async def test_get_query_expression_none():
    result = await get_query_expression(User, None)
    assert result == snapshot({})


@pytest.mark.asyncio
async def test_get_query_expression_extra_query_base_model():
    query = PaginationQuery()
    extra_query = TestQueryModel(email="test@test.com", nickname="test")
    result = await get_query_expression(User, query, extra_query)
    assert result == snapshot({"email": "test@test.com", "nickname": "test"})


@pytest.mark.asyncio
async def test_get_query_expression_extra_query_dict():
    query = PaginationQuery()
    extra_query = {"email": "test@test.com", "nickname": "test"}
    result = await get_query_expression(User, query, extra_query)
    assert result == snapshot({"email": "test@test.com", "nickname": "test"})
