import logging
import os
import sys
from types import FrameType
from typing import cast

from loguru import logger
from {{cookiecutter.project_name}}.settings import settings


class InterceptHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:  # pragma: no cover
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = str(record.levelno)

        # Find caller from where originated the logged message
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:  # noqa: WPS609
            frame = cast(FrameType, frame.f_back)
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level,
            record.getMessage(),
        )


def install_logger():
    LOGGING_LEVEL = logging.DEBUG if settings.DEBUG else logging.INFO
    LOGGERS = ("uvicorn.asgi", "uvicorn.access")

    logging.getLogger().handlers = [InterceptHandler()]
    for logger_name in LOGGERS:
        logging_logger = logging.getLogger(logger_name)
        logging_logger.handlers = [InterceptHandler(level=LOGGING_LEVEL)]

    log_file_path = os.path.join(
        settings.BASE_DIR, f"logs/{settings.PROJECT_NAME}.out.log"
    )
    err_log_file_path = os.path.join(
        settings.BASE_DIR, f"logs/{settings.PROJECT_NAME}.err.log"
    )

    loguru_config = {
        "handlers": [
            {
                "sink": sys.stderr,
                "level": "INFO",
                # "format": "<green>{time:YYYY-mm-dd HH:mm:ss.SSS}</green> | {thread.name} | <level>{level}</level> | "
                #         "<cyan>{module}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
            },
            {"sink": log_file_path, "rotation": "500 MB", "encoding": "utf-8"},
            {
                "sink": err_log_file_path,
                "serialize": True,
                "level": "ERROR",
                "rotation": "500 MB",
                "encoding": "utf-8",
            },
        ],
    }
    logger.configure(**loguru_config)  # type: ignore


install_logger()
