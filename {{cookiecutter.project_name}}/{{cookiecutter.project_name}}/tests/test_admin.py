from datetime import datetime
from typing import cast

from fastapi import FastAPI
from fastapi.testclient import TestClient

from {{cookiecutter.project_name}}.models.user import SimpleUser, User
from {{cookiecutter.project_name}}.schemas import PageResp, Resp


def test_manage_user(app: FastAPI, client: TestClient, admin_token: str, admin: User):
    url = app.url_path_for("admin:users")

    name = datetime.now().strftime("create%Y%m%d%H%M%S")
    data = {
        "email": f"{name}@email.com",
        "nickname": "create",
    }

    response = client.post(url, headers={"Access-Token": admin_token}, json=data)

    assert response.status_code == 200

    resp = Resp[User].model_validate(response.json())
    assert resp.data is not None
    user = cast(User, resp.data)
    assert user.email == data["email"]
    assert user.nickname == data["nickname"]

    id = user.id
    response = client.put(
        f"{url}/{id}",
        headers={"Access-Token": admin_token},
        json={
            "nickname": "updated",
            "password": "!QAZ2wsx",
            "enabled": False,
        },
    )
    assert response.status_code == 200

    resp = Resp[User].model_validate(response.json())
    assert resp.data is not None

    update = cast(User, resp.data)

    assert update.email == user.email
    assert update.nickname == "updated"
    assert update.enabled is False

    url = app.url_path_for("admin:reset-password", id=id)
    response = client.post(
        url,
        headers={"Access-Token": admin_token},
    )
    assert response.status_code == 200, (
        id,
        f"{url}/{id}",
    )
    password = response.json()["data"]
    assert password

    url = app.url_path_for("admin:users", id=id)
    response = client.delete(
        url,
        headers={"Access-Token": admin_token},
    )
    assert response.status_code == 200, response.json()


def test_admin_users(app: FastAPI, client: TestClient, admin_token: str, admin: User):
    url = app.url_path_for("admin:users")

    params = {
        "q": admin.nickname,
    }

    response = client.get(url, headers={"Access-Token": admin_token}, params=params)

    assert response.status_code == 200
    resp = PageResp[SimpleUser].model_validate(response.json())
    assert resp.data is not None
    assert all(i.nickname == admin.nickname for i in resp.data)
