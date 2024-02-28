from datetime import timedelta
from celery import Celery
from settings import settings

app = Celery(
    "worker",
    backend=settings.CELERY_BACKEND,
    broker=settings.CELERY_BROKRE,
    include=["worker.tasks"],
)


app.conf.update(task_track_started=True)
app.conf.beat_schedule = {
    # 名字随意命名
    "asys_cpu_dynamic": {
        "task": "worker.tasks.sys_cpu_dynamic",
        "schedule": timedelta(seconds=1),
    },
    "sys_mem_dynamic": {
        "task": "worker.tasks.sys_mem_dynamic",
        "schedule": timedelta(seconds=5),
    },
    "clear_cache": {
        "task": "worker.tasks.clear_cache",
        "schedule": timedelta(hours=1),
    },
}
# celery -A worker.app worker  -l info  -P eventlet
# celery -A worker.app  beat -l info
