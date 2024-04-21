from typing import Set

from {{cookiecutter.project_name}}.schemas.response import APIState


class APIException(Exception):
    def __init__(self, code: APIState, msg: str) -> None:
        super().__init__(code, msg)

    def dict(self):
        return {"code": self.args[0], "msg": self.args[1]}


class DBTimeoutError(APIException):
    def __init__(self, msg: str) -> None:
        super().__init__(APIState.DB_TIMEOUT, msg)


class RBACRouteNotFindError(APIException):
    def __init__(self, method: str, path: str) -> None:
        super().__init__(
            APIState.PERMISSION_DENIED, f"RBACRouteNotFind:{path}.{method}"
        )


class PermissionDeniedError(APIException):
    def __init__(self, permissions: Set[str]) -> None:
        super().__init__(
            APIState.PERMISSION_DENIED, f"Permission denied: {list(permissions)}"
        )
