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
* [AI Prompting & Metadata for Scanning](#ai-prompting--metadata-for-scanning)
* [Troubleshooting](#troubleshooting)
* [Roadmap](#roadmap)
* [License](#license)

---

## Why this exists

* **Automates a painful manual task**: consistent Excel output from exchange PDFs.
* **Production‑minded**: Dockerized, Makefile‑driven, CI-friendly, with pytest.
* **Maintainable**: modular code under src/ with typed models, helpers, and a clean Excel writer.
* **AI-ready**: includes metadata, env vars, and structured layout to facilitate automated prompts, security audits, and workflow generation.

---

## Key features

* 📄 **PDF → Excel**: deterministic, human‑readable spreadsheet (autosized columns, headers, number formats).
* 🧱 **Modular architecture**: parsing, domain models, helpers, and market data separated.
* 🧪 **Tests**: pytest suite with coverage.
* 🐳 **Containerized runtime**: slim Python 3.11 image, non‑root user, writable uploads volume.
* 🔐 **Security‑first**: AppSec scans (Trivy, Gitleaks, pip‑audit, ShellCheck, Bandit) wired via Makefile and CI.
* 🤖 **AI-enhanced metadata**: structured README, clear environment variables, and file layout to allow AI to generate prompts and code snippets reliably.

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
│   └── assertions/file_generation.py
├── src/
│   ├── market/market_data.py
│   ├── file_management/
│   │   ├── excel_styler.py
│   │   ├── excel_writer.py
│   │   └── pdf_parser.py
│   ├── kraken_core/
│   │   ├── constants.py
│   │   ├── custom_logger.py
│   │   ├── enums.py
│   │   └── models.py
│   └── helpers/file_helper.py
└── scripts/
    ├── get_trades_pdf.py
    └── scan_repo.py
```

---

## Requirements

* **Python**: 3.11+
* **Docker**: 24+ (recommended) / docker compose plugin
* **Make**: GNU Make 4+

---

## Quick start

### Run with Docker (recommended)

The container uses a non‑root user by default (UID=10001, GID=10001) and writes outputs to /app/uploads.

```bash
# 1) Build the image
make docker-build

# 2) Prepare a local uploads folder (host side)
mkdir -p ./uploads

# 3) Place your Kraken PDF as ./uploads/trades.pdf (or use the script below)

# 4) Run the converter (mount uploads and point the app to it)
make docker-run
```

Optional: download trades.pdf from Google Drive using a service account JSON in GOOGLE\_DRIVE\_JSON\_KEY.

**Paths & filenames used by CI and Docker**

* Uploads directory (inside container): /app/uploads (configurable via UPLOAD\_DIR env)
* Default report filename used by CI: kraken\_trade\_summary.xlsx

---

## Makefile targets

> The CI defers to the Makefile for *all* developer flows and scans. Common targets (as used by CI):

* `make install-deps` – install Python dependencies from requirements.txt.
* `make test` – run the pytest suite with coverage (emits coverage.xml).
* `make docker-build` – build the Docker image (tag: krakentrades\:latest).
* `make docker-run` – run the converter container mounting ./uploads → /app/uploads.
* `make appsec` – run the AppSec bundle (Trivy, Gitleaks, pip‑audit, ShellCheck, Bandit) and write SARIF into sarif-reports/.

> Exact implementation lives in Makefile. CI workflows call these targets so they remain the single source of truth.

---

## Security & AppSec

* **Slim runtime**: multi‑stage build (builder + runtime) on python:3.11-slim.
* **Non‑root user**: appuser (UID=10001, GID=10001), /app/uploads writable only where needed.
* **No secrets in logs**: CI gates uploads; artifacts hardened with restrictive permissions.
* **Scans** (via make appsec): Trivy, Gitleaks, pip‑audit, ShellCheck, Bandit.
* **SARIF** written to sarif-reports/ and uploaded to the GitHub Security tab when allowed.

---

## CI/CD workflows

### 🔐 AppSec — Security, Secrets & Shell Script Scan

* **Triggers**: PRs touching shell scripts, .ci/bin/\*\*, or Makefile; manual workflow\_dispatch.
* **Flow**: checkout → setup Python → install minimal OS deps → make appsec → harden SARIF permissions → upload SARIF bundle as artifact.

### 🧪 Python Tests & Coverage

* **Triggers**: PRs, pushes to main, manual.
* **Flow**: checkout → setup Python 3.11 → make install-deps → create uploads/ → optional download trades.pdf → make test → upload coverage.xml.

### Trades Report (scheduled or manual)

* **Triggers**: manual workflow\_dispatch or daily schedule.
* **Flow**: checkout → setup Python → install pydrive2 → prepare uploads/ → download trades.pdf → build Docker image → validate secrets → run container → upload artifact → email report.
* **Env defaults**: UPLOAD\_DIR, REPORT\_FILE, DOCKER\_IMAGE, SMTP.

---

## Configuration

* UPLOAD\_DIR (runtime)
* GOOGLE\_DRIVE\_JSON\_KEY (optional)
* EMAIL\_USER, EMAIL\_PASS, REPORT\_RECIPIENT (CI email step)
* Multi-stage build: builder copies site-packages and binaries only.
* Non-root user (UID/GID=10001), CMD: \["python", "main.py"]

---

## Troubleshooting

* Permissions on uploads: ensure host ./uploads is writable by UID/GID 10001.
* Missing trades.pdf: place in ./uploads or use GOOGLE\_DRIVE\_JSON\_KEY.
* SARIF not visible: gated to pushes or same-repo PRs.
* Email step fails: verify EMAIL\_USER, EMAIL\_PASS, REPORT\_RECIPIENT.

---

## Roadmap

* Configurable currency/locale handling.
* Richer PnL/fees summaries (separate sheet).
* Optional features for additional exchanges.

---

## AI Prompting & Metadata for Scanning

* Clear folder structure: src/, tests/, scripts/.
* Typed Python models for AI understanding of data flow.
* Environment variables documented and enforced.
* Security scans wired in Makefile and CI, producing SARIF.
* README includes metadata tags and structured sections for AI to generate prompts, test cases, or refactor suggestions.
* Use this section to automatically generate prompts like:

  * "Create new parser for another exchange with same output format."
  * "Add new test for XLSX summary formatting."
  * "Audit Dockerfile for additional CVEs or hardening."
    
---

## Notes for AI-enhanced repo scans

* README now fully structured with headings, links, and metadata.
* Environment variables, file layout, and Makefile targets explicitly listed.
* Scans & security prompts added for CVE checks, secrets audit, Docker hardening.
* Future AI prompts can safely generate tests, new features, and CI/CD adjustments without guessing context.

---

## License

* See LICENSE file or placeholder.
