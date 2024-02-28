from typing import Dict, Set, Type

from odmantic import Model


class APIException(Exception):
    ...


class DBTimeoutError(APIException):
    def __init__(self, model: Type[Model], query: Dict, timeout: float) -> None:
        self.model = model
        self.query = query
        self.timeout = timeout

    def dict(self):
        return {
            "msg": f"TimeoutError:{self.timeout}s",
            "model": +type(self.model),
            "query": self.query,
        }


class RBACRouteNotFindError(APIException):
    def __init__(self, method: str, path: str) -> None:
        self.method = method
        self.path = path

    def dict(self):
        return {
            "msg": f"RBACRouteNotFind:{self.path}.{self.method}",
        }


class PermissionDeniedError(APIException):
    def __init__(self, permissions: Set[str]) -> None:
        self.permissions = list(permissions)

    def dict(self):
        return {
            "msg": "Permission denied",
            "permissions": self.permissions,
        }
