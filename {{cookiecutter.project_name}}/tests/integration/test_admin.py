import re
from typing import cast

from fastapi import FastAPI
from fastapi.testclient import TestClient
from inline_snapshot import snapshot
from odmantic import ObjectId

from {{cookiecutter.project_name}}.db import db
from {{cookiecutter.project_name}}.models.user import SimpleUser, User
from {{cookiecutter.project_name}}.schemas import PageResp, Resp
from {{cookiecutter.project_name}}.settings import settings

admin_create_user_email = "admin_create_user@email.com"
admin_create_user_name = "admin_create_user"
admin_create_user_id: ObjectId | None = None


def delete_admin_create_user():
    global admin_create_user_email
    db.user.delete_one({"email": admin_create_user_email})


def test_admin_create_user(app: FastAPI, client: TestClient, admin_token_headers: str):
    delete_admin_create_user()

    url = app.url_path_for("admin:users")

    data = {
        "email": admin_create_user_email,
        "nickname": admin_create_user_name,
    }

    response = client.post(url, headers=admin_token_headers, json=data)

    assert response.status_code == 200, response.text

    resp = Resp[SimpleUser].model_validate(response.json())
    assert resp.data.email == data["email"]
    assert resp.data.nickname == data["nickname"]
    global admin_create_user_id
    admin_create_user_id = cast(ObjectId, resp.data.id)


def test_admin_create_user_again(app: FastAPI, client: TestClient, admin_token_headers: str):
    url = app.url_path_for("admin:users")

    data = {
        "email": admin_create_user_email,
        "nickname": admin_create_user_name,
    }

    response = client.post(url, headers=admin_token_headers, json=data)

    assert response.status_code == snapshot(400)
    data = response.json()
    assert data["code"] == snapshot(2003)
    assert data["msg"] == snapshot("Data Existed:User(email=admin_create_user@email.com)")


def test_admin_edit_user(app: FastAPI, client: TestClient, admin_token_headers: str):
    global admin_create_user_id
    print("admin_create_user_id=", admin_create_user_id)
    url = app.url_path_for("admin:users", id=admin_create_user_id)
    response = client.put(
        url,
        headers=admin_token_headers,
        json={
            "nickname": "updated",
            "password": "!QAZ2wsx",
            "enabled": False,
        },
    )
    assert response.status_code == 200
    resp = Resp[SimpleUser].model_validate(response.json())
    update = cast(SimpleUser, resp.data)
    assert update.nickname == "updated"
    assert update.enabled is False


def test_admin_reset_password(app: FastAPI, client: TestClient, admin_token_headers: str):
    global admin_create_user_id
    url = app.url_path_for("admin:reset-password", id=admin_create_user_id)
    response = client.post(url, headers=admin_token_headers)
    assert response.status_code == 200
    password = response.json()["data"]
    assert re.match(settings.PASSWORD_REGEX, password), password


def test_admin_delete_user(app: FastAPI, client: TestClient, admin_token_headers: str):
    global admin_create_user_id
    url = app.url_path_for("admin:users", id=admin_create_user_id)
    response = client.delete(url, headers=admin_token_headers)
    assert response.status_code == 200


def test_admin_delete_user_again(app: FastAPI, client: TestClient, admin_token_headers: str):
    global admin_create_user_id
    url = app.url_path_for("admin:users", id=admin_create_user_id)
    response = client.delete(url, headers=admin_token_headers)

    assert response.status_code == snapshot(200)
    data = response.json()
    assert data["code"] == snapshot(0)
    assert data["msg"] == snapshot(None)


def test_admin_delete_user_not_exists(app: FastAPI, client: TestClient, admin_token_headers: str):
    global admin_create_user_id
    url = app.url_path_for("admin:users", id=ObjectId("683fe2476d955f8b60422961"))
    response = client.delete(url, headers=admin_token_headers)

    assert response.status_code == snapshot(400)
    data = response.json()
    assert data["code"] == snapshot(2001)
    assert data["msg"] == snapshot("Data Not Found: User(id=683fe2476d955f8b60422961)")


def test_get_admin_users(app: FastAPI, client: TestClient, admin_token_headers: str, admin: User):
    url = app.url_path_for("admin:users")

    params = {"q": admin.nickname, "sort_by": "nickname"}

    response = client.get(url, headers=admin_token_headers, params=params)

    assert response.status_code == 200, response.text
    resp = PageResp[SimpleUser].model_validate(response.json())
    assert resp.data is not None
    assert all(i.nickname == admin.nickname for i in resp.data)


def test_user_get_users(app: FastAPI, client: TestClient, tester_token_headers: str):
    url = app.url_path_for("admin:users")

    response = client.get(url, headers=tester_token_headers)

    assert response.status_code == snapshot(400)
    data = response.json()
    assert data["code"] == snapshot(5000)
    assert data["msg"] == snapshot("Permission denied: admin")
