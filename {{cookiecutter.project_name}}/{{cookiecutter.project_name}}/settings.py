import os
import typing
from enum import Enum
from typing import ClassVar, List, Optional

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class EnvState(str, Enum):
    DEV = "dev"
    TEST = "test"
    PROD = "prod"


ENV_STATE: EnvState = EnvState(os.getenv("ENV_STATE", "dev").lower())
BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

_env_files: dict[EnvState, str] = {
    EnvState.DEV: ".dev.env",
    EnvState.TEST: ".test.env",
    EnvState.PROD: ".prod.env",
}


class Settings(BaseSettings):
    """Global configurations."""

    PROJECT_NAME: str = Field("{{cookiecutter.project_name}}")
    SECRET_KEY: SecretStr = Field(...)
    VERSION: str = "{{cookiecutter.version}}"
    DESCRIPTION: str = ""

    ENV_STATE: Optional[str] = "dev"

    # API
    API_VER: str = "/api/v1"

    # mongo
    MONGO_URI: str = Field()
    MONGO_DB_NAME: str = Field()
    MONGO_QUERY_TIMEOUT: int = 1

    # Redis
    REDIS_HOST: str = Field()

    @property
    def REDIS_URI(self) -> str:  # pragma: no cover
        return f"redis://{self.REDIS_HOST}:6379/0"

    CACHE_TIMEOUT: int = Field(3600)

    @property
    def CELERY_BACKEND(self) -> str:  # pragma: no cover
        return f"redis://{self.REDIS_HOST}:6379/6"

    @property
    def CELERY_BROKRE(self) -> str:  # pragma: no cover
        return f"redis://{self.REDIS_HOST}:6379/7"

    PASSWORD_REGEX: typing.Pattern[str] = Field("(?=.*\d)(?=.*[a-z])(?=.*[A-Z])(?=.*[^a-zA-Z0-9\s])([^\s]){6,24}$")  # type: ignore[arg-type]
    USERNAME_REGEX: typing.Pattern[str] = Field("[\u4e00-\u9fa5a-zA-Z0-9-_]{2,30}$")  # type: ignore[arg-type]

    # JWT
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 14
    # Open user registration
    USERS_OPEN_REGISTRATION: bool = True

    # Statics Path
    BASE_DIR: ClassVar[str] = BASE_DIR

    @property
    def STATICS_DIR(self) -> str:  # pragma: no cover
        return os.path.join(BASE_DIR, self.PROJECT_NAME, "statics")

    # COS
    ALLOW_ORIGINS: List[str] = ["*"]

    @property
    def DEBUG(self) -> bool:
        return self.ENV_STATE == EnvState.PROD

    model_config = SettingsConfigDict(env_file=_env_files[ENV_STATE])  # type: ignore


settings = Settings()  # type: ignore[call-arg]
