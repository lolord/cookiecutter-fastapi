FROM mcr.microsoft.com/devcontainers/python:3.11

RUN apt-get update \
  && apt-get install -y --no-install-recommends \
    netcat-openbsd \
    git-lfs \
  && apt-get clean autoclean \
  && apt-get autoremove -y \
  && rm -rf /var/lib/apt/lists/* \
  && rm -f /var/cache/apt/archives/*.deb

# Install task
# RUN curl -sL https://taskfile.dev/install.sh | sh
# ENV PATH=/root/.bin/:/root/.local/bin/:${PATH}

RUN apt install build-essential
RUN make --version

# Install devtools
RUN python -m pip install go-task-bin pdm pre-commit -i https://pypi.tuna.tsinghua.edu.cn/simple
