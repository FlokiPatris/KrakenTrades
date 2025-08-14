#!/usr/bin/env bash

# === Strict mode for reliability ===
set -euo pipefail

# === Configuration ===
readonly PYTHON_VERSION="3.10.13"
readonly ENV_FILE=".env"
readonly POETRY_INSTALL_URL="https://install.python-poetry.org"
readonly LOG_PREFIX="[KrakenTrades Setup]"

# === Log helpers ===
log()     { echo "${LOG_PREFIX} $*"; }
log_warn(){ echo "${LOG_PREFIX} ⚠️ $*" >&2; }
log_err() { echo "${LOG_PREFIX} ❌ $*" >&2; exit 1; }

# === Install system dependencies ===
install_build_dependencies() {
    log "Installing system build dependencies..."
    sudo apt update && sudo apt install -y \
        build-essential libssl-dev zlib1g-dev libbz2-dev \
        libreadline-dev libsqlite3-dev curl libncursesw5-dev \
        xz-utils tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev \
        python3 python3-pip \
        || log_err "Failed to install system dependencies"
    log "✅ System dependencies installed"
}

# === Install pyenv ===
install_pyenv() {
    if command -v pyenv &>/dev/null; then
        log "pyenv is already installed."
        return
    fi

    log "Installing pyenv..."
    curl https://pyenv.run | bash || log_err "pyenv install script failed"

    local BASHRC="${HOME}/.bashrc"
    if ! grep -q 'pyenv init' "$BASHRC"; then
        cat <<EOF >> "$BASHRC"

# pyenv setup
export PYENV_ROOT="\$HOME/.pyenv"
export PATH="\$PYENV_ROOT/bin:\$PATH"
eval "\$(pyenv init --path)"
eval "\$(pyenv init -)"
EOF
        log "✅ .bashrc updated with pyenv configuration"
    fi

    export PYENV_ROOT="$HOME/.pyenv"
    export PATH="$PYENV_ROOT/bin:$PATH"
    eval "$(pyenv init --path)"
    eval "$(pyenv init -)"
    log "✅ pyenv installed and initialized"
}

# === Setup Python version ===
setup_python() {
    if ! pyenv versions | grep -q "${PYTHON_VERSION}"; then
        log "Installing Python ${PYTHON_VERSION} via pyenv..."
        pyenv install "${PYTHON_VERSION}" || log_err "Python install failed"
    fi

    pyenv global "${PYTHON_VERSION}"
    log "✅ Python environment set: $(python --version)"
}

# === Install Poetry ===
install_poetry() {
    if command -v poetry &>/dev/null; then
        log "Poetry already installed."
        return
    fi

    log "Installing Poetry..."
    curl -sSL "${POETRY_INSTALL_URL}" | python3 - || log_err "Poetry install failed"
    export PATH="${HOME}/.local/bin:$PATH"
    log "✅ Poetry installed"
}

# === Configure Poetry environment ===
configure_poetry_env() {
    log "Configuring Poetry to use Python ${PYTHON_VERSION}..."
    poetry env use "$(pyenv which python)" || log_err "Poetry environment setup failed"
    log "✅ Poetry is now using Python ${PYTHON_VERSION}"
}

# === Install dependencies ===
install_dependencies() {
    log "Installing project dependencies via Poetry..."
    poetry install --no-root || log_err "Dependency installation failed"
    log "✅ Project dependencies installed"
}

# === Load environment variables ===
load_env_variables() {
    if [ ! -f "${ENV_FILE}" ]; then
        log_warn "No ${ENV_FILE} found. Skipping environment variable load."
        return
    fi

    log "Loading environment variables from ${ENV_FILE}..."
    export $(grep -v '^#' "${ENV_FILE}" | xargs) || log_warn "Failed to load some variables"
    log "✅ Environment variables loaded"
}

# === Instructions for manual execution ===
show_manual_run_instructions() {
    log "📝 Setup complete. To run the KrakenTrades parser manually:"
    echo -e "\n🔧 Run:\n  poetry run python main.py\n"
    echo -e "📂 Ensure your PDF path is correct. If running from WSL, use:\n  /mnt/c/Users/<yourname>/Downloads/trades.pdf\n"
    echo -e "📦 Example .env content:\n  KRAKEN_TRADES_PDF=/mnt/c/Users/fkotr/Downloads/trades.pdf\n  PARSED_TRADES_EXCEL=../kraken_parsed_trades.xlsx\n"
}

# === Entrypoint ===
main() {
    log "🚀 KrakenTrades setup started"
    install_build_dependencies
    install_pyenv
    setup_python
    install_poetry
    configure_poetry_env
    install_dependencies
    load_env_variables
    show_manual_run_instructions
    log "🏁 KrakenTrades setup finished. You’re good to go!"
}

main "$@"
