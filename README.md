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

### Prerequisites

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

### Makefile

- install: Install the package, dependencies, and pre-commit for local development
- format: Auto-format python source files
- lin: Lint python source files
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

## Note

#### Response 是一个Generic Model

使用时指明route的response_model可以生成更友好的API文档

``` python
@router.get(response_model=Resp[bool])
```

#### middleware的request参数不是FastAPI的request

两个Request不是同一个对象, 所以不要在middleware中读取body数据, path, query, header等参数是可以.

#### API依赖参数是BaseModel类型时, exclude_unset可能不起作用

dependencies解决依赖参数时会从Signature提取到默认值, BaseModel接收到默认值, 不会将字段标记为未赋值

## FAQ

#### files.pythonhosted.org timeout

HTTPSConnectionPool(host='files.pythonhosted.org', port=443): Read timed out.

切换国内镜像源

- 清华大学镜像 <https://pypi.tuna.tsinghua.edu.cn/simple/>
- 豆瓣镜像 <http://pypi.douban.com/simple/>
- 阿里镜像 <http://mirrors.aliyun.com/pypi/simple/>

方法1：设置pip全局设置镜像源（推荐）

``` shell
pip3 config --global set global.index-url https://mirrors.aliyun.com/pypi/simple/
pip3 config --global set install.trusted-host mirrors.aliyun.com
```

方法2：安装时指定源

``` shell
pip3 install <package> -i https://pypi.doubanio.com/simple
```

#### swagger cdn timeout

1. 切换至国内cdn
2. 使用静态资源: statics/api-docs/swagger
