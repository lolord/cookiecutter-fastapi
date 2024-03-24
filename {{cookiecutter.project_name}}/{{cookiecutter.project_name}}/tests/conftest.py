from __future__ import absolute_import

from datetime import timedelta

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pytest import FixtureRequest, Parser

from {{cookiecutter.project_name}}.api.user import User
from {{cookiecutter.project_name}}.db.mongodb import db
from {{cookiecutter.project_name}}.main import app as test_app
from {{cookiecutter.project_name}}.services.security import (
    create_access_token,
    get_password_hash,
)
from {{cookiecutter.project_name}}.settings import settings


def pytest_configure(config):
    """配置 markers, 结合命令行参数-m使用:
    在命令行通过-m指定运行mark打标的case
    $ pytest -v -m unit
    反选
    $ pytest -v -m "not unit"
    """

    config.addinivalue_line("markers", "unit: tests for Unit Test")
    config.addinivalue_line("markers", "sit: tests for System Integration Test")
    config.addinivalue_line("markers", "uat: tests for User Acceptance Test")


def pytest_addoption(parser: Parser):
    """配置自定义命令行参数"""
    mongo_uri = parser.addoption("--mongo", help="set mongo uri")
    if mongo_uri:
        settings.MONGO_URI = mongo_uri
    redis_host = parser.addoption("--redis", help="set redis host")
    if redis_host:
        settings.REDIS_HOST = redis_host


def pytest_report_header(config):
    """配置报告头信息"""


@pytest.fixture
def redis_uri(request: FixtureRequest):
    """获取命令行参数 redis_uri"""
    return request.config.getoption("--redis")


@pytest.fixture
def mongo_uri(request: FixtureRequest):
    """获取命令行参数 mongo_uri"""
    return request.config.getoption("--mongo")


@pytest.fixture(scope="module")
def app() -> FastAPI:
    return test_app


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(app=test_app)


@pytest.fixture(scope="module")
def admin_raw():
    return {
        "email": "admin@admin.com",
        "nickname": "admin",
        "roles": ["admin"],
        "password": "!QAZ2wsx",
    }


@pytest.fixture(scope="module")
def admin(admin_raw: dict):
    user = User(**admin_raw)
    data = user.model_dump()
    data["hashed_password"] = get_password_hash(admin_raw["password"])
    email = data.pop("email")
    db[+User].update_one({"email": email}, {"$set": data}, upsert=True)

    return user


@pytest.fixture(scope="module")
def admin_token(admin: User):
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return create_access_token(
        data={"sub": admin.email}, expires_delta=access_token_expires
    )


@pytest.fixture(scope="module")
def tester_raw():
    return {
        "email": "tester@email.com",
        "nickname": "tester",
        "password": "!QAZ2wsx",
    }


@pytest.fixture(scope="module")
def tester(tester_raw: dict):
    user = User(**tester_raw)
    data = user.model_dump()
    data["hashed_password"] = get_password_hash(tester_raw["password"])
    email = data.pop("email")
    db[+User].update_one({"email": email}, {"$set": data}, upsert=True)

    return user


@pytest.fixture(scope="module")
def tester_token(tester: User):
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return create_access_token(
        data={"sub": tester.email}, expires_delta=access_token_expires
    )
