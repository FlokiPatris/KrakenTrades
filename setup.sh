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
log_warn(){ echo "${LOG_PREFIX} ⚠️ $*"; }
log_err() { echo "${LOG_PREFIX} ❌ $*" >&2; exit 1; }

# === Install pyenv ===
install_pyenv() {
    if command -v pyenv &>/dev/null; then
        log "pyenv is already installed."
        return
    fi

    log "Installing pyenv..."
    curl https://pyenv.run | bash

    local BASHRC="${HOME}/.bashrc"

    if ! grep -q 'pyenv init' "$BASHRC"; then
        cat <<EOF >> "$BASHRC"

# pyenv setup
export PYENV_ROOT="\$HOME/.pyenv"
export PATH="\$PYENV_ROOT/bin:\$PATH"
eval "\$(pyenv init --path)"
eval "\$(pyenv init -)"
EOF
        log "Patched .bashrc for pyenv"
    fi

    export PYENV_ROOT="$HOME/.pyenv"
    export PATH="$PYENV_ROOT/bin:$PATH"
    eval "$(pyenv init --path)"
    eval "$(pyenv init -)"
}

# === Setup Python version ===
setup_python() {
    if ! pyenv versions | grep -q "${PYTHON_VERSION}"; then
        log "Installing Python ${PYTHON_VERSION}..."
        pyenv install "${PYTHON_VERSION}" || log_err "Python install failed"
    fi

    pyenv global "${PYTHON_VERSION}"
    log "✅ Using Python: $(python --version)"
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
}

# === Configure Poetry environment ===
configure_poetry_env() {
    log "Configuring Poetry with Python ${PYTHON_VERSION}..."
    poetry env use "$(pyenv which python)" || log_err "Poetry environment setup failed"
}

# === Install dependencies ===
install_dependencies() {
    log "Installing project dependencies..."
    poetry install --no-root || log_err "Dependency installation failed"
}

# === Load environment variables ===
load_env_variables() {
    if [ ! -f "${ENV_FILE}" ]; then
        log_warn "No ${ENV_FILE} found. Skipping env load."
        return
    fi

    log "Loading environment from ${ENV_FILE}..."
    export $(grep -v '^#' "${ENV_FILE}" | xargs)
}

# === Optionally run main.py ===
run_main_script() {
    if [ ! -f "main.py" ]; then
        log_warn "No main.py found. Skipping execution."
        return
    fi

    log "Running main.py..."
    poetry run python main.py || log_err "main.py execution failed"
}

# === Entrypoint ===
main() {
    log "🚀 KrakenTrades setup started"
    install_pyenv
    setup_python
    install_poetry
    configure_poetry_env
    install_dependencies
    load_env_variables
    run_main_script
    log "✅ KrakenTrades setup completed successfully"
}

main "$@"
