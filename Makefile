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
PYTHON_VERSION         ?= 3.11
SARIF_DIR              ?= sarif-reports
PIP_AUDIT_VERSION      ?= 2.9.0
BANDIT_VERSION         ?= 1.8.6
GITLEAKS_IMAGE         ?= zricethezav/gitleaks
GITLEAKS_IMAGE_TAG     ?= 8.18.2
GITLEAKS_FALLBACK_TAG  ?= latest
TRIVY_VERSION          ?= 0.51.4
TRIVY_SEVERITY         ?= HIGH,CRITICAL
TRIVY_EXIT_CODE        ?= 0
SHELLCHECK_SEVERITY    ?= warning
SHELLCHECK_FAIL_ON     ?= any

# Paths and security defaults
CI_BIN := .ci/bin
UMASK  := 077

# Internal helpers
REQ_TOOLS := bash awk grep docker
SCAN_SCRIPTS := \
    $(CI_BIN)/run_trivy.sh \
    $(CI_BIN)/run_gitleaks.sh \
    $(CI_BIN)/run_pip_audit.sh \
    $(CI_BIN)/run_bandit.sh \
    $(CI_BIN)/run_shellcheck.sh

# Group scanning targets for easy chaining
SCANS := trivy pip-audit bandit shellcheck gitleaks

# ===== Targets =====
.PHONY: help all preflight validate prepare-dir $(SCANS) spellcheck harden clean-sarif print-config

help: ## Show this help
>   @grep -E '^[a-zA-Z0-9._-]+:.*?## ' $(MAKEFILE_LIST) | \
>     awk 'BEGIN {FS = ":.*?## "}; {printf "%-20s %s\n", $$1, $$2}'

print-config: ## Print non-sensitive effective configuration
>   @echo "Config:"
>   @printf "  %-22s = %s\n" PYTHON_VERSION "$(PYTHON_VERSION)"
>   @printf "  %-22s = %s\n" SARIF_DIR "$(SARIF_DIR)"
>   @printf "  %-22s = %s\n" PIP_AUDIT_VERSION "$(PIP_AUDIT_VERSION)"
>   @printf "  %-22s = %s\n" BANDIT_VERSION "$(BANDIT_VERSION)"
>   @printf "  %-22s = %s\n" GITLEAKS_IMAGE "$(GITLEAKS_IMAGE)"
>   @printf "  %-22s = %s\n" GITLEAKS_IMAGE_TAG "$(GITLEAKS_IMAGE_TAG)"
>   @printf "  %-22s = %s\n" GITLEAKS_FALLBACK_TAG "$(GITLEAKS_FALLBACK_TAG)"
>   @printf "  %-22s = %s\n" TRIVY_VERSION "$(TRIVY_VERSION)"
>   @printf "  %-22s = %s\n" TRIVY_SEVERITY "$(TRIVY_SEVERITY)"
>   @printf "  %-22s = %s\n" TRIVY_EXIT_CODE "$(TRIVY_EXIT_CODE)"
>   @printf "  %-22s = %s\n" SHELLCHECK_SEVERITY "$(SHELLCHECK_SEVERITY)"
>   @printf "  %-22s = %s\n" SHELLCHECK_FAIL_ON "$(SHELLCHECK_FAIL_ON)"
>   @printf "  %-22s = %s\n" CI_BIN "$(CI_BIN)"
>   @printf "  %-22s = %s\n" UMASK "$(UMASK)"

prepare-dir: ## Create SARIF dir with secure permissions
>   umask $(UMASK)
>   mkdir -p "$(SARIF_DIR)"
>   chmod 700 "$(SARIF_DIR)" || true

preflight: ## Verify required tools and scripts exist
>   for t in $(REQ_TOOLS); do \
>     command -v $$t >/dev/null 2>&1 || { echo "Error: required tool '$$t' not found"; exit 1; }; \
>   done
>   for s in $(SCAN_SCRIPTS); do \
>     [ -f "$$s" ] || { echo "Error: missing script '$$s'"; exit 1; }; \
>   done
>   $(MAKE) prepare-dir
>   command -v docker >/dev/null 2>&1 || \
>     echo "Note: 'docker' not found. Trivy/Gitleaks will try native binaries if available."

validate: ## Validate required secrets if script is available
>   if [ -x "$(CI_BIN)/common.sh" ]; then \
>       bash "$(CI_BIN)/common.sh" validate_required_secrets; \
>   else \
>       echo "Note: $(CI_BIN)/common.sh not found; skipping secrets validation."; \
>   fi

all: preflight validate $(SCANS) harden ## Run all scans

# ===== Scan Targets =====
shellcheck: prepare-dir ## Run ShellCheck
>   export SARIF_DIR="$(SARIF_DIR)" \
>          SHELLCHECK_SEVERITY="$(SHELLCHECK_SEVERITY)" \
>          SHELLCHECK_FAIL_ON="$(SHELLCHECK_FAIL_ON)"
>   command -v shellcheck >/dev/null 2>&1 || \
>       { sudo apt-get update && sudo apt-get install -y shellcheck; }
>   bash "$(CI_BIN)/run_shellcheck.sh"

trivy: prepare-dir ## Run Trivy filesystem scan
>   export SARIF_DIR="$(SARIF_DIR)"
>   bash "$(CI_BIN)/run_trivy.sh"

pip-audit: prepare-dir ## Run pip-audit
>   export SARIF_DIR="$(SARIF_DIR)"
>   bash "$(CI_BIN)/run_pip_audit.sh"

bandit: prepare-dir ## Run Bandit static code analysis
>   export SARIF_DIR="$(SARIF_DIR)"
>   bash "$(CI_BIN)/run_bandit.sh"

gitleaks: prepare-dir ## Run Gitleaks secret scan
>   export SARIF_DIR="$(SARIF_DIR)"
>   bash "$(CI_BIN)/run_gitleaks.sh"

# ===== Maintenance =====
harden: ## Restrict permissions on SARIF files and directories
>   if [ -d "$(SARIF_DIR)" ]; then \
>       find "$(SARIF_DIR)" -type f -name "*.sarif" -exec chmod 600 {} \; 2>/dev/null || true; \
>       find "$(SARIF_DIR)" -type d -exec chmod 700 {} \; 2>/dev/null || true; \
>   fi
>   echo "Artifacts hardened in '$(SARIF_DIR)'."

clean-sarif: ## Remove all SARIF artifacts
>   rm -rf "$(SARIF_DIR)"
>   echo "Removed $(SARIF_DIR)"
