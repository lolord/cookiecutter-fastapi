from datetime import datetime, timedelta

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from inline_snapshot import snapshot

from {{cookiecutter.project_name}}.models.user import User
from {{cookiecutter.project_name}}.schemas.auth import Token
from {{cookiecutter.project_name}}.schemas.response import APIState, Resp
from {{cookiecutter.project_name}}.services.security import get_password_hash
from {{cookiecutter.project_name}}.settings import settings
from {{cookiecutter.project_name}}.utils import random_password


@pytest.mark.order(1)
def test_register_closed(app: FastAPI, client: TestClient, admin: User):
    settings.USERS_OPEN_REGISTRATION = False
    url = app.url_path_for("auth:register")
    data = {
        "email": admin.email,
        "nickname": admin.nickname,
        "password": random_password(8),
    }
    response = client.post(url, json=data)
    resp = Resp.model_validate(response.json())
    assert resp.code == APIState.PERMISSION_DENIED
    settings.USERS_OPEN_REGISTRATION = True


def test_register_illegal_password(app: FastAPI, client: TestClient):
    url = app.url_path_for("auth:register")
    data = {
        "email": "{{cookiecutter.email}}",
        "nickname": "test",
        "password": "123456",
    }
    response = client.post(url, json=data)
    assert response.status_code == 422


def test_register_illegal_name(app: FastAPI, client: TestClient):
    url = app.url_path_for("auth:register")
    data = {
        "email": "{{cookiecutter.email}}",
        "nickname": "test1234567890",
        "password": random_password(8),
    }
    response = client.post(url, json=data)
    assert response.status_code == 422


def test_register_email_exists(app: FastAPI, client: TestClient, admin: User):
    url = app.url_path_for("auth:register")
    data = {
        "email": admin.email,
        "nickname": admin.nickname,
        "password": random_password(8),
    }
    response = client.post(url, json=data)
    resp = Resp.model_validate(response.json())
    assert resp.code == APIState.DATA_EXISTED


def test_login(app: FastAPI, client: TestClient, admin_raw: dict):
    url = app.url_path_for("auth:login")
    response = client.post(url, json=admin_raw)
    assert response.status_code == 200, response.text
    resp = Resp[Token].model_validate(response.json())
    assert resp.data.access_token


def test_login_not_user(app: FastAPI, client: TestClient):
    url = app.url_path_for("auth:login")
    data = {
        "email": "nobody@gmail.com",
        "password": "!QAZ2wsx",
    }
    response = client.post(url, json=data)
    assert response.status_code == 400
    assert response.json()["msg"] == snapshot("Login Error: Incorrect email or password")


def test_login_user_deleted(mocker, app: FastAPI, client: TestClient):
    url = app.url_path_for("auth:login")
    data = {
        "email": "nobody@gmail.com",
        "password": "!QAZ2wsx",
    }
    mock_get = mocker.patch("{{cookiecutter.project_name}}.services.security.get_user_by_email")
    mock_get.return_value = User(nickname="nobody", email="nobody@gmail.com", deleted=1)
    response = client.post(url, json=data)
    assert response.status_code == 400
    assert response.json()["msg"] == snapshot("Login Error: User deleted")


def test_login_not_enabled(mocker, app: FastAPI, client: TestClient):
    url = app.url_path_for("auth:login")
    data = {
        "email": "nobody@gmail.com",
        "password": "!QAZ2wsx",
    }
    mock_get = mocker.patch("{{cookiecutter.project_name}}.services.security.get_user_by_email")
    mock_get.return_value = User(nickname="nobody", email="nobody@gmail.com", enabled=False)
    response = client.post(url, json=data)
    assert response.status_code == 400
    assert response.json()["msg"] == snapshot("Login Error: Inactive user")


def test_login_expired(mocker, app: FastAPI, client: TestClient):
    url = app.url_path_for("auth:login")
    data = {
        "email": "nobody@gmail.com",
        "password": "!QAZ2wsx",
    }
    mock_get = mocker.patch("{{cookiecutter.project_name}}.services.security.get_user_by_email")
    mock_get.return_value = User(
        nickname="nobody",
        email="nobody@gmail.com",
        expire_at=datetime.now() - timedelta(days=1),
    )
    response = client.post(url, json=data)
    assert response.status_code == 400
    assert response.json()["msg"] == snapshot("Login Error: User has expired")


def test_login_password_error(mocker, app: FastAPI, client: TestClient):
    url = app.url_path_for("auth:login")
    data = {
        "email": "nobody@gmail.com",
        "password": "!QAZ2wsx",
    }
    mock_get = mocker.patch("{{cookiecutter.project_name}}.services.security.get_user_by_email")
    mock_get.return_value = User(
        nickname="nobody",
        email="nobody@gmail.com",
        hashed_password=get_password_hash("!qaz2wsx"),
        expire_at=datetime.now() + timedelta(days=1),
    )
    response = client.post(url, json=data)
    assert response.status_code == 400
    assert response.json()["msg"] == snapshot("Login Error: Incorrect password")


def test_login_logout(app: FastAPI, client: TestClient):
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
    response = client.post(url, headers={"Authorization": access_token})
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


def test_oauth2login(app: FastAPI, client: TestClient, admin: User, admin_raw: dict):
    url = app.url_path_for("auth:oauth2login")
    form_data = {
        "username": admin_raw["email"],
        "password": admin_raw["password"],
    }

    response = client.post(url, data=form_data)
    assert response.status_code == 200, response.text
    resp = Token.model_validate(response.json())
    assert resp.access_token


def test_token_error(app: FastAPI, client: TestClient):
    error_token = {"Authorization": "Bearer xxxxx"}
    url = app.url_path_for("user:me")
    response = client.get(url, headers=error_token)
    assert response.status_code == snapshot(400), response.text
    print(response.text)
    assert response.json()["msg"] == snapshot("Login Error: Incorrect email or password")
