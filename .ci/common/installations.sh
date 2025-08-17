#!/usr/bin/env bash
# installations.sh — Idempotent installer helpers for tools used in CI.
# Source after strict_mode.sh, config.sh, and sarif_utils.sh.
#
# Usage example:
#   install_bandit_or_exit
#   install_pip_audit_or_exit
# They will be NO-OP if the tool is already on PATH or SKIP flags are set.

# shellcheck disable=SC1090,SC2154

##############################
# Helper Functions
##############################

# Determine the Python command to use
_python_cmd() {
  if command -v python3 >/dev/null 2>&1; then
    printf "%s" "python3"
  elif command -v python >/dev/null 2>&1; then
    printf "%s" "python"
  else
    return 1
  fi
}

# Wrapper for pip installation
_pip_install() {
  local pkg="$1"
  local py
  py="$(_python_cmd)" || die "python not found; cannot install $pkg"
  # Best-effort pip upgrade
  "$py" -m pip install --upgrade pip >/dev/null 2>&1 || log_warn "pip upgrade failed"
  log_info "Installing Python package: $pkg"
  "$py" -m pip install --disable-pip-version-check --no-cache-dir "$pkg"
}

##############################
# Python Tool Installers
##############################

# Install Bandit (Python security linter)
install_bandit_or_exit() {
  if [[ "${SKIP_PIP_INSTALL:-false}" == "true" || "${SKIP_INSTALLS:-false}" == "true" ]]; then
    log_info "Skipping Bandit install due to SKIP_* flags."
    return 0
  fi
  if command -v bandit >/dev/null 2>&1; then
    log_info "bandit already installed, skipping."
    return 0
  fi

  local ver="${BANDIT_VERSION:-}"
  if [[ -n "$ver" ]]; then
    _pip_install "bandit[toml]==${ver}" || die "Failed to install bandit"
  else
    _pip_install "bandit[toml]" || die "Failed to install bandit"
  fi
}

# Install pip-audit (Python package vulnerability scanner)
install_pip_audit_or_exit() {
  if [[ "${SKIP_PIP_INSTALL:-false}" == "true" || "${SKIP_INSTALLS:-false}" == "true" ]]; then
    log_info "Skipping pip-audit install due to SKIP_* flags."
    return 0
  fi
  if command -v pip-audit >/dev/null 2>&1 || _python_cmd >/dev/null 2>&1 && "$(_python_cmd)" -m pip show pip-audit >/dev/null 2>&1; then
    log_info "pip-audit already available, skipping."
    return 0
  fi

  local ver="${PIP_AUDIT_VERSION:-}"
  if [[ -n "$ver" ]]; then
    _pip_install "pip-audit==${ver}" || die "Failed to install pip-audit"
  else
    _pip_install "pip-audit" || die "Failed to install pip-audit"
  fi
}

##############################
# Shell Utilities Installers
##############################

# Install ShellCheck (shell script linter)
install_shellcheck_or_exit() {
  if command -v shellcheck >/dev/null 2>&1; then
    log_info "shellcheck already available, skipping."
    return 0
  fi
  if [[ "${SKIP_INSTALLS:-false}" == "true" ]]; then
    log_info "SKIP_INSTALLS set; skipping shellcheck install. Please ensure shellcheck exists in CI image."
    return 0
  fi

  log_warn "shellcheck not found. Please install it via package manager (apt/brew) or use an image that includes it."
  return 1
}

##############################
# Security Tools Installers
##############################

# Install Trivy (container/image vulnerability scanner)
install_trivy_or_exit() {
  if command -v trivy >/dev/null 2>&1; then
    log_info "trivy already available, skipping."
    return 0
  fi
  if [[ "${SKIP_INSTALLS:-false}" == "true" ]]; then
    log_info "SKIP_INSTALLS set; skipping trivy install. Ensure trivy present in CI image if you expect scan to run."
    return 0
  fi

  local ver="${TRIVY_VERSION:-}"
  if [[ -z "$ver" ]]; then
    log_warn "TRIVY_VERSION not set; skipping automatic Trivy install."
    return 1
  fi

  # Best-effort download for Linux/amd64
  local tarball="trivy_${ver}_Linux-64bit.tar.gz"
  local url="https://github.com/aquasecurity/trivy/releases/download/v${ver}/${tarball}"
  local tmpdir
  tmpdir="$(mktemp -d)" || { log_warn "mktemp failed"; return 1; }

  if command -v curl >/dev/null 2>&1; then
    curl -fsSL -o "${tmpdir}/${tarball}" "${url}" || { log_warn "curl failed to fetch trivy"; rm -rf "${tmpdir}"; return 1; }
  elif command -v wget >/dev/null 2>&1; then
    wget -q -O "${tmpdir}/${tarball}" "${url}" || { log_warn "wget failed to fetch trivy"; rm -rf "${tmpdir}"; return 1; }
  else
    log_warn "Neither curl nor wget available; cannot auto-install trivy."
    rm -rf "${tmpdir}"
    return 1
  fi

  tar -xzf "${tmpdir}/${tarball}" -C "${tmpdir}" || { log_warn "tar failed"; rm -rf "${tmpdir}"; return 1; }

  # Attempt to move binary to /usr/local/bin
  if mv "${tmpdir}"/*/trivy /usr/local/bin/trivy 2>/dev/null; then
    chmod 0755 /usr/local/bin/trivy || true
    log_info "trivy installed to /usr/local/bin/trivy"
  elif mv "${tmpdir}/trivy" /usr/local/bin/trivy 2>/dev/null; then
    chmod 0755 /usr/local/bin/trivy || true
    log_info "trivy installed to /usr/local/bin/trivy"
  else
    log_warn "Could not move trivy to /usr/local/bin (permission denied). Using local copy in ${tmpdir} for this run."
    export PATH="${tmpdir}:${PATH}"
    log_info "Prepended ${tmpdir} to PATH for this session"
  fi

  rm -rf "${tmpdir}" || true
  return 0
}

# Gitleaks (secret detection) guidance
install_gitleaks_or_exit() {
  # gitleaks is typically run via docker image in our runners.
  if [[ -n "$(command -v gitleaks 2>/dev/null)" ]]; then
    log_info "gitleaks binary already present; skipping."
    return 0
  fi
  if [[ "${SKIP_INSTALLS:-false}" == "true" ]]; then
    log_info "SKIP_INSTALLS set; skipping gitleaks install."
    return 0
  fi

  log_warn "gitleaks not found locally. Recommended: run via Docker image (${GITLEAKS_IMAGE}:${GITLEAKS_IMAGE_TAG}) in CI."
  return 1
}
