from __future__ import absolute_import

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from {{cookiecutter.project_name}}.api.user import User
from {{cookiecutter.project_name}}.db.mongodb import db
from {{cookiecutter.project_name}}.main import app as test_app
from {{cookiecutter.project_name}}.services.security import get_password_hash


def pytest_configure(config):
    config.addinivalue_line("markers", "control: tests for Control")
    config.addinivalue_line("markers", "scheduler: tests for Scheduler")
    config.addinivalue_line("markers", "memcached: tests for Memcached")
    config.addinivalue_line("markers", "redis: tests for Redis")
    config.addinivalue_line("markers", "fakeredis: tests for Fake Redis")
    config.addinivalue_line("markers", "sentinel: tests for Redis Sentinel")
    config.addinivalue_line("markers", "settings: tests for Settings and Configuration")  # noqa E501
    config.addinivalue_line("markers", "logger: tests for Logger")


@pytest.fixture(scope="module")
def app() -> FastAPI:
    return test_app


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(test_app)


admin_raw = {
    "email": "admin@admin.com",
    "nickname": "admin",
    "roles": ["admin"],
    "password": "!QAZ2wsx",
}


@pytest.fixture(scope="module")
def admin(client):
    user = User(**admin_raw)  # type: ignore
    data = user.model_dump()
    data["hashed_password"] = get_password_hash(admin_raw["password"])
    email = data.pop("email")
    db[+User].update_one({"email": email}, {"$set": data}, upsert=True)

    return user


@pytest.fixture(scope="module")
def admin_token(admin: User, client):
    url = test_app.url_path_for("auth:login")
    data = admin_raw
    response = client.post(url, json=data)
    assert response.status_code == 200
    return response.json()["data"]["access_token"]


tester_raw = {
    "email": "tester@email.com",
    "nickname": "tester",
    "password": "!QAZ2wsx",
}


@pytest.fixture(scope="module")
def tester(client):
    user = db[+User].find_one({"email": tester_raw["email"]})
    if not user:
        url = test_app.url_path_for("auth:register")
        data = tester_raw
        response = client.post(url, json=data)
        assert response.status_code == 200
        user = db[+User].find_one({"email": tester_raw["email"]})

    return User(**user)  # type: ignore


@pytest.fixture(scope="module")
def tester_token(app: FastAPI, tester: User, client):
    url = app.url_path_for("auth:login")
    data = tester_raw
    response = client.post(url, json=data)
    assert response.status_code == 200
    return response.json()["data"]["access_token"]
