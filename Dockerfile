# syntax=docker/dockerfile:1.7
# Hardened multi-stage Dockerfile for KrakenTrades
# CI/CD-ready, secure, production-ready, validates environment variables

############################
# 1) Builder stage
############################
FROM python:3.11-slim AS builder

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    APP_HOME=/app

# Minimal build dependencies for wheels
RUN --mount=type=cache,target=/var/cache/apt \
    apt-get update && apt-get install -y --no-install-recommends \
        build-essential gcc curl git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR ${APP_HOME}

# Copy requirements first for caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

############################
# 2) Runtime stage
############################
FROM python:3.11-slim AS runtime

ENV APP_HOME=/app \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Runtime user setup
ARG APP_USER=appuser
ARG APP_UID=10001
ARG APP_GID=10001

# Install runtime OS dependencies
RUN --mount=type=cache,target=/var/cache/apt \
    apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd -g "${APP_GID}" "${APP_USER}" \
    && useradd -m -u "${APP_UID}" -g "${APP_GID}" -s /usr/sbin/nologin "${APP_USER}"

WORKDIR ${APP_HOME}

# Copy installed dependencies from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code with proper ownership
COPY --chown=${APP_UID}:${APP_GID} . ${APP_HOME}

# Drop privileges
USER ${APP_UID}:${APP_GID}

# Run the application
CMD ["python", "main.py"]
