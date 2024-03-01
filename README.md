# Template project based on FastAPI

基于FastAPI+MongoDB的模板项目

## Features

- Manage Python Virtual Environment
- Install the package, dependencies, and pre-commit for local development
- Auto-format python source files
- Lint python source files
- Use Codespell to do spellchecking
- Type-checking
- Automated testing and coverage report
- Devcontainer

## Prerequisites

What things you need to install the software and how to install them

- [Python](https://www.python.org/): Recommendation 3.11
- [GNU Make](https://www.gnu.org/software/make): Please install according to different operating systems

## Develop dependency packages

- [pdm](https://pdm-project.org/latest/) Python package and dependency manager
- [pre-commit](https://pre-commit.com/)
- [ruff](https://docs.astral.sh/ruff/)
- [codespell](https://github.com/codespell-project/codespell)
- [coverage](https://coverage.readthedocs.io/)
- [pyright](https://microsoft.github.io/pyright/#/)
- [hatch](https://hatch.pypa.io/latest/)

## Getting Started

### Create New Project From a Template

``` shell
> pdm init --cookiecutter git@github.com:lolord/cookiecutter-fastapi.git
Creating a pyproject.toml for PDM...
  [1/5] project_name (new_project): 
  [2/5] description (A short description of the package.):
  [3/5] version (0.0.0):
  [4/5] author (author):
  [5/5] email (author@email.com):
Project is initialized successfully
> tree
new_project
│  .gitignore
│  .pre-commit-config.yaml
│  Makefile
│  pyproject.toml
├─.devcontainer
│  │  docker-compose.yaml
│  ├─app
│  │      Dockerfile
│  ├─mongo
│  │  │  Dockerfile
│  │  ├─conf
│  │  │      mongod.conf
│  │  └─init
│  │          01-init.js
│  └─nginx
│      │  nginx.conf
│      │  nginx_http.conf
│      │  nginx_https.conf
│      └─conf
│              .htpasswd
│              openssl.sh
├─.vscode
│      extensions.json
│      keybindings.json
│      settings.json
└─new_project
    │  .env
    │  main.py
    │  settings.py
    │  __init__.py
    ├─api
    │      admin.py
    │      auth.py
    │      dashboard.py
    │      public.py
    │      stat.py
    │      user.py
    │      __init__.py
    ├─db
    │      backend.py
    │      mongodb.py
    │      __init__.py
    ├─extends
    │      crud_router.py
    │      logger.py
    │      __init__.py
    ├─models
    │      user.py
    ├─rbac
    │      api.py
    │      model.py
    │      service.py
    ├─schemas
    │      auth.py
    │      errors.py
    │      request.py
    │      response.py
    │      __init__.py
    ├─scripts
    │      init_db.py
    ├─services
    │      security.py
    │      __init__.py
    ├─statics
    │  └─api-docs
    │      │  favicon.png
    │      │
    │      └─swagger
    │              swagger-ui-bundle.min.js
    │              swagger-ui.css
    ├─supervisord
    │      app.ini
    ├─tests
    │      conftest.py
    │      test_admin.py
    │      test_auth.py
    │      __init__.py
    ├─utils
    │      date_range.py
    │      hash.py
    │      __init__.py
    └─worker
            app.py
            celery_worker.py
            tasks.py

```

### Configure environmental parameters

Create .dev.env file and modify it

``` shell
> cd new_project
> copy .env .dev.env
```

### Launch

``` shell
> uvicorn main:app --host 127.0.0.1 --port 5000 --reload
INFO:     Uvicorn running on <http://127.0.0.1:5000> (Press CTRL+C to quit)
INFO:     Started reloader process [17316] using StatReload
INFO:     Started server process [4308]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### supervisor

[program:project_name]
directory=/app
command=uvicorn main:app --host 0.0.0.0 --port 5000
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true
stderr_logfile=/var/log/supervisor/%(program_name)s.err.log
stdout_logfile=/var/log/supervisor/%(program_name)s.out.log

### Makefile

- install: Install the package, dependencies, and pre-commit for local development
- format: Auto-format python source files
- lint: Lint python source files
- codespell: Use Codespell to do spellchecking
- typecheck: Perform type-checking
- test: Run all tests, skipping the type-checker integration tests
- testcov: Run tests and generate a coverage report, skipping the type-checker integration tests
- all: lint typecheck codespell testcov
- help

## Deployment

Add additional notes about how to deploy this on a live system

## Authors

- [lolord](https://github.com/lolord)

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details

## FAQ

#### 请使用`anyio`

`Starlette`是依赖`anyio`的，`FastAPI`是基于`Starlette`的, 所以请使用`anyio`
`anyio`兼容`asyncio`和`trio`

特别是，您可以直接使用AnyIO的适用于需要在自己的代码中加入更高级模式的高级并发用例。

#### Response 是一个Generic Model

使用时指明route的`response_model`可以生成更友好的API文档

``` python
@router.get(response_model=Resp[bool])
```

#### middleware的request参数不是FastAPI的request

两个Request不是同一个对象, 所以不要在middleware中读取body数据, path, query, header等参数是可以.

#### API依赖参数是BaseModel类型时, exclude_unset可能不起作用

dependencies解决依赖参数时会从Signature提取到默认值, BaseModel接收到默认值, 不会将字段标记为未赋值

#### 运行阻塞的代码

不应该直接调用阻塞(CPU-bound)代码

例如，如果一个函数执行1秒的 CPU 密集型计算，那么所有并发异步任务和 IO 操作都将延迟1秒。

可以用执行器在不同的线程甚至不同的进程中运行任务，以避免使用事件循环阻塞 OS 线程

```python
import time

from anyio import to_thread


async def main():
    await to_thread.run_sync(time.sleep, 1)
```

#### 并发任务

一个接口中需要请求多个资源时, 可以并发执行, 等待时间取决于耗时最长的任务
通过`Semaphore`可以控制并发量, 避免对资源(数据库)造成压力

```python
from anyio import Semaphore, create_task_group, sleep


async def run_with_semaphore(func, semaphore):
    async with semaphore:
        await func()


async def main():
    semaphore = Semaphore(2)
    async with create_task_group() as tg:
        tg.start_soon(run_with_semaphore, get_user, semaphore)
        tg.start_soon(run_with_semaphore, get_roles, semaphore)
        tg.start_soon(run_with_semaphore, get_permissions, semaphore)

```

#### swagger cdn timeout

1. 切换至国内cdn
2. 使用静态资源: statics/api-docs/swagger

#### odmantic RuntimeError: attached to a different loop

```shell
RuntimeError: Task <Task pending coro=<xyz.insertMany() running at <my workspace location>/xyz.py:144> cb=[_run_until_complete_cb() at /usr/lib64/python3.5/asyncio/base_events.py:164]> got Future <Future pending cb=[_chain_future.<locals>._call_check_cancel() at /usr/lib64/python3.5/asyncio/futures.py:431]> attached to a different loop
```

错误原因: odmantic的io loop不是主进程的event loop
解决办法: 更改MotorClient的get_io_loop方法

```py
from motor.motor_asyncio import (
    AsyncIOMotorClient as MotorClient,
)

# MongoDB client
client = MotorClient('mongodb://localhost:27017/test')
client.get_io_loop = asyncio.get_running_loop
```

<https://stackoverflow.com/questions/41584243/runtimeerror-task-attached-to-a-different-loop>
