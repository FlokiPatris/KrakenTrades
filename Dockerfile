# Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY . .

RUN pip install poetry && poetry install --no-root

CMD ["pytest", "tests"]
