#!/usr/bin/env bash
# installations.sh — Idempotent installer helpers for CI tools.
#
# Usage:
#   source ".ci/common/installations.sh"
#   install_bandit_or_exit
#   install_pip_audit_or_exit
#
# Tools are NO-OP if already available.
#
# -------------------------------
# Helper Functions
# -------------------------------

# Determine Python command
_python_cmd() {
  if command -v python3 >/dev/null 2>&1; then
    printf "python3"
  elif command -v python >/dev/null 2>&1; then
    printf "python"
  else
    return 1
  fi
}

# Wrapper for pip installation
# Args:
#   $1 - package to install (e.g., "bandit[toml]")
_pip_install() {
  local pkg="$1"
  local py
  py="$(_python_cmd)" || die "Python not found; cannot install ${pkg}"

  "$py" -m pip install --upgrade pip >/dev/null 2>&1 || log_warn "pip upgrade failed"
  log_info "Installing Python package: ${pkg}"
  "$py" -m pip install --disable-pip-version-check --no-cache-dir "$pkg"
}

# -------------------------------
# Python Tool Installers
# -------------------------------

install_bandit_or_exit() {
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

install_pip_audit_or_exit() {
  if command -v pip-audit >/dev/null 2>&1 || \
     (_python_cmd >/dev/null 2>&1 && "$(_python_cmd)" -m pip show pip-audit >/dev/null 2>&1); then
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

# -------------------------------
# Shell Utilities Installers
# -------------------------------

install_shellcheck_or_exit() {
  if command -v shellcheck >/dev/null 2>&1; then
    log_info "shellcheck already installed, skipping."
    return 0
  fi

  log_warn "shellcheck not found. Install via package manager (apt/brew) or use an image that includes it."
  return 1
}

# -------------------------------
# Security Tools Installers
# -------------------------------

install_trivy_or_exit() {
  if command -v trivy >/dev/null 2>&1; then
    log_info "trivy already installed, skipping."
    return 0
  fi

  local ver="${TRIVY_VERSION:-}"
  if [[ -z "$ver" ]]; then
    log_warn "TRIVY_VERSION not set; skipping automatic install."
    return 1
  fi

  local tarball="trivy_${ver}_Linux-64bit.tar.gz"
  local url="https://github.com/aquasecurity/trivy/releases/download/v${ver}/${tarball}"
  local tmpdir
  tmpdir="$(mktemp -d)" || { log_warn "mktemp failed"; return 1; }

  if command -v curl >/dev/null 2>&1; then
    curl -fsSL -o "${tmpdir}/${tarball}" "${url}" || { log_warn "curl failed"; rm -rf "${tmpdir}"; return 1; }
  elif command -v wget >/dev/null 2>&1; then
    wget -q -O "${tmpdir}/${tarball}" "${url}" || { log_warn "wget failed"; rm -rf "${tmpdir}"; return 1; }
  else
    log_warn "Neither curl nor wget available; cannot auto-install trivy."
    rm -rf "${tmpdir}"
    return 1
  fi

  tar -xzf "${tmpdir}/${tarball}" -C "${tmpdir}" || { log_warn "tar extraction failed"; rm -rf "${tmpdir}"; return 1; }

  if mv "${tmpdir}"/*/trivy /usr/local/bin/trivy 2>/dev/null || mv "${tmpdir}/trivy" /usr/local/bin/trivy 2>/dev/null; then
    chmod 0755 /usr/local/bin/trivy || true
    log_info "trivy installed to /usr/local/bin/trivy"
  else
    log_warn "Could not move trivy to /usr/local/bin; using local tmpdir copy for this session."
    export PATH="${tmpdir}:${PATH}"
    log_info "Prepended ${tmpdir} to PATH"
  fi

  rm -rf "${tmpdir}" || true
}

install_gitleaks_or_exit() {
  if command -v gitleaks >/dev/null 2>&1; then
    log_info "gitleaks already installed, skipping."
    return 0
  fi

  log_warn "gitleaks not found locally. Recommended: run via Docker image (${GITLEAKS_IMAGE}:${GITLEAKS_IMAGE_TAG}) in CI."
  return 1
}
