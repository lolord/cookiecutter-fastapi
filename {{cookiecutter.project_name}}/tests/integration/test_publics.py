from fastapi import FastAPI
from fastapi.testclient import TestClient

from {{cookiecutter.project_name}}.settings import settings


def test_docs(app: FastAPI, client: TestClient):
    response = client.get("/docsx")
    assert response.status_code == 200


def test_publics_hello(app: FastAPI, client: TestClient):
    url = app.url_path_for("publics:hello")
    response = client.get(url)
    assert response.status_code == 200
    assert response.json() == "hello"


def test_publics_app(app: FastAPI, client: TestClient):
    url = app.url_path_for("publics:app")
    response = client.get(url)
    assert response.status_code == 200
    assert response.json() == {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "description": settings.DESCRIPTION,
    }
