#!/usr/bin/env bash
# config.sh — Centralized environment defaults for .ci scripts.
#
# Usage:
#   source ".ci/common/config.sh"
#
# Notes:
#   - Minimal, central place for defaults.
#   - Override via CI workflow env or local export.

# -------------------------------
# SARIF and report paths
# -------------------------------
: "${SARIF_OUT_DIR:=${PWD}/sarif-reports}"  # Directory for SARIF and other CI reports

# -------------------------------
# Repository root
# -------------------------------
: "${GITHUB_WORKSPACE:=${PWD}}"  # CI sets this, fallback to current directory

# -------------------------------
# Tool versions (defaults)
# -------------------------------
: "${PYTHON_VERSION:=3.11}"      # Python version to use
: "${BANDIT_VERSION:=1.8.6}"     # Bandit version
: "${PIP_AUDIT_VERSION:=2.9.0}"  # pip-audit version
: "${SHELLCHECK_VERSION:=0.9.0}" # ShellCheck advisory/default version
: "${TRIVY_VERSION:=0.51.4}"     # Trivy version

# -------------------------------
# Gitleaks Docker defaults
# -------------------------------
: "${GITLEAKS_IMAGE:=zricethezav/gitleaks}" # Gitleaks image name
: "${GITLEAKS_IMAGE_TAG:=8.18.2}"           # Gitleaks image tag

# -------------------------------
# Installer toggles
# -------------------------------
: "${SKIP_INSTALLS:=false}"       # Skip installing CI tools if true
: "${SKIP_PIP_INSTALL:=false}"    # Skip pip install if true

# -------------------------------
# Trivy behavior
# -------------------------------
: "${TRIVY_EXIT_CODE:=0}"         # 0 = do not fail on findings; 1 = fail

# -------------------------------
# Export variables for other scripts
# -------------------------------
export SARIF_OUT_DIR GITHUB_WORKSPACE PYTHON_VERSION BANDIT_VERSION \
       PIP_AUDIT_VERSION SHELLCHECK_VERSION TRIVY_VERSION
export GITLEAKS_IMAGE GITLEAKS_IMAGE_TAG
export SKIP_INSTALLS SKIP_PIP_INSTALL TRIVY_EXIT_CODE
