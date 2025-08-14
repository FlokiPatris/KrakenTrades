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

# Install minimal build deps only if needed for wheels (e.g., cryptography)
# Keep this list minimal and remove afterward.
RUN --mount=type=cache,target=/var/cache/apt \
    apt-get update && apt-get install -y --no-install-recommends \
      build-essential gcc curl git \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry in a reproducible way
RUN pip install --no-cache-dir "poetry==${POETRY_VERSION}"

WORKDIR /app

# Copy lockfiles first for better layering and caching
# If you use requirements.txt instead of poetry, adapt accordingly.
COPY pyproject.toml poetry.lock ./

# Export to requirements to ensure reproducible runtime install in final stage
RUN poetry export -f requirements.txt --without-hashes -o /tmp/requirements.txt

# Copy application source (keep .dockerignore tight)
COPY . /app

############################
# 2) Runtime stage
############################
FROM python:3.11-slim AS runtime

# Security: create non-root user and group with fixed IDs for consistency
ARG APP_USER=appuser
ARG APP_UID=10001
ARG APP_GID=10001

# Set python to not write .pyc and use UTF-8; keep logs unbuffered
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install only runtime OS deps (requests/certifi rely on CA certs)
RUN --mount=type=cache,target=/var/cache/apt \
    apt-get update && apt-get install -y --no-install-recommends \
      ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd -g "${APP_GID}" "${APP_USER}" \
    && useradd -m -u "${APP_UID}" -g "${APP_GID}" -s /usr/sbin/nologin "${APP_USER}"

WORKDIR /app

# Copy only what’s needed at runtime
COPY --from=builder /tmp/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt \
    && rm -f /tmp/requirements.txt

# Copy app source (exclude tests/docs in .dockerignore)
COPY --chown=${APP_UID}:${APP_GID} . /app

# Drop privileges
USER ${APP_UID}:${APP_GID}

# Default command; prefer passing args via ENTRYPOINT + CMD
# Use a thin runner, not poetry, in runtime image to reduce layers/attack surface
ENTRYPOINT ["python", "main.py"]

# Runtime hardening is applied at run/compose time:
# - Read-only FS:          docker run --read-only ...
# - Drop capabilities:     docker run --cap-drop=ALL --cap-add=NET_BIND_SERVICE ...
# - No new privileges:     docker run --security-opt=no-new-privileges ...
# - Seccomp/AppArmor:      docker run --security-opt=seccomp=default.json (or distro default)
