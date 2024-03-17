import os
from typing import ClassVar, List, Optional

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class EnvSettings(BaseSettings):
    ENV_STATE: Optional[str] = "dev"


BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Settings(BaseSettings):
    """Global configurations."""

    PROJECT_NAME: str = Field(...)
    SECRET_KEY: SecretStr = Field(...)
    PROJECT_NAME: str = "FastAPI"
    VERSION: str = "{{cookiecutter.version}}"
    DESCRIPTION: str = ""
    DEBUG: bool = True

    ENV_STATE: Optional[str] = "dev"

    # API
    API_VER: str = "/api/v1"

    # mongo
    MONGO_URI: str = Field()
    MONGO_DB_NAME: str = Field()
    MONGO_TIMROUT: int = 60

    # Redis
    REDIS_HOST: str = Field()

    @property
    def REDIS_URI(self) -> str:
        return f"redis://{self.REDIS_HOST}:6379/0"

    # CACHE_TIMEOUT = 3600

    @property
    def CELERY_BACKEND(self) -> str:
        return f"redis://{self.REDIS_HOST}:6379/6"

    @property
    def CELERY_BROKRE(self) -> str:
        return f"redis://{self.REDIS_HOST}:6379/7"

    PASSWORD_REGEX: str = r"[a-zA-Z0-9~!@#$%^&*()_\-+=<>?:\"\{\}\|,.\/;'\\\[\]]{6,24}$"

    # JWT
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 14
    # Open user registration
    USERS_OPEN_REGISTRATION: bool = True

    # Statics Path
    BASE_DIR: ClassVar[str] = BASE_DIR
    STATICS_DIR: str = os.path.join(BASE_DIR, "statics")

    # COS
    ALLOW_ORIGINS: List[str] = ["*"]

    model_config = SettingsConfigDict(env_file=".env")


env_state = EnvSettings().ENV_STATE
if env_state == "dev":
    settings = Settings(_env_file=".dev.env")  # type: ignore
elif env_state == "test":
    settings = Settings(_env_file=".test.env")  # type: ignore
elif env_state == "prod":
    settings = Settings(_env_file=".prod.env")  # type: ignore
else:
    raise ValueError("unknown ENV_STATE: {}, must be dev or prod".format(env_state))
