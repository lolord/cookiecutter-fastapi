from datetime import datetime

from fastapi import FastAPI
from fastapi.testclient import TestClient

from {{cookiecutter.project_name}}.models.user import User


def test_manage_user(app: FastAPI, client: TestClient, admin_token: str, admin: User):
    url = app.url_path_for("admin:users")

    name = datetime.now().strftime("create%Y%m%d%H%M%S")
    data = {
        "email": f"{name}@gmail.com",
        "nickname": "create",
    }

    response = client.post(url, headers={"Access-Token": admin_token}, json=data)

    assert response.status_code == 200

    user = response.json()["data"]
    assert user["email"] == data["email"]
    assert user["nickname"] == data["nickname"]

    id = user["id"]
    response = client.put(
        f"{url}/{id}",
        headers={"Access-Token": admin_token},
        json={"nickname": "updated"},
    )
    assert response.status_code == 200
    user = response.json()["data"]
    assert user["email"] == data["email"]
    assert user["nickname"] == "updated"

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
