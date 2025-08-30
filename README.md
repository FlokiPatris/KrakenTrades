# KrakenTrades — Kraken PDF → Styled Excel Pipeline

**Quick links**
- [What is this?](#what-is-this)
- [For recruiters (summary)](#for-recruiters-summary)
- [Github](#github)
- [Example Excel PNGs](#examples)
- [CI & Security](#ci--security)
- [Run locally (detailed)](#run-locally-detailed)
- [Run with Docker / Compose](#run-with-docker--compose)
- [Repository layout](#repository-layout)
- [Environment variables / .env](#environment-variables--env)
- [How it works (high level)](#how-it-works-high-level)
- [License & contact](#license--contact)

# What is this?
KrakenTrades is a pipeline that ingests Kraken trade statement PDFs, parses trade records, builds Pandas DataFrames and writes a styled Excel report suitable for downstream analysis or archival. It is designed to be CI/CD friendly, secure by default (SARIF, secret scanning, hardened file permissions) and production-oriented (Docker, DB integration).

# For recruiters (summary)
- Purpose: Convert Kraken PDF trade statements into a clean, styled Excel summary with additional data analysis.
- Languages / tech: Python 3.11+, Pandas, pdfplumber, openpyxl; Docker; GitHub Actions for CI.
- Production features: tests (pytest), Docker image + compose, appsec scans (Bandit, ShellCheck, pip-audit, gitleaks, Trivy), SARIF conversion for security tooling.
- What to look for: `main.py` (pipeline entry), `src/file_management` (parsers, writers, stylers), `tests/` (e2e + integration).

# Run locally (detailed)
## Prepare repo
- Clone the repo and change into it.
    git clone https://github.com/FlokiPatris/KrakenTrades.git
    cd KrakenTrades

- Create and activate a virtual environment (recommended).

## Install deps
    make install-deps
    
## Run the script
- Ensure the input PDF exists at `KRAKEN_TRADES_PDF` (default: `downloads/trades.pdf`).
    python main.py
- Check `uploads/` for `kraken_trade_summary.xlsx` (or the value in `PARSED_TRADES_EXCEL`).

# Run with Docker & Compose
- Build image:
    make docker-build

- Run image (one-off):
    make docker-run

- Or use Compose:
    make up

- Tear down:
    make down

Notes:
- `Makefile` wraps common tasks (tests, scans, build, run).
- `docker-compose.yml` contains container service definitions for convenience (see file for exact behavior).

# CI & Security
This repository includes GitHub Actions workflows:
- `/.github/workflows/run-tests.yml` — runs tests and coverage.
- `/.github/workflows/trade-report.yml` — scheduled / on-demand report generation (CI container).
- `/.github/workflows/enhanced-security-scan.yml` — runs Bandit, pip-audit, ShellCheck, gitleaks, Trivy.

Security tooling is invoked via Makefile targets:
    make appsec # run full security suite
    make bandit
    make pip-audit
    make shellcheck
    make gitleaks
    make trivy

SARIF conversion helper: `.ci/bin/sarif_convert.py` — converts tool outputs (Bandit, pip-audit, ShellCheck) into SARIF 2.1.0 and writes files with restrictive permissions (0o600). CI uploads SARIF artifacts only when configured to do so (see `UPLOAD_SARIF` gating in workflows).

# Repository layout
- `main.py` — pipeline entry point.
- `requirements.txt` — Python dependencies.
- `Makefile` — common tasks (install, test, appsec, docker).
- `docker-compose.yml` — compose definitions.
- `src/`
  - `file_management/` — pdf parser, dataframe builder, excel writer & styler.
  - `kraken_core/` — constants, config dataclasses, logger, enums, models.
  - `kraken_db/` — DB connector & migrations (Postgres helper).
  - `helpers/` — utilities (file helper, etc.).
  - `market/` — market price helpers.
- `scripts/` — convenience scripts (GDrive download, DB import, repo scan).
- `.ci/` — CI helpers & SARIF conversions.
- `.github/workflows/` — GitHub Actions workflows.
- `tests/` — pytest tests: smoke, integration, e2e.
- `uploads/` and `downloads/` — runtime folders (configured via PathsConfig).

# Environment variables / .env (recommended)
Below is a compact list of env variables the code refers to (set them in `.env` locally and as GitHub Secrets in CI):

- `UPLOADS_DIR` — default `uploads`
- `DOWNLOADS_DIR` — default `downloads`
- `KRAKEN_TRADES_PDF` — path to PDF input (default `downloads/trades.pdf`)
- `PARSED_TRADES_EXCEL` — path to generated Excel (default `uploads/kraken_trade_summary.xlsx`)
- `REPORTS_DIR`
- `REPO_ROOT`

Database (optional):
- `RDS_HOST`, `RDS_DB_NAME`, `RDS_USER`, `RDS_PASSWORD`, `RDS_PORT`

CI / GDrive / Notifications:
- `GOOGLE_DRIVE_JSON_KEY` — service account JSON for Drive integration (store as secret)
- `UPLOAD_SARIF` — gating flag whether CI should upload SARIF artifacts
- `SMTP_SERVER`, `SMTP_PORT`, `EMAIL_USER`, `EMAIL_PASS`, `REPORT_FILE` — if email reporting is used in workflows

Security note: never commit secrets. Use GitHub Actions Secrets and `.gitignore` the `.env` file.

# How it works (high level)
1. `main.py` orchestrates the pipeline:
   - Read PDF from `KRAKEN_TRADES_PDF`
   - Extract trade records using `pdfplumber` and regex rules in `src/kraken_core`
   - Normalize into a Pandas DataFrame
   - Compute summary metrics and snapshots
   - Write a styled Excel workbook with multiple sheets (portfolio, ROI, per-token breakdown)
   - Optionally insert results into a Postgres DB or upload to Google Drive via scripts

2. Tests validate both file generation and DB queries (see `tests/`).

3. AppSec pipeline (Makefile + `.ci`) runs static checks and converts results to SARIF for consistent reporting.

# License & contact
- Author / Contact:
  - Floki Patris


# Github:
All running PR pipelines:
<img width="1892" height="235" alt="image" src="https://github.com/user-attachments/assets/1b7fda01-5f60-438b-a4be-cbf86759fd85" />

Expanded PR checks:
<img width="1908" height="899" alt="image" src="https://github.com/user-attachments/assets/0f1bbce4-38ba-45fb-890e-476094d24c7f" />

Leak found (Security pipeline in action):
<img width="924" height="449" alt="image" src="https://github.com/user-attachments/assets/9f26d18a-fb6a-4707-bad0-b65a04b49fbe" />


# Excel File Example:
1. Portfolio sheet (First Excel sheet)
<img width="1536" height="1024" alt="blur the prices for readme" src="https://github.com/user-attachments/assets/bd057760-bda0-44e0-a9aa-1f84fa4e5d28" />

2. Asset ROI sheet (Second Excel sheet)
<img width="1054" height="383" alt="asset roi sheet" src="https://github.com/user-attachments/assets/4cbf0fca-5d00-4f4f-a0c5-1be864c8e09d" />

3. BTC/EUR Sheet (One of the trade pair sheets)
<img width="1065" height="328" alt="bitcoin sheet" src="https://github.com/user-attachments/assets/df35b3a8-8013-454e-912c-6c36ec4a227a" />
---

