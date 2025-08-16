# ==========================================================
# KrakenTrades - Unified Makefile
# ==========================================================
# Goals:
# - Single entrypoint for both local dev and CI (predictable behavior).
# - Wrap all existing .ci/bin/*.sh scripts → DRY principle, no workflow duplication.
# - Avoid "magic constants": configure paths/flags via variables at the top.
# - Security-first defaults: fail fast, strict error handling, consistent dirs.
# - CI/CD & Docker friendly: same commands run everywhere.
#
# Usage (examples):
#   make help             # show all available targets
#   make appsec           # run full security suite
#   make test             # run tests with coverage
#   make docker-build     # build Docker image
#
# Best practice:
# - Add new scanners or tools here (not directly into CI YAML).
# - Never hardcode credentials; rely on environment variables.
# ==========================================================

# ----- Configurable variables -----
BIN_DIR ?= .ci/bin
SARIF_DIR ?= sarif-reports
PYTHON ?= python3
PIP ?= pip3
DOCKER_IMAGE ?= krakentrades:ci
COMPOSE_FILE ?= docker-compose.yml

# ----- Strict shell mode -----
SHELL := /bin/bash
.SHELLFLAGS := -Eeuo pipefail -c
# -E: inherit ERR traps, -e: exit on error, -u: undefined vars = error
# -o pipefail: fail if any pipe stage fails

# ----- Colors (for pretty CLI output) -----
BLUE := \033[1;34m
GREEN := \033[0;32m
GRAY := \033[0;37m
NC := \033[0m

.DEFAULT_GOAL := help

# ----- Declare phony targets -----
.PHONY: help ensure-dirs local-all appsec \
        shellcheck bandit pip-audit gitleaks trivy hadolint \
        fmt lint test pre-commit \
        docker-build docker-run up down clean

# ==========================================================
# Helpers
# ==========================================================
help:
	@printf "\n$(GREEN)Available targets$(NC)\n"
	@printf "  $(BLUE)appsec$(NC)        Run all security scans (shellcheck, bandit, pip-audit, gitleaks, trivy)\n"
	@printf "  $(BLUE)shellcheck$(NC)    Run ShellCheck + SARIF conversion\n"
	@printf "  $(BLUE)bandit$(NC)        Run Bandit + SARIF conversion\n"
	@printf "  $(BLUE)pip-audit$(NC)     Run pip-audit + SARIF conversion\n"
	@printf "  $(BLUE)gitleaks$(NC)      Run gitleaks + SARIF conversion\n"
	@printf "  $(BLUE)trivy$(NC)         Run Trivy container scan + SARIF conversion\n"
	@printf "  $(BLUE)hadolint$(NC)      Lint Dockerfile\n"
	@printf "  $(BLUE)test$(NC)          Run pytest with coverage\n"
	@printf "  $(BLUE)fmt$(NC)           Format code (black + isort)\n"
	@printf "  $(BLUE)lint$(NC)          Lint code (flake8 + mypy)\n"
	@printf "  $(BLUE)pre-commit$(NC)    Install & run pre-commit hooks\n"
	@printf "  $(BLUE)docker-build$(NC)  Build Docker image ($(DOCKER_IMAGE))\n"
	@printf "  $(BLUE)docker-run$(NC)    Run Docker image (ephemeral)\n"
	@printf "  $(BLUE)up$(NC)            docker compose up (detached)\n"
	@printf "  $(BLUE)down$(NC)          docker compose down (cleanup)\n"
	@printf "  $(BLUE)clean$(NC)         Remove caches, build, and $(SARIF_DIR)\n\n"

ensure-dirs:
	@mkdir -p "$(SARIF_DIR)"

# ==========================================================
# Local full pipeline (developer convenience)
# ==========================================================
local-all: ensure-dirs
	# Run security + quality stack locally in one shot
	SARIF_OUT_DIR="$(PWD)/$(SARIF_DIR)" \
	GITHUB_ENV=/dev/null \
	$(MAKE) shellcheck || true
	python -m bandit -r . -f json -o "$(SARIF_DIR)/bandit.json" || true
	$(MAKE) pip-audit || true
	gitleaks detect --source . --report-format sarif --report-path "$(SARIF_DIR)/gitleaks.sarif" || true
	$(MAKE) trivy || true
	$(MAKE) hadolint || true
	$(MAKE) test || true
	$(MAKE) fmt || true
	$(MAKE) lint || true

# ==========================================================
# Security meta-targets
# ==========================================================
appsec: ensure-dirs shellcheck bandit pip-audit gitleaks trivy
	@echo "✔ All AppSec scans completed."

# ---- Security scanners (delegated to scripts in .ci/bin) ----
shellcheck: ensure-dirs
	@"$(BIN_DIR)/run_shellcheck.sh"

bandit: ensure-dirs
	@"$(BIN_DIR)/run_bandit.sh"

pip-audit: ensure-dirs
	@"$(BIN_DIR)/run_pip_audit.sh"

gitleaks: ensure-dirs
	@"$(BIN_DIR)/run_gitleaks.sh"

trivy: ensure-dirs
	@"$(BIN_DIR)/run_trivy.sh"

# ---- Optional Dockerfile linter ----
hadolint:
	@echo "→ hadolint Dockerfile"
	@curl -sSL https://github.com/hadolint/hadolint/releases/latest/download/hadolint-Linux-x86_64 -o hadolint
	@chmod +x hadolint
	@./hadolint Dockerfile || true
	@rm -f hadolint
	@echo "✔ hadolint completed."

# ==========================================================
# Quality & testing
# ==========================================================
fmt:
	@echo "→ format (black + isort)"
	@$(PIP) install -q black isort
	@$(PYTHON) -m black .
	@$(PYTHON) -m isort .

lint:
	@echo "→ lint (flake8 + mypy)"
	@$(PIP) install -q flake8 mypy
	@$(PYTHON) -m flake8 .
	@$(PYTHON) -m mypy --ignore-missing-imports .

test:
	@echo "→ test (pytest + coverage)"
	@$(PIP) install -q pytest pytest-cov
	@$(PYTHON) -m pytest -q --cov=. --cov-report=term-missing

pre-commit:
	@echo "→ pre-commit install & run"
	@$(PIP) install -q pre-commit
	@pre-commit install
	@pre-commit run --all-files || true

# ==========================================================
# Docker/Compose helpers
# ==========================================================
docker-build:
	@echo "→ docker build $(DOCKER_IMAGE)"
	@docker build -t "$(DOCKER_IMAGE)" .

docker-run:
	@echo "→ docker run $(DOCKER_IMAGE)"
	@docker run --rm "$(DOCKER_IMAGE)"

up:
	@echo "→ docker compose up"
	@docker compose -f "$(COMPOSE_FILE)" up -d --build

down:
	@echo "→ docker compose down"
	@docker compose -f "$(COMPOSE_FILE)" down --remove-orphans

# ==========================================================
# Cleanup
# ==========================================================
clean:
	@echo "→ clean build/cache/SARIF artifacts"
	@rm -rf .pytest_cache .mypy_cache .ruff_cache .venv build dist "$(SARIF_DIR)"
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@echo "✔ clean complete."
