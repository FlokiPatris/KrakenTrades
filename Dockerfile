# KrakenTrades Dockerfile (Ubuntu + pyenv + poetry)

# 📦 Base image — using Ubuntu 24.04 as our OS foundation
FROM ubuntu:24.04

# ⚙️ Prevent interactive prompts during package installs
ENV DEBIAN_FRONTEND=noninteractive

# 🐍 Python environment setup

ENV PYTHON_VERSION=3.10.13
ENV PYENV_ROOT=/root/.pyenv
ENV PATH="$PYENV_ROOT/bin:$PYENV_ROOT/shims:$PATH"

# 🔧 Install build tools and Python compilation dependencies
RUN apt update && apt install -y \
    build-essential curl git libssl-dev zlib1g-dev libbz2-dev \
    libreadline-dev libsqlite3-dev libncursesw5-dev xz-utils tk-dev \
    libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev \
    && rm -rf /var/lib/apt/lists/*                # Clean up apt cache

# 🐒 Install pyenv to manage Python versions
RUN curl https://pyenv.run | bash

# 🐍 Install specified Python version using pyenv
RUN bash -c "source ~/.bashrc && pyenv install $PYTHON_VERSION && pyenv global $PYTHON_VERSION"

# 🎼 Install Poetry (Python dependency manager)
RUN curl -sSL https://install.python-poetry.org | python3 && \
    ln -s /root/.local/bin/poetry /usr/local/bin/poetry  # Add poetry to global path

# 🗂️ Set the working directory inside the container
WORKDIR /app

# 📁 Copy project files from host into the container
COPY . .

# 📦 Install Python dependencies defined in pyproject.toml
RUN poetry config virtualenvs.create false && poetry install --no-root

# 🚀 Run your app using Poetry — entry point for container execution
CMD ["poetry", "run", "python", "main.py"]
