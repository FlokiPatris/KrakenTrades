#!/usr/bin/env bash

# === Strict mode for reliability ===
set -e      # Exit on errors
set -u      # Treat unset variables as errors
set -o pipefail  # Catch failures in pipelines

# === Configuration ===
readonly PYTHON_VERSION="3.10"
readonly ENV_FILE=".env"
readonly PYENV_HOME="${HOME}/.pyenv"
readonly POETRY_INSTALL_URL="https://install.python-poetry.org"
readonly LOG_PREFIX="[KrakenTrades Setup]"

# === Log helpers ===
log()     { echo "${LOG_PREFIX} $*"; }
log_warn(){ echo "${LOG_PREFIX} ⚠️ $*"; }
log_err() { echo "${LOG_PREFIX} ❌ $*" >&2; exit 1; }

# === Curl workaround for Git Bash SSL ===
apply_windows_curl_fix() {
    if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
        log "Detected Git Bash on Windows — forcing curl to use OpenSSL"
        export CURL_SSL_BACKEND=openssl
    fi
}

# === Install pyenv-win for Windows ===
install_pyenv_win() {
    # Add pyenv-win to PATH early
    export PATH="${PYENV_HOME}/pyenv-win/bin:${PYENV_HOME}/pyenv-win/shims:$PATH"

    if command -v pyenv &>/dev/null; then
        log "pyenv-win is available."
        return
    fi

    if [ -d "${PYENV_HOME}/pyenv-win" ]; then
        log "pyenv-win directory already exists — skipping clone"
        return
    fi

    log "Cloning pyenv-win into ${PYENV_HOME}/pyenv-win..."
    git clone https://github.com/pyenv-win/pyenv-win.git "${PYENV_HOME}/pyenv-win" || log_err "Failed to clone pyenv-win"
}


# === Setup Python with pyenv-win ===
setup_python() {
    if ! pyenv versions | grep -q "${PYTHON_VERSION}"; then
        log "Installing Python ${PYTHON_VERSION} via pyenv-win..."
        pyenv install "${PYTHON_VERSION}" || log_err "Python ${PYTHON_VERSION} install failed"
    fi

    pyenv global "${PYTHON_VERSION}"
    log "Using Python: $(python --version)"
}

# === Install Poetry ===
install_poetry() {
    if command -v poetry &>/dev/null; then
        log "Poetry already installed."
        return
    fi

    log "Installing Poetry..."
    curl -sSL "${POETRY_INSTALL_URL}" | python - || log_err "Poetry install failed"
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

# === Orchestrator ===
main() {
    log "🚀 KrakenTrades setup started"

    apply_windows_curl_fix
    install_pyenv_win
    setup_python
    install_poetry
    configure_poetry_env
    install_dependencies
    load_env_variables
    run_main_script

    log "✅ KrakenTrades setup completed successfully"
}

main "$@"
