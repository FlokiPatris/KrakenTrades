#!/usr/bin/env bash

# Enable strict error handling (split for portability in Windows Git Bash)
set -e
set -u
set -o pipefail

# === CONFIGURATION ===
readonly PYTHON_VERSION="3.10"
readonly ENV_FILE=".env"
readonly PYENV_ROOT="${HOME}/.pyenv"
readonly POETRY_INSTALL_URL="https://install.python-poetry.org"
readonly LOG_PREFIX="[KrakenTrades Setup]"

# === Logging Helpers ===
log()    { echo "${LOG_PREFIX} $*"; }
log_err() { echo "${LOG_PREFIX} ❌ $*" >&2; exit 1; }

# === Helper: Setup pyenv ===
install_pyenv() {
    if ! command -v pyenv &>/dev/null; then
        log "Installing pyenv..."
        curl https://pyenv.run | bash || log_err "pyenv installation failed"
        export PATH="$PYENV_ROOT/bin:$PYENV_ROOT/shims:$PATH"
        eval "$(pyenv init -)"
        eval "$(pyenv virtualenv-init -)"
    else
        log "pyenv already installed."
    fi
}

setup_python() {
    if ! pyenv versions --bare | grep -q "${PYTHON_VERSION}"; then
        log "Installing Python ${PYTHON_VERSION} via pyenv..."
        pyenv install "${PYTHON_VERSION}" || log_err "Python install failed"
    fi
    pyenv global "${PYTHON_VERSION}"
    log "Using Python version: $(python3 --version)"
}

# === Helper: Setup Poetry ===
install_poetry() {
    if ! command -v poetry &>/dev/null; then
        log "Installing Poetry..."
        curl -sSL "${POETRY_INSTALL_URL}" | python3 - || log_err "Poetry install failed"
        export PATH="${HOME}/.local/bin:$PATH"
    else
        log "Poetry already installed."
    fi
}

configure_poetry_env() {
    log "Configuring Poetry to use Python ${PYTHON_VERSION}..."
    poetry env use "$(pyenv which python)" || log_err "Poetry environment setup failed"
}

install_dependencies() {
    log "Installing dependencies via Poetry..."
    poetry install --no-root || log_err "Dependency installation failed"
}

load_env_variables() {
    if [ -f "${ENV_FILE}" ]; then
        log "Loading environment variables from ${ENV_FILE}..."
        export $(grep -v '^#' "${ENV_FILE}" | xargs)
    else
        log "No .env file found. Continuing without environment vars."
    fi
}

run_main_script() {
    if [ -f "main.py" ]; then
        log "Executing main.py..."
        poetry run python main.py || log_err "main.py execution failed"
    else
        log "No main.py found. Skipping execution."
    fi
}

# === Orchestrator ===
main() {
    log "🚀 KrakenTrades setup started"

    # 🛡️ Git Bash SSL fix for Windows
    if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
        log "Detected Git Bash on Windows — configuring curl to use OpenSSL"
        export CURL_SSL_BACKEND=openssl
    fi

    install_pyenv
    setup_python
    install_poetry
    configure_poetry_env
    install_dependencies
    load_env_variables
    run_main_script

    log "✅ Setup finished successfully!"
}


main "$@"
