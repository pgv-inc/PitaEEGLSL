# Define custom function directory
FROM python:3.12 AS build-image
LABEL maintainer="kezure <3447723+kezure@users.noreply.github.com>"

RUN apt-get update -y \
 && apt-get install -y git-lfs libhdf5-dev \
 && apt-get autoremove -y && apt-get autoclean -y

# Install Poetry and dependencies with .netrc for private repos
ARG POETRY_WITHOUT
ARG PACKAGE_NAME
ENV PACKAGE_NAME=${PACKAGE_NAME}
# poetryのPATHを$PATHに追加
ENV POETRY_HOME=/opt/poetry
ADD pyproject.toml poetry.lock ./
RUN --mount=type=secret,id=github,dst=/root/.netrc \
    pip3 install --no-cache-dir -U pip \
 && pip3 install --no-cache-dir poetry \
# 仮想環境を作成しない設定(コンテナ前提のため，仮想環境を作らない)
 && poetry config virtualenvs.create false \
 && poetry install --no-cache ${POETRY_WITHOUT} \
 && pip3 freeze \
 && pip3 list --outdate \ 
 && rm -rf pyproject.toml poetry.lock

FROM python:3.12-slim

# Include global arg in this stage of the build
ARG FUNCTION_DIR="/function"
RUN mkdir -p ${FUNCTION_DIR}

# Include global arg in this stage of the build
ARG PACKAGE_NAME
ENV PACKAGE_NAME=${PACKAGE_NAME}

# Set working directory to function root directory
WORKDIR ${FUNCTION_DIR}

# Copy in the built dependencies
COPY --from=build-image /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
ADD ./${PACKAGE_NAME} ./${PACKAGE_NAME}
ADD run.py ./

# Pass the name of the function handler as an argument to the runtime
CMD ["python", "run.py"]
