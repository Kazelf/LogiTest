# syntax=docker/dockerfile:1

FROM node:22-bookworm-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /workspace

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        bash \
        ca-certificates \
        curl \
        openssl \
        postgresql-client \
        python3 \
        python3-pip \
        python3-venv \
    && rm -rf /var/lib/apt/lists/*

COPY logitest-ai/package.json logitest-ai/package-lock.json ./logitest-ai/
COPY logitest-ai/apps/web/package.json ./logitest-ai/apps/web/package.json
COPY logitest-ai/packages/shared/package.json ./logitest-ai/packages/shared/package.json
RUN cd logitest-ai && npm install

COPY logitest-ai/apps/api/requirements.txt ./logitest-ai/apps/api/requirements.txt
RUN python3 -m venv ./logitest-ai/apps/api/.venv \
    && ./logitest-ai/apps/api/.venv/bin/python -m pip install --upgrade pip \
    && ./logitest-ai/apps/api/.venv/bin/python -m pip install --no-cache-dir -r ./logitest-ai/apps/api/requirements.txt

COPY shoplite/server/package.json shoplite/server/package-lock.json ./shoplite/server/
RUN cd shoplite/server && npm ci

COPY shoplite/client/package.json shoplite/client/package-lock.json ./shoplite/client/
RUN cd shoplite/client && npm ci

COPY logitest-ai/apps/web ./logitest-ai/apps/web
COPY logitest-ai/packages/shared ./logitest-ai/packages/shared
COPY logitest-ai/apps/api/app ./logitest-ai/apps/api/app
COPY logitest-ai/database ./logitest-ai/database
COPY logitest-ai/mock-data ./logitest-ai/mock-data
COPY logitest-ai/scripts ./logitest-ai/scripts

COPY shoplite/server/src ./shoplite/server/src
COPY shoplite/client/index.html ./shoplite/client/index.html
COPY shoplite/client/src ./shoplite/client/src

RUN cd shoplite/server && npm run prisma:generate

COPY docker ./docker
RUN chmod +x ./docker/entrypoint.sh \
    && mkdir -p ./shoplite/server/logs ./logitest-ai/generated-tests

EXPOSE 3000 4000 5173 8000

ENTRYPOINT ["/workspace/docker/entrypoint.sh"]
