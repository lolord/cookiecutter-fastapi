# FROM tiangolo/uvicorn-gunicorn-fastapi:python3.8-slim
FROM tiangolo/uvicorn-gunicorn-fastapi:python3.9

ARG SERVICE_NAME='{{cookiecutter.project_name}}'

WORKDIR /app

# timezone
ENV TZ=Asia/Shanghai
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list \
    && sed -i 's/security.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list \
    && apt-get update \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone \
    && apt-get install tzdata

# 安装supervisor
RUN apt-get update && apt-get install -y supervisor
RUN echo "files = /app/supervisord/*.ini" >> /etc/supervisor/supervisord.conf

# RUN pip install supervisor -i https://pypi.douban.com/simple

#RUN  apt-get --allow-unauthenticated upgrade
#RUN apt-get update
#RUN apt-get install -y libkrb5-dev
#RUN apt-get update
#RUN apt-get install -y supervisor
#RUN echo "files = /app/supervisor/*.ini" >> /etc/supervisor/supervisord.conf

# 安装包
RUN pwd
RUN pip install --upgrade pip -i https://pypi.douban.com/simple
COPY requirements.txt .
RUN pip install -r requirements.txt  -i https://pypi.douban.com/simple


EXPOSE 5000
# start supervisord
CMD ["supervisord", "--nodaemon", "-c", "/etc/supervisor/supervisord.conf"]
