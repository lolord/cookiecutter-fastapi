import json
from time import time

import psutil  # 进程运行情况
from redis import from_url
from settings import settings
from worker.app import app

redis_db = from_url(settings.REDIS_URI)


@app.task  # type: ignore[misc]
def sys_cpu_dynamic() -> None:
    # 硬件信息
    cpu = psutil.cpu_percent(1)
    cpus = psutil.cpu_percent(percpu=True)

    info = {
        "at": int(time()),
        "cpu": cpu,
        "cpus": cpus,
    }
    redis_db.rpush("sys_cpu_dynamic", json.dumps(info))


@app.task  # type: ignore[misc]
def sys_mem_dynamic() -> None:
    info = psutil.virtual_memory()._asdict()
    info["time"] = int(time() * 1000)
    redis_db.rpush("sys_mem_dynamic", json.dumps(info))


@app.task  # type: ignore[misc]
def clear_cache() -> None:
    size = redis_db.llen("sys_cpu_dynamic")
    delta = size - 3600
    if delta:
        redis_db.ltrim("sys_cpu_dynamic", 0, delta)

    size = redis_db.llen("sys_mem_dynamic")
    delta = size - 3600
    if delta:
        redis_db.ltrim("sys_mem_dynamic", 0, delta)
