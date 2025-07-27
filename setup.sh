#!/bin/bash

# === CONFIG ===
REPO_URL="https://github.com/FlokiPatris/KrakenTrades.git"
PROJECT_DIR="KrakenTrades"

echo "🚀 Starting KrakenTrades setup..."

# === 1. Clone the repository ===
if [ -d "$PROJECT_DIR" ]; then
    echo "📁 Project directory '$PROJECT_DIR' already exists. Skipping clone."
else
    echo "🔗 Cloning repository from $REPO_URL..."
    git clone "$REPO_URL"
    if [ $? -ne 0 ]; then
        echo "❌ Failed to clone repository. Exiting."
        exit 1
    fi
fi

cd "$PROJECT_DIR" || { echo "❌ Failed to enter project directory. Exiting."; exit 1; }

# === 2. Install Poetry ===
if ! command -v poetry &> /dev/null; then
    echo "📦 Installing Poetry..."
    curl -sSL https://install.python-poetry.org | python3 -
    export PATH="$HOME/.local/bin:$PATH"
    if ! command -v poetry &> /dev/null; then
        echo "❌ Poetry installation failed. Exiting."
        exit 1
    fi
else
    echo "✅ Poetry is already installed."
fi

# === 3. Install dependencies ===
echo "📦 Installing dependencies with Poetry..."
poetry install
if [ $? -ne 0 ]; then
    echo "❌ Poetry failed to install dependencies. Exiting."
    exit 1
fi

# === 4. Load environment variables ===

# === 5. Run tests ===


# === 6. Optional: Run main script ===
if [ -f "main.py" ]; then
    echo "🚀 Running main.py..."
    poetry run python main.py
else
    echo "ℹ️ No main.py found. Setup complete."
fi

echo "✅ KrakenTrades setup complete!"