from {{cookiecutter.project_name}}.schemas.response import APIState, Resp


class APIError(Exception):
    def __init__(self, code: APIState, msg: str) -> None:
        super().__init__(code, msg)

    def response(self) -> Resp[None]:
        return Resp(code=self.args[0], msg=self.args[1], data=None)


class DataNotFoundError(APIError):
    def __init__(self, data: str):
        super().__init__(code=APIState.DATA_NOT_FOUND, msg=f"Data Not Found: {data}")


class DataExistedError(APIError):
    def __init__(self, data: str):
        super().__init__(code=APIState.DATA_EXISTED, msg=f"Data Existed:{data}")


class DataInvalidError(APIError):
    def __init__(self, data: str):
        super().__init__(code=APIState.DATA_INVALID, msg=f"Data Invalid: {data}")


class OperateInvalidError(APIError):
    def __init__(self, msg: str):
        super().__init__(code=APIState.OPERATE_INVALID, msg=f"Operate Invalid: {msg}")


class QueryTimeoutError(APIError):
    def __init__(self, msg: str) -> None:
        super().__init__(code=APIState.QUERY_TIMEOUT, msg=f"Query Timeout Error: {msg}")


class PermissionDeniedError(APIError):
    def __init__(self, msg: str) -> None:
        super().__init__(APIState.PERMISSION_DENIED, f"Permission denied: {msg}")


class LoginFailedError(APIError):
    def __init__(self, msg: str) -> None:
        super().__init__(APIState.LOGIN_FAILED, f"Login Error: {msg}")
