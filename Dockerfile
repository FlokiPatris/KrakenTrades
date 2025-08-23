# syntax=docker/dockerfile:1.7

############################
# 1) Builder stage
############################
FROM python:3.11-slim AS builder

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    APP_HOME=/app

# Install build dependencies
RUN --mount=type=cache,target=/var/cache/apt \
    apt-get update && apt-get install -y --no-install-recommends \
        build-essential gcc curl git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR ${APP_HOME}

# Install Python dependencies first for caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the code and install editable package
COPY . .
RUN pip install --no-cache-dir -e .

############################
# 2) Runtime stage
############################
FROM python:3.11-slim AS runtime

ENV APP_HOME=/app \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UPLOADS_DIR=/app/uploads

# Runtime user setup
ARG APP_USER=appuser
ARG APP_UID=10001
ARG APP_GID=10001

RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd -g "${APP_GID}" "${APP_USER}" \
    && useradd -m -u "${APP_UID}" -g "${APP_GID}" -s /usr/sbin/nologin "${APP_USER}"

WORKDIR ${APP_HOME}

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy app code with correct ownership
COPY --chown=${APP_UID}:${APP_GID} . ${APP_HOME}

# Create uploads folder with proper permissions
RUN mkdir -p ${UPLOADS_DIR} && chown -R ${APP_UID}:${APP_GID} ${UPLOADS_DIR}

USER ${APP_UID}:${APP_GID}

CMD ["python", "main.py"]
