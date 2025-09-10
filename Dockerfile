# syntax=docker/dockerfile:1.7

# ====================================================================================================
# 📝 Multi-Stage Docker Overview
# ====================================================================================================
# ┌───────────────────────────┐     ┌───────────────────────────┐     ┌───────────────────────────┐  #
# │ Builder Stage             │     │ Runtime Stage             │     │ Key Insights              │  #
# ├───────────────────────────┤     ├───────────────────────────┤     ├───────────────────────────┤  #
# │ Base: python:3.11-slim    │     │ Base: python:3.11-slim    │     │ • Builder stage ensures   │  #
# │ Purpose: compile Python   │     │ Purpose: minimal runtime  │     │   correct compilation for │  #
# │ packages & build deps     │     │ environment & security    │     │   packages with native    │  #
# │ Actions:                  │     │ Actions:                  │     │   extensions.             │  #
# │   • Install build tools   │     │   • Install runtime deps  │     │ • Runtime stage remains   │  #
# │     (gcc, make, build-    │ ––> │     (ca-certificates)     │ ––> │   lightweight, secure,    │  #
# │      essential, etc.)     │     │                           │     │   and fast to deploy.     │  #
# │   • Copy source code      │     │   • Copy pre-built Python │     │ • Separation improves CI/ │  #
# │   • Run `make install-    │     │     packages from builder │     │   CD caching and security.│  #
# │     deps` for Python deps │     │   • Copy app code & set   │     │ • Some runtime deps       │  #
# │ Output: compiled Python   │     │     permissions           │     │   (e.g., 7z) are needed   │  #
# │ packages in /usr/local/...│     │   • Run app as non-root   │     │   only at execution time. │  #
# └───────────────────────────┘     └───────────────────────────┘     └───────────────────────────┘  #
# ====================================================================================================

########################################################
# 1) Builder stage
########################################################
FROM python:3.11-slim AS builder

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    APP_HOME=/app

# Install build dependencies
RUN --mount=type=cache,target=/var/cache/apt \
    apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        gcc \
        curl \
        git \
        make \
    && rm -rf /var/lib/apt/lists/*

WORKDIR ${APP_HOME}

# Copy code first (to allow Makefile caching)
COPY . .

# Install Python dependencies via Makefile target
RUN make install-deps

########################################################
# 2) Runtime stage
########################################################
FROM python:3.11-slim AS runtime

ENV APP_HOME=/app \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UPLOADS_DIR=/app/uploads

# Runtime user setup
ARG APP_USER=appuser
ARG APP_UID=10001
ARG APP_GID=10001

# Install runtime dependencies
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
