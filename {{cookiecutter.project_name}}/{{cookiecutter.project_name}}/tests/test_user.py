from typing import cast

from fastapi import FastAPI
from fastapi.testclient import TestClient

from {{cookiecutter.project_name}}.models.user import SimpleUser, User
from {{cookiecutter.project_name}}.schemas.response import Resp


def test_user_change_password(
    app: FastAPI, client: TestClient, tester: User, tester_token
):
    url = app.url_path_for("user:change-password")
    response = client.post(
        url, json={"password": "!QAZxsw2"}, headers={"Access-Token": tester_token}
    )
    assert response.status_code == 200


def test_user_get_me(app: FastAPI, client: TestClient, tester: User, tester_token):
    url = app.url_path_for("user:me")
    response = client.get(url, headers={"Access-Token": tester_token})
    assert response.status_code == 200
    resp = Resp[SimpleUser].model_validate(response.json())
    user = cast(SimpleUser, resp.data)
    assert user.email == tester.email
    assert user.nickname == tester.nickname


def test_user_put_me(app: FastAPI, client: TestClient, tester: User, tester_token):
    url = app.url_path_for("user:me")
    new_name = "tester01"
    response = client.put(
        url, headers={"Access-Token": tester_token}, json={"nickname": new_name}
    )
    assert response.status_code == 200
    resp = Resp[SimpleUser].model_validate(response.json())
    user = cast(SimpleUser, resp.data)
    assert user.email == tester.email
    assert user.nickname == new_name
