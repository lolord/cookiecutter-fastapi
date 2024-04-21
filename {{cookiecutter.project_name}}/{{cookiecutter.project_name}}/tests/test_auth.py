from datetime import datetime

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from {{cookiecutter.project_name}}.models.user import User
from {{cookiecutter.project_name}}.schemas.response import APIState, Resp
from {{cookiecutter.project_name}}.settings import settings


@pytest.mark.run(order=1)
def test_register_closed(app: FastAPI, client: TestClient, admin: User):
    settings.USERS_OPEN_REGISTRATION = False
    url = app.url_path_for("auth:register")
    data = {
        "email": admin.email,
        "nickname": admin.nickname,
        "password": "123456",
    }
    response = client.post(url, json=data)
    resp = Resp.model_validate(response.json())
    assert resp.code == APIState.PERMISSION_DENIED
    settings.USERS_OPEN_REGISTRATION = True


def test_register_Illegal_password(app: FastAPI, client: TestClient):
    url = app.url_path_for("auth:register")
    data = {
        "email": "{{cookiecutter.email}}",
        "nickname": "test",
        "password": "12345",
    }
    response = client.post(url, json=data)
    assert response.status_code == 422


def test_register_Illegal_name(app: FastAPI, client: TestClient):
    url = app.url_path_for("auth:register")
    data = {
        "email": "{{cookiecutter.email}}",
        "nickname": "test1234567890",
        "password": "123456",
    }
    response = client.post(url, json=data)
    assert response.status_code == 422


def test_register_email_exists(app: FastAPI, client: TestClient, admin: User):
    url = app.url_path_for("auth:register")
    data = {
        "email": admin.email,
        "nickname": admin.nickname,
        "password": "123456",
    }
    response = client.post(url, json=data)
    resp = Resp.model_validate(response.json())
    assert resp.code == APIState.DATA_EXISTED


def test_register_login_logout(app: FastAPI, client: TestClient):
    url = app.url_path_for("auth:register")
    name = datetime.now().strftime("register%Y%m%d%H%M%S")
    data = {
        "email": f"{name}@gmail.com",
        "nickname": "register",
        "password": "!QAZ2wsx",
    }

    response = client.post(url, json=data)

    assert response.status_code == 200, response.json()

    url = app.url_path_for("auth:login")
    response = client.post(url, json=data)
    assert response.status_code == 200
    access_token = response.json()["data"]["access_token"]

    url = app.url_path_for("auth:logout")
    response = client.post(url, headers={"Access-Token": access_token})
    assert response.status_code == 200


def test_auth_user_exists(app: FastAPI, client: TestClient, admin: User):
    url = app.url_path_for("auth:user-exists")
    response = client.get(url, params={"email": admin.email})
    assert response.status_code == 200
    assert response.json()["data"] is True

    url = app.url_path_for("auth:user-exists")
    response = client.get(url, params={"email": "non_existent@email.com"})
    assert response.status_code == 200
    assert response.json()["data"] is False
