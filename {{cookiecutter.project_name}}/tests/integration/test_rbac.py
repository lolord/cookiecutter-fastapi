from fastapi import FastAPI
from fastapi.testclient import TestClient
from inline_snapshot import snapshot

from {{cookiecutter.project_name}}.models.user import User
from {{cookiecutter.project_name}}.rbac.model import Menu, Permission, RBACRoute, Role
from {{cookiecutter.project_name}}.rbac.service import RoleProfile
from {{cookiecutter.project_name}}.schemas.response import PageResp, Resp

admin_role: Role = None


def test_rbac_route_not_matched(app: FastAPI, client: TestClient):
    response = client.get("/not_matched")
    assert response.status_code == snapshot(404)
    assert response.json()["detail"] == snapshot("Not Found")


def test_rbac_route_visitor_unauthorized(app: FastAPI, client: TestClient):
    url = app.url_path_for("rbac:roles")
    response = client.get(url)
    print("xxx", response.text)
    assert response.status_code == snapshot(401)
    assert response.json()["detail"] == snapshot("Could not validate credentials")


def test_rbac_route_user_not_permissions(app: FastAPI, client: TestClient, tester_token_headers: User):
    url = app.url_path_for("rbac:roles")
    response = client.get(url, headers=tester_token_headers)
    assert response.status_code == snapshot(401)
    assert response.json()["detail"] == snapshot("Not enough permissions")


def test_query_roles(app: FastAPI, client: TestClient, tester: User, admin_token_headers):
    url = app.url_path_for("rbac:roles")
    response = client.get(url, headers=admin_token_headers)
    assert response.status_code == 200, response.text
    resp = PageResp[Role].model_validate(response.json())

    global admin_role
    for role in resp.data:
        if role.name == "admin":
            admin_role = role
    assert admin_role


def test_query_roles_by_name(app: FastAPI, client: TestClient, tester: User, admin_token_headers):
    global admin_role
    url = app.url_path_for("rbac:roles")
    response = client.get(url, params={"name": admin_role.name}, headers=admin_token_headers)
    assert response.status_code == 200
    resp = PageResp[Role].model_validate(response.json())
    assert resp.data[0] == admin_role


def test_get_role_profile(app: FastAPI, client: TestClient, tester: User, admin_token_headers):
    global admin_role
    url = app.url_path_for("rbac:role-profile", id=admin_role.id)
    response = client.get(url, headers=admin_token_headers)
    assert response.status_code == 200
    resp = Resp[RoleProfile].model_validate(response.json())
    assert resp.data.name == admin_role.name


def test_get_role_profile_not_exists(app: FastAPI, client: TestClient, tester: User, admin_token_headers):
    global admin_role

    url = app.url_path_for("rbac:role-profile", id="68383101b7e37b1f685b6ccc")
    response = client.get(url, headers=admin_token_headers)
    assert response.status_code == snapshot(400)
    assert response.json()["code"] == snapshot(2001)
    assert response.json()["msg"] == snapshot("Data Not Found: Role(id=68383101b7e37b1f685b6ccc)")


tmp_role = Role(id="68382e543bbb56f8c20eeaa0", name="tmp_role")


def create_role(role: Role, app: FastAPI, client: TestClient, admin_token_headers):
    url = app.url_path_for("rbac:roles")
    return client.post(url, content=role.model_dump_json(), headers=admin_token_headers)


def delete_role(role: Role, app: FastAPI, client: TestClient, admin_token_headers):
    url = app.url_path_for("rbac:roles", id=role.id)
    return client.delete(url, headers=admin_token_headers)


def test_create_role(app: FastAPI, client: TestClient, tester: User, admin_token_headers):
    delete_role(tmp_role, app, client, admin_token_headers)

    response = create_role(tmp_role, app, client, admin_token_headers)
    assert response.status_code == 200
    resp = Resp[Role].model_validate(response.json())
    assert resp.data == tmp_role


def test_create_role_exists(app: FastAPI, client: TestClient, tester: User, admin_token_headers):
    response = create_role(tmp_role, app, client, admin_token_headers)
    data = response.json()
    assert data["code"] == snapshot(2003)
    assert data["msg"] == snapshot("Data Existed:Role(name=tmp_role)")


def test_edit_role(app: FastAPI, client: TestClient, tester: User, admin_token_headers):
    url = app.url_path_for("rbac:roles")
    tmp_role.name = "update"
    response = client.put(url, content=tmp_role.model_dump_json(), headers=admin_token_headers)
    assert response.status_code == snapshot(200)
    resp = Resp[Role].model_validate(response.json())
    assert resp.data == tmp_role


def test_edit_role_not_exists(app: FastAPI, client: TestClient, tester: User, admin_token_headers):
    not_exists = Role(id="68383101b7e37b1f685b6cdb", name="not_exists")
    url = app.url_path_for("rbac:roles")
    response = client.put(url, content=not_exists.model_dump_json(), headers=admin_token_headers)
    assert response.status_code == snapshot(400)
    data = response.json()
    assert data["code"] == snapshot(2001)
    assert data["msg"] == snapshot("Data Not Found: Role(id=68383101b7e37b1f685b6cdb)")


def test_edit_role_admin(app: FastAPI, client: TestClient, tester: User, admin_token_headers):
    url = app.url_path_for("rbac:roles")
    tmp_role.name = "admin"
    response = client.put(url, content=tmp_role.model_dump_json(), headers=admin_token_headers)
    assert response.status_code == snapshot(400)
    data = response.json()
    assert data["code"] == snapshot(5000)
    assert data["msg"] == snapshot("Not enough permissions.")


def test_delete_role(app: FastAPI, client: TestClient, tester: User, admin_token_headers):
    response = delete_role(tmp_role, app, client, admin_token_headers)
    assert response.status_code == snapshot(200)


def test_delete_role_not_exists(app: FastAPI, client: TestClient, tester: User, admin_token_headers):
    response = delete_role(tmp_role, app, client, admin_token_headers)
    assert response.status_code == snapshot(400)
    print("xxx", response.text)
    data = response.json()
    assert data["code"] == snapshot(2001)
    assert data["msg"] == snapshot("Data Not Found: Role(id=68382e543bbb56f8c20eeaa0)")


def test_delete_role_admin(app: FastAPI, client: TestClient, tester: User, admin_token_headers):
    response = delete_role(admin_role, app, client, admin_token_headers)
    assert response.status_code == snapshot(400)
    data = response.json()
    assert data["code"] == snapshot(5000)
    assert data["msg"] == snapshot("Permission denied: delete admin")


def test_routes_sort_by_name_asc(app: FastAPI, client: TestClient, admin_token_headers):
    url = app.url_path_for("rbac:routes")

    response = client.get(url, headers=admin_token_headers, params={"sort_by": "name", "sort_order": "ascend"})
    assert response.status_code == 200
    resp = PageResp[RBACRoute].model_validate(response.json())
    names = [route.name for route in resp.data]

    _names = sorted(names, key=lambda x: x.lower())
    assert names == _names


def test_routes_sort_by_name_desc(app: FastAPI, client: TestClient, admin_token_headers):
    url = app.url_path_for("rbac:routes")

    response = client.get(url, headers=admin_token_headers, params={"sort_by": "name", "sort_order": "descend"})
    assert response.status_code == 200
    resp = PageResp[RBACRoute].model_validate(response.json())
    names = [route.name for route in resp.data]
    _names = sorted(names, key=lambda x: x.lower(), reverse=True)
    assert names == _names


def find_route_by_name(name: str, app: FastAPI, client: TestClient, admin_token_headers) -> RBACRoute | None:
    url = app.url_path_for("rbac:routes")
    response = client.get(url, headers=admin_token_headers, params={"name": name})
    resp = PageResp[RBACRoute].model_validate(response.json())
    return resp.data[0]


def test_post_route_permissions(app: FastAPI, client: TestClient, admin_token_headers):
    delete_permission(permission.id, app, client, admin_token_headers)
    route = find_route_by_name("rbac:routes:permissions", app, client, admin_token_headers)
    url = app.url_path_for("rbac:routes:permissions", id=route.id)
    response = client.post(url, headers=admin_token_headers, json={"permissions": [permission.name]})
    assert response.status_code == 200
    Resp[RBACRoute].model_validate(response.json())


def test_post_route_permissions_not_exists(app: FastAPI, client: TestClient, admin_token_headers):
    url = app.url_path_for("rbac:routes:permissions", id="68383101b7e37b1f685b6ddd")
    response = client.post(url, headers=admin_token_headers, json={"permissions": [permission.name]})
    assert response.status_code == snapshot(400)
    assert response.json()["code"] == snapshot(2001)
    assert response.json()["msg"] == snapshot("Data Not Found: RBACRoute(id=68383101b7e37b1f685b6ddd)")


menu = Menu(id="683e9aac73a7f4a7bc5a76b5", path="/test", title="test")


def test_post_menu(app: FastAPI, client: TestClient, admin_token_headers):
    url = app.url_path_for("rbac:menus")
    response = client.post(url, headers=admin_token_headers, content=menu.model_dump_json())
    assert response.status_code == 200
    Resp[Menu].model_validate(response.json())


def test_get_menus(app: FastAPI, client: TestClient, admin_token_headers):
    url = app.url_path_for("rbac:menus")
    response = client.get(url, headers=admin_token_headers)
    assert response.status_code == 200
    PageResp[Menu].model_validate(response.json())


def get_menu_by_id(app: FastAPI, client: TestClient, admin_token_headers):
    url = app.url_path_for("rbac:menus")
    response = client.get(url, headers=admin_token_headers, params={"q": str(menu.id), "keys": ["id"]})
    resp = PageResp[Menu].model_validate(response.json())
    return resp.data[0]


def test_put_menu(app: FastAPI, client: TestClient, admin_token_headers):
    url = app.url_path_for("rbac:menus")
    menu.path = "/test/test"
    response = client.put(url, headers=admin_token_headers, content=menu.model_dump_json())
    assert response.status_code == 200
    _menu = get_menu_by_id(app, client, admin_token_headers)
    assert menu == _menu


def test_delete_menu(app: FastAPI, client: TestClient, admin_token_headers):
    url = app.url_path_for("rbac:menus:remove", id=str(menu.id))
    response = client.delete(url, headers=admin_token_headers)
    assert response.status_code == 200


def test_delete_menu_again(app: FastAPI, client: TestClient, admin_token_headers):
    url = app.url_path_for("rbac:menus:remove", id=str(menu.id))
    response = client.delete(url, headers=admin_token_headers)
    assert response.status_code == snapshot(400)
    assert response.json()["msg"] == snapshot("Data Not Found: Menu(id=683e9aac73a7f4a7bc5a76b5)")


permission = Permission(
    id="683e9aac73a7f4a7bc5a76b6",
    name="test_permission",
    description="Test permission",
)


def delete_permission(id, app: FastAPI, client: TestClient, admin_token_headers):
    url = app.url_path_for("rbac:permissions", id=id)

    resp = client.delete(url, headers=admin_token_headers)
    return resp


def get_permission_by_name(name: str, app: FastAPI, client: TestClient, admin_token_headers):
    url = app.url_path_for("rbac:permissions")
    response = client.get(url, headers=admin_token_headers, params={"name": name})
    resp = PageResp[Permission].model_validate(response.json())
    return resp.data[0] if len(resp.data) > 0 else None


def test_post_permission(app: FastAPI, client: TestClient, admin_token_headers):
    p = get_permission_by_name(permission.name, app, client, admin_token_headers)

    if p:
        delete_permission(p.id, app, client, admin_token_headers)
    url = app.url_path_for("rbac:permissions")
    response = client.post(url, headers=admin_token_headers, content=permission.model_dump_json())
    assert response.status_code == 200
    Resp[Permission].model_validate(response.json())


def test_post_permission_exists(app: FastAPI, client: TestClient, admin_token_headers):
    url = app.url_path_for("rbac:permissions")
    response = client.post(url, headers=admin_token_headers, content=permission.model_dump_json())
    assert response.status_code == snapshot(400)
    assert response.json()["msg"] == snapshot("Data Not Found: Permission(name=test_permission)")


def test_put_permission_same_name(app: FastAPI, client: TestClient, admin_token_headers):
    url = app.url_path_for("rbac:permissions")
    permission_not_exists = Permission(
        id="683e9aac73a7f4a7bc5a76b7",
        name="admin",
        description="",
    )
    response = client.put(url, headers=admin_token_headers, content=permission_not_exists.model_dump_json())
    assert response.status_code == snapshot(400)
    assert response.json()["msg"] == snapshot("Data Existed:Permission(name=683e9aac73a7f4a7bc5a76b7)")


def test_put_permission_not_exists(app: FastAPI, client: TestClient, admin_token_headers):
    url = app.url_path_for("rbac:permissions")
    permission_not_exists = Permission(
        id="683e9aac73a7f4a7bc5a76b7",
        name="permission_not_exists",
        description="",
    )
    response = client.put(url, headers=admin_token_headers, content=permission_not_exists.model_dump_json())
    assert response.status_code == snapshot(400)
    assert response.json()["msg"] == snapshot("Data Not Found: Permission(id=683e9aac73a7f4a7bc5a76b7)")


def test_put_permission_description(app: FastAPI, client: TestClient, admin_token_headers):
    url = app.url_path_for("rbac:permissions")
    permission.description = "Updated description"
    response = client.put(url, headers=admin_token_headers, content=permission.model_dump_json())
    assert response.status_code == snapshot(200)
    resp = Resp[Permission].model_validate(response.json())
    assert resp.data.description == "Updated description"


def test_put_permission_name(app: FastAPI, client: TestClient, admin_token_headers):
    url = app.url_path_for("rbac:permissions")
    permission.name = "updated_permission"
    response = client.put(url, headers=admin_token_headers, content=permission.model_dump_json())
    assert response.status_code == snapshot(200)
    resp = Resp[Permission].model_validate(response.json())
    assert resp.data.name == "updated_permission"


def test_get_permissions(app: FastAPI, client: TestClient, admin_token_headers):
    url = app.url_path_for("rbac:permissions")
    response = client.get(url, headers=admin_token_headers)
    assert response.status_code == 200
    resp = PageResp[Permission].model_validate(response.json())
    assert permission in resp.data


def test_delete_permission(app: FastAPI, client: TestClient, admin_token_headers):
    response = delete_permission(permission.id, app, client, admin_token_headers)
    assert response.status_code == snapshot(200)


def test_delete_permission_not_exists(app: FastAPI, client: TestClient, admin_token_headers):
    response = delete_permission(permission.id, app, client, admin_token_headers)
    assert response.status_code == snapshot(400)
    assert response.json()["msg"] == snapshot("Data Not Found: Permission(id=683e9aac73a7f4a7bc5a76b6)")
