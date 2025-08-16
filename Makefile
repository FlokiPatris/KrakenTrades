# File: Makefile
# Purpose: Run the same AppSec scans locally as in .github/workflows/appsec-security.yml
# Security: strict shell, locked-down artifacts, no secret echo

SHELL := /bin/bash
.SHELLFLAGS := -eu -o pipefail -c
.ONESHELL:
.DEFAULT_GOAL := help
.RECIPEPREFIX := >

# Load optional .env (commit only .env.example)
ifneq (,$(wildcard .env))
    include .env
    export
endif

# ===== Global defaults =====
PYTHON_VERSION        ?= 3.11
SARIF_DIR             ?= sarif-reports
PIP_AUDIT_VERSION     ?= 2.9.0
BANDIT_VERSION        ?= 1.8.6
GITLEAKS_IMAGE        ?= zricethezav/gitleaks
GITLEAKS_IMAGE_TAG    ?= 8.18.2
GITLEAKS_FALLBACK_TAG ?= latest
TRIVY_VERSION         ?= 0.51.4
TRIVY_SEVERITY        ?= HIGH,CRITICAL
TRIVY_EXIT_CODE       ?= 0  # 0=do not fail build; 1=fail on HIGH/CRITICAL
CODESPELL_VERSION     ?= 2.3.0

# Paths and security defaults
CI_BIN := .ci/bin
UMASK  := 077

# Internal helpers
SCRIPTS := \
    $(CI_BIN)/run_trivy.sh \
    $(CI_BIN)/run_gitleaks.sh \
    $(CI_BIN)/run_pip_audit.sh \
    $(CI_BIN)/run_bandit.sh

REQ_TOOLS := bash awk grep docker

# ===== Targets =====
.PHONY: help all preflight validate prepare-dir trivy gitleaks pip-audit bandit spellcheck harden clean-sarif print-config

help: ## Show this help
>   @grep -E '^[a-zA-Z0-9._-]+:.*?## ' $(MAKEFILE_LIST) | \
>   awk 'BEGIN {FS = ":.*?## "}; {printf "%-20s %s\n", $$1, $$2}'

print-config: ## Print non-sensitive effective configuration
>   @echo "Config:"
>   @echo "  PYTHON_VERSION        = $(PYTHON_VERSION)"
>   @echo "  SARIF_DIR             = $(SARIF_DIR)"
>   @echo "  PIP_AUDIT_VERSION     = $(PIP_AUDIT_VERSION)"
>   @echo "  BANDIT_VERSION        = $(BANDIT_VERSION)"
>   @echo "  GITLEAKS_IMAGE        = $(GITLEAKS_IMAGE)"
>   @echo "  GITLEAKS_IMAGE_TAG    = $(GITLEAKS_IMAGE_TAG)"
>   @echo "  GITLEAKS_FALLBACK_TAG = $(GITLEAKS_FALLBACK_TAG)"
>   @echo "  TRIVY_VERSION         = $(TRIVY_VERSION)"
>   @echo "  TRIVY_SEVERITY        = $(TRIVY_SEVERITY)"
>   @echo "  TRIVY_EXIT_CODE       = $(TRIVY_EXIT_CODE)"
>   @echo "  CODESPELL_VERSION     = $(CODESPELL_VERSION)"
>   @echo "  CI_BIN                = $(CI_BIN)"
>   @echo "  UMASK                 = $(UMASK)"

prepare-dir: ## Create SARIF dir with secure permissions
>   umask $(UMASK)
>   mkdir -p "$(SARIF_DIR)"
>   chmod 700 "$(SARIF_DIR)" || true

preflight: ## Verify required tools and scripts exist
>   for t in $(REQ_TOOLS); do \
>       if ! command -v $$t >/dev/null 2>&1; then echo "Error: required tool '$$t' not found in PATH"; exit 1; fi; \
>   done
>   missing=0; \
>   for s in $(SCRIPTS); do \
>       if [ ! -f "$$s" ]; then echo "Error: missing script '$$s'"; missing=1; fi; \
>   done; \
>   if [ $$missing -ne 0 ]; then exit 1; fi
>   $(MAKE) prepare-dir
>   if ! command -v docker >/dev/null 2>&1; then \
>       echo "Note: 'docker' not found. Trivy/Gitleaks scripts will try native binaries if available."; \
>   fi

validate: ## Validate required secrets if script is available
>   if [ -x "$(CI_BIN)/common.sh" ]; then \
>       bash "$(CI_BIN)/common.sh" validate_required_secrets; \
>   else \
>       echo "Note: $(CI_BIN)/common.sh not found; skipping required secrets validation."; \
>   fi

all: preflight validate trivy pip-audit bandit shellcheck harden gitleaks 

shellcheck: ## Run ShellCheck on tracked shell script files
>    @if ! command -v shellcheck >/dev/null 2>&1; then \
>        sudo apt-get update && sudo apt-get install -y shellcheck; \
>    fi
>    bash "$(CI_BIN)/run_shellcheck.sh"

trivy: prepare-dir ## Run Trivy filesystem scan
>   SARIF_DIR="$(SARIF_DIR)"; export SARIF_DIR
>   SARIF_FILE="trivy.sarif"; export SARIF_FILE
>   TRIVY_VERSION="$(TRIVY_VERSION)"; export TRIVY_VERSION
>   TRIVY_SEVERITY="$(TRIVY_SEVERITY)"; export TRIVY_SEVERITY
>   TRIVY_TARGET="."; export TRIVY_TARGET
>   TRIVY_MODE="fs"; export TRIVY_MODE
>   TRIVY_IGNORE_UNFIXED="true"; export TRIVY_IGNORE_UNFIXED
>   TRIVY_EXIT_CODE="$(TRIVY_EXIT_CODE)"; export TRIVY_EXIT_CODE
>   bash "$(CI_BIN)/run_trivy.sh"

pip-audit: prepare-dir ## Run pip-audit on dependencies
>   SARIF_DIR="$(SARIF_DIR)"; export SARIF_DIR
>   PIP_AUDIT_VERSION="$(PIP_AUDIT_VERSION)"; export PIP_AUDIT_VERSION
>   PYTHON_VERSION="$(PYTHON_VERSION)"; export PYTHON_VERSION
>   bash "$(CI_BIN)/run_pip_audit.sh"

bandit: prepare-dir ## Run Bandit static code analysis
>   SARIF_DIR="$(SARIF_DIR)"; export SARIF_DIR
>   BANDIT_VERSION="$(BANDIT_VERSION)"; export BANDIT_VERSION
>   GITHUB_WORKSPACE="$(PWD)"; export GITHUB_WORKSPACE
>   PYTHON_VERSION="$(PYTHON_VERSION)"; export PYTHON_VERSION
>   bash "$(CI_BIN)/run_bandit.sh"

gitleaks: prepare-dir ## Run Gitleaks secret scan
>   SARIF_DIR="$(SARIF_DIR)"; export SARIF_DIR
>   GITLEAKS_IMAGE="$(GITLEAKS_IMAGE)"; export GITLEAKS_IMAGE
>   GITLEAKS_IMAGE_TAG="$(GITLEAKS_IMAGE_TAG)"; export GITLEAKS_IMAGE_TAG
>   GITLEAKS_FALLBACK_TAG="$(GITLEAKS_FALLBACK_TAG)"; export GITLEAKS_FALLBACK_TAG
>   bash "$(CI_BIN)/run_gitleaks.sh"

harden: ## Restrict permissions on SARIF files and directories
>   set +e
>   if [ -d "$(SARIF_DIR)" ]; then \
>       find "$(SARIF_DIR)" -type f -name "*.sarif" -exec chmod 600 {} \; 2>/dev/null || true; \
>       find "$(SARIF_DIR)" -type d -exec chmod 700 {} \; 2>/dev/null || true; \
>   fi
>   set -e
>   echo "Artifacts hardened in '$(SARIF_DIR)'."

clean-sarif: ## Remove all SARIF artifacts
>   rm -rf "$(SARIF_DIR)"
>   echo "Removed $(SARIF_DIR)"
