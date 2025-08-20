# KrakenTrades

**PDF → Excel converter for Kraken trade statements**, built with a clean, testable, security‑first Python stack. It parses Kraken PDF statements, normalizes trades/fees, and exports a polished Excel report suitable for tax prep, PnL review, or audit trails.

---

## Table of contents

* [Why this exists](#why-this-exists)
* [Key features](#key-features)
* [Architecture & Project layout](#architecture--project-layout)
* [Requirements](#requirements)
* [Quick start](#quick-start)
  * [Run with Docker (recommended)](#run-with-docker-recommended)
* [Usage](#usage)
* [Makefile targets](#makefile-targets)
* [Security & AppSec](#security--appsec)
* [CI/CD workflows](#cicd-workflows)

  * [🔐 AppSec — Security, Secrets & Shell Script Scan](#-appsec--security-secrets--shell-script-scan)
  * [🧪 Python Tests & Coverage](#-python-tests--coverage)
  * [Trades Report (scheduled or manual)](#trades-report-scheduled-or-manual)
* [Configuration](#configuration)
* [Troubleshooting](#troubleshooting)
* [Roadmap](#roadmap)
* [License](#license)

---

## Why this exists

* **Automates a painful manual task**: consistent Excel output from exchange PDFs.
* **Production‑minded**: Dockerized, Makefile‑driven, CI‑friendly, with pytest.
* **Maintainable**: modular code under `src/` with typed models, helpers, and a clean Excel writer.

---

## Key features

* 📄 **PDF → Excel**: deterministic, human‑readable spreadsheet (autosized columns, headers, number formats).
* 🧱 **Modular architecture**: parsing, domain models, helpers, and market data separated.
* 🧪 **Tests**: pytest suite with coverage.
* 🐳 **Containerized runtime**: slim Python 3.11 image, non‑root user, writable uploads volume.
* 🔐 **Security‑first**: AppSec scans (Trivy, Gitleaks, pip‑audit, ShellCheck, Bandit) wired via Makefile and CI.

---

## Architecture & Project layout

```
trades/
├── Dockerfile
├── Makefile
├── README.md
├── docker-compose.yml
├── main.py
├── requirements.txt
├── setup.cfg
├── tests/
│   ├── test_generate_excel_file.py
│   └── assertions/
│       └── file_generation.py
├── src/
│   ├── market/
│   │   └── market_data.py
│   ├── file_management/
│   │   ├── excel_styler.py
│   │   ├── excel_writer.py
│   │   └── pdf_parser.py
│   ├── kraken_core/
│   │   ├── constants.py
│   │   ├── custom_logger.py
│   │   ├── enums.py
│   │   └── models.py
│   └── helpers/
│       └── file_helper.py
└── scripts/
    ├── get_trades_pdf.py
    └── scan_repo.py
```

---

## Requirements

* **Python**: 3.11+
* **Docker**: 24+ (recommended) / `docker compose` plugin
* **Make**: GNU Make 4+

---

## Quick start

### Run with Docker (recommended)

The container uses a non‑root user by default (`UID=10001`, `GID=10001`) and writes outputs to `/app/uploads`.

```bash
# 1) Build the image
make docker-build            # equivalent to: docker build -t krakentrades:latest .

# 2) Prepare a local uploads folder (host side)
mkdir -p ./uploads

# 3) Place your Kraken PDF as ./uploads/trades.pdf (or use the script below)

# 4) Run the converter (mount uploads and point the app to it)
make docker-run              # equivalent to the below manual run
# Manual run (if you prefer):
# docker run --rm \
#   -v "$(pwd)/uploads:/app/uploads:rw" \
#   -e UPLOAD_DIR=/app/uploads \
#   krakentrades:latest
```

Optional: download `trades.pdf` from Google Drive using a service account JSON in `GOOGLE_DRIVE_JSON_KEY`:

What you get:

* A single Excel workbook with standardized sheets (e.g. trades, fees, summary where applicable).
* Clean headers and number formatting suitable for review or downstream tooling.

**Paths & filenames used by CI and Docker**

* Uploads directory (inside container): `/app/uploads` (configurable via `UPLOAD_DIR` env)
* Default report filename used by CI: `kraken_trade_summary.xlsx`

---

## Makefile targets

> The CI defers to the Makefile for *all* developer flows and scans.

Common targets (as used by CI):

* `make install-deps` – install Python dependencies from `requirements.txt`.
* `make test` – run the pytest suite with coverage (emits `coverage.xml`).
* `make docker-build` – build the Docker image (tag: `krakentrades:latest`).
* `make docker-run` – run the converter container mounting `./uploads` → `/app/uploads`.
* `make appsec` – run the AppSec bundle (Trivy, Gitleaks, pip‑audit, ShellCheck, Bandit) and write SARIF into `sarif-reports/`.

> Exact implementation lives in `Makefile`. CI workflows call these targets so they remain the single source of truth.

---

## Security & AppSec

* **Slim runtime**: multi‑stage build (builder + runtime) on `python:3.11-slim`.
* **Non‑root user**: `appuser` (`UID=10001`, `GID=10001`), `/app/uploads` writable only where needed.
* **No secrets in logs**: CI gates uploads; artifacts hardened with restrictive permissions.
* **Scans** (via `make appsec`):

  * Container & deps: Trivy
  * Secrets: Gitleaks
  * Python deps: pip‑audit (generates SARIF)
  * Shell scripts: ShellCheck
  * Python security lint: Bandit
* **SARIF** written to `sarif-reports/` and uploaded to the GitHub Security tab when allowed (see CI rules below).

---

## CI/CD workflows

### 🔐 AppSec — Security, Secrets & Shell Script Scan

* **Triggers**: `pull_request` touching shell scripts, `.ci/bin/**`, or `Makefile`; manual `workflow_dispatch`.
* **Permissions**: minimal – `contents: read`, `security-events: write`.
* **Flow**: checkout → setup Python → install minimal OS deps → `make appsec` → harden SARIF permissions → upload SARIF bundle as artifact.
* **Upload to Security tab**: separate `sarif-upload` job iterates expected files (`trivy.sarif`, `gitleaks.sarif`, `pip-audit.sarif`, `shellcheck.sarif`, `bandit.sarif`) and uploads those that exist.

### 🧪 Python Tests & Coverage

* **Triggers**: PRs to any branch, pushes to `main`, and manual.
* **Flow**: checkout → setup Python 3.11 (pip cache on) → `make install-deps` → create `uploads/` → (optional) download `trades.pdf` via `scripts/get_trades_pdf.py` using `GOOGLE_DRIVE_JSON_KEY` → `make test` → upload `coverage.xml` artifact.

### Trades Report (scheduled or manual)

* **Triggers**: manual `workflow_dispatch` or daily schedule `0 6 * * *` (06:00 UTC).
* **Flow**: checkout → setup Python → install `pydrive2` → prepare and chown `uploads/` → download `trades.pdf` (requires `GOOGLE_DRIVE_JSON_KEY`) → build Docker image with Buildx → validate email secrets → run container to generate report → upload artifact → email the report.
* **Env defaults**:

  * `UPLOAD_DIR=uploads` (host) ↔ `UPLOAD_DIR_PATH=/app/uploads` (container)
  * `REPORT_FILE=kraken_trade_summary.xlsx`
  * `DOCKER_IMAGE=krakentrades:latest`
  * SMTP: `smtp.gmail.com:465`, subject/body templated in env

---

## Configuration

Environment variables consumed by the app and CI:

* `UPLOAD_DIR` (runtime): path to the writable uploads directory (default inside container: `/app/uploads`).
* `GOOGLE_DRIVE_JSON_KEY` (CI/optional local): JSON for a Google service account used by `scripts/get_trades_pdf.py` to fetch `trades.pdf`.
* **Emailing (CI)**: `EMAIL_USER`, `EMAIL_PASS`, `REPORT_RECIPIENT` (validated before sending).

Build/runtime details (from `Dockerfile`):

* Multi‑stage build: builder installs deps from `requirements.txt`; runtime copies site‑packages and binaries only.
* Non‑root user `appuser` (`UID/GID=10001`) and owned `/app/uploads`.
* Entrypoint: `CMD ["python", "main.py"]`.

---

## Troubleshooting

* **Permissions on uploads**: ensure the host `./uploads` is writable by the container’s UID/GID or mount with `:rw`. CI explicitly `chown`s to `10001:10001`.
* **Missing `trades.pdf`**: place it in `./uploads` or set `GOOGLE_DRIVE_JSON_KEY` and run `python scripts/get_trades_pdf.py`.
* **SARIF not visible**: uploads to the Security tab are gated to pushes or same‑repo PRs. Fork PRs will still produce artifacts but won’t upload to Security.
* **Email step fails**: verify secrets `EMAIL_USER`, `EMAIL_PASS`, `REPORT_RECIPIENT` are set.

---

## Roadmap

* Configurable currency/locale handling.
* Richer PnL/fees summaries (separate sheet).
* Optional C
