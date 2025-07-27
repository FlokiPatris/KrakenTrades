# Dockerfile.test
FROM python:3.11-slim

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y build-essential curl && \
    pip install --no-cache-dir poetry

# Copy only relevant files for dependency install
COPY pyproject.toml poetry.lock ./

# Install dependencies (including dev-deps)
RUN poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi

# Copy the full source
COPY . .

# Run tests by default
CMD ["pytest", "--tb=short", "-q"]
