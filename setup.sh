set -euo pipefail

# === CONFIG ===
PYTHON_VERSION="3.10"
ENV_FILE=".env"
PYENV_ROOT="${HOME}/.pyenv"

echo "🚀 Starting KrakenTrades setup..."

# === 1. Install pyenv + Python ===
if ! command -v pyenv &>/dev/null; then
    echo "🐍 Installing pyenv..."
    curl https://pyenv.run | bash

    export PATH="$PYENV_ROOT/bin:$PYENV_ROOT/shims:$PATH"
    eval "$(pyenv init -)"
    eval "$(pyenv virtualenv-init -)"
else
    echo "✅ pyenv already installed."
fi

if ! pyenv versions --bare | grep -q "$PYTHON_VERSION"; then
    echo "📦 Installing Python $PYTHON_VERSION via pyenv..."
    pyenv install "$PYTHON_VERSION"
fi

pyenv global "$PYTHON_VERSION"
echo "🧪 Using Python $(python3 --version)"

# === 2. Install Poetry ===
if ! command -v poetry &>/dev/null; then
    echo "📦 Installing Poetry..."
    curl -sSL https://install.python-poetry.org | python3 -
    export PATH="${HOME}/.local/bin:$PATH"
else
    echo "✅ Poetry is already installed."
fi

# === 3. Set Python for Poetry ===
echo "🧪 Configuring Poetry to use Python $PYTHON_VERSION..."
poetry env use "$(pyenv which python)"

# === 4. Install Dependencies ===
echo "📦 Installing dependencies via Poetry..."
poetry install --no-root || { echo "❌ Dependency install failed."; exit 1; }

# === 5. Load .env (Optional) ===
if [ -f "$ENV_FILE" ]; then
    echo "🧪 Loading env variables from $ENV_FILE..."
    export $(grep -v '^#' "$ENV_FILE" | xargs)
else
    echo "ℹ️ No $ENV_FILE found. Continuing without env vars."
fi

# === 6. Optional: Run Main Script ===
if [ -f "main.py" ]; then
    echo "🚀 Running main.py..."
    poetry run python main.py
else
    echo "ℹ️ No main.py found. Setup complete."
fi

echo "✅ KrakenTrades setup finished successfully!"
