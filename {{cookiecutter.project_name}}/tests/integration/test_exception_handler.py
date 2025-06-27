from typing import Any

import anyio
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from inline_snapshot import snapshot
from starlette.exceptions import HTTPException

from {{cookiecutter.project_name}}.schemas.errors import (
    APIError,
    APIState,
    DataExistedError,
    DataInvalidError,
    DataNotFoundError,
    LoginFailedError,
    OperateInvalidError,
    PermissionDeniedError,
    QueryTimeoutError,
)
from {{cookiecutter.project_name}}.settings import settings


def test_RequestValidationError(mocker: Any, app: FastAPI, client: TestClient):
    url = app.url_path_for("auth:login")
    response = client.post(url, json={})
    assert response.status_code == snapshot(422)
    assert response.json()["detail"] == snapshot(
        [
            {
                "type": "missing",
                "loc": ["body", "password"],
                "msg": "Field required",
                "input": {},
            },
            {
                "type": "missing",
                "loc": ["body", "email"],
                "msg": "Field required",
                "input": {},
            },
        ]
    )


def test_HTTPException(mocker: Any, app: FastAPI, client: TestClient, tester_token_headers: str):
    mock_get = mocker.patch("{{cookiecutter.project_name}}.api.publics.app_description")
    mock_get.side_effect = HTTPException(status_code=500, detail="Mocked")
    url = app.url_path_for("publics:app")
    response = client.get(url, headers=tester_token_headers)
    assert response.status_code == snapshot(500)
    assert response.json()["detail"] == snapshot("Mocked")


def test_APIError(mocker: Any, app: FastAPI, client: TestClient, tester_token_headers: str):
    mock_get = mocker.patch("{{cookiecutter.project_name}}.api.publics.app_description")
    mock_get.side_effect = APIError(code=APIState.OTHER, msg="Mocked")
    url = app.url_path_for("publics:app")
    response = client.get(url, headers=tester_token_headers)
    assert response.status_code == snapshot(400)
    assert response.json()["msg"] == snapshot("Mocked")


@pytest.mark.parametrize(
    "err,code,msg",
    [
        (DataNotFoundError("Mocked"), snapshot(400), snapshot("Data Not Found: Mocked")),
        (DataExistedError("Mocked"), snapshot(400), snapshot("Data Existed:Mocked")),
        (DataInvalidError("Mocked"), snapshot(400), snapshot("Data Invalid: Mocked")),
        (OperateInvalidError("Mocked"), snapshot(400), snapshot("Operate Invalid: Mocked")),
        (QueryTimeoutError("Mocked"), snapshot(400), snapshot("Query Timeout Error: Mocked")),
        (PermissionDeniedError("Mocked"), snapshot(400), snapshot("Permission denied: Mocked")),
        (LoginFailedError("Mocked"), snapshot(400), snapshot("Login Error: Mocked")),
    ],
)
def test_errors(
    mocker: Any, app: FastAPI, client: TestClient, tester_token_headers: str, err: APIError, code: int, msg: str
):
    mock_get = mocker.patch("{{cookiecutter.project_name}}.api.publics.app_description")
    mock_get.side_effect = err
    url = app.url_path_for("publics:app")
    response = client.get(url, headers=tester_token_headers)
    assert response.status_code == code
    assert response.json()["msg"] == msg


def test_QueryTimeoutError1(mocker, app: FastAPI, client: TestClient, admin_token_headers: str):
    url = app.url_path_for("admin:users")
    old = settings.MONGO_QUERY_TIMEOUT
    settings.MONGO_QUERY_TIMEOUT = 0.1

    async def mock_get(*args, **kwargs):
        await anyio.sleep(1)

    mock_get = mocker.patch("{{cookiecutter.project_name}}.db.mongodb._get_count", new=mock_get)
    response = client.get(url, headers=admin_token_headers)
    assert response.status_code == 400, response.text
    assert response.json()["msg"] == snapshot("Query Timeout Error: collection=user query={'deleted': 0}")
    settings.MONGO_QUERY_TIMEOUT = old


def test_QueryTimeoutError2(mocker, app: FastAPI, client: TestClient, admin_token_headers: str):
    url = app.url_path_for("admin:users")
    old = settings.MONGO_QUERY_TIMEOUT
    settings.MONGO_QUERY_TIMEOUT = 0.5

    async def mock_get(*args, **kwargs):
        await anyio.sleep(1)

    mock_get = mocker.patch("{{cookiecutter.project_name}}.db.mongodb._get_instances", new=mock_get)

    response = client.get(url, headers=admin_token_headers)
    assert response.status_code == 400, response.text
    assert response.json()["msg"] == snapshot(
        "Query Timeout Error: collection=user query={'deleted': 0} sort=None skip=0 limit=10"
    )
    settings.MONGO_QUERY_TIMEOUT = old
