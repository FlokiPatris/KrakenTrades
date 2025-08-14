# syntax=docker/dockerfile:1.7
# Hardened multi-stage Dockerfile for KrakenTrades
# Goals:
# - Minimal attack surface (slim base, no build toolchain in final)
# - Reproducible dependency install (Poetry, no dev deps)
# - Non-root runtime user
# - Ready for read-only FS and capability drop at runtime
# - CI/CD-friendly and fast to build/cache

############################
# 1) Builder stage
############################
FROM python:3.11-slim AS builder

# Prevent interactive tzdata prompts and reduce image size
ENV DEBIAN_FRONTEND=noninteractive \
    POETRY_VERSION=1.8.3 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1

# Install minimal build deps only if needed for wheels
RUN --mount=type=cache,target=/var/cache/apt \
    apt-get update && apt-get install -y --no-install-recommends \
      build-essential gcc curl git \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install --no-cache-dir "poetry==${POETRY_VERSION}"

WORKDIR /app

# Copy lockfiles for caching
COPY pyproject.toml poetry.lock ./

# Export requirements for reproducible runtime install
RUN poetry export -f requirements.txt --without-hashes -o /tmp/requirements.txt

# Copy application source
COPY . /app

############################
# 2) Runtime stage
############################
FROM python:3.11-slim AS runtime

# Non-root user setup
ARG APP_USER=appuser
ARG APP_UID=10001
ARG APP_GID=10001

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install only runtime OS deps
RUN --mount=type=cache,target=/var/cache/apt \
    apt-get update && apt-get install -y --no-install-recommends \
      ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd -g "${APP_GID}" "${APP_USER}" \
    && useradd -m -u "${APP_UID}" -g "${APP_GID}" -s /usr/sbin/nologin "${APP_USER}"

WORKDIR /app

# Install Python dependencies
COPY --from=builder /tmp/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt \
    && rm -f /tmp/requirements.txt

# Copy application code
COPY --chown=${APP_UID}:${APP_GID} . /app

# Drop privileges
USER ${APP_UID}:${APP_GID}

ENTRYPOINT ["python", "main.py"]
