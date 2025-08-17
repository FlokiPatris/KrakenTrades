#!/usr/bin/env bash
# config.sh — Centralized environment defaults for .ci scripts.
# Source after strict_mode.sh:
#   source ".ci/common/strict_mode.sh"
#   source ".ci/common/config.sh"
#
# Keep this file minimal and avoid unused variables.
# Override these at runtime (CI workflow env or local export) as needed.

# Where SARIF and other report artifacts are written
: "${SARIF_OUT_DIR:=${PWD}/sarif-reports}"

# Repo root (CI sets GITHUB_WORKSPACE typically)
: "${GITHUB_WORKSPACE:=${PWD}}"

# Tool versions (set sensible defaults, override in CI if needed)
: "${PYTHON_VERSION:=3.11}"
: "${BANDIT_VERSION:=1.8.6}"
: "${PIP_AUDIT_VERSION:=2.9.0}"
: "${SHELLCHECK_VERSION:=0.9.0}"   # advisory/default, not used for auto-download here
: "${TRIVY_VERSION:=0.51.4}"

# Gitleaks image defaults (we prefer Docker runner for gitleaks)
: "${GITLEAKS_IMAGE:=zricethezav/gitleaks}"
: "${GITLEAKS_IMAGE_TAG:=8.18.2}"

# Installer toggles: set to "true" in CI if your image already provides these tools
: "${SKIP_INSTALLS:=false}"
: "${SKIP_PIP_INSTALL:=false}"

# How to treat Trivy findings (0 = do not fail, 1 = fail on findings)
: "${TRIVY_EXIT_CODE:=0}"

export SARIF_OUT_DIR GITHUB_WORKSPACE PYTHON_VERSION BANDIT_VERSION PIP_AUDIT_VERSION SHELLCHECK_VERSION TRIVY_VERSION
export GITLEAKS_IMAGE GITLEAKS_IMAGE_TAG
export SKIP_INSTALLS SKIP_PIP_INSTALL TRIVY_EXIT_CODE
