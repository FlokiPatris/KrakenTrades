# 🐙 KrakenTrades

**KrakenTrades** is a Python tool for **parsing and analyzing trade reports from the Kraken exchange** (PDF → Excel).  
The repository also features a **fully integrated CI/CD security pipeline** that **automatically scans code, dependencies, and containers**, publishing results directly into the **GitHub Security tab**.

---

## ✨ Key Features
- 📄 **Parse PDF trade statements** from Kraken and convert them into clean, structured **Excel reports**.  
- 🎨 Automated Excel styling for readability.  
- 🧩 Modular architecture (data classes, enums, centralized config).  
- 🐳 **Docker & docker-compose** support for easy setup and deployment.  
- 🔒 **Security-first pipeline**:
  - [Bandit](https://bandit.readthedocs.io/) – Python security linter  
  - [Trivy](https://aquasecurity.github.io/trivy/) – container & dependency scanning  
  - [Gitleaks](https://github.com/gitleaks/gitleaks) – secret detection  
  - [pip-audit](https://github.com/pypa/pip-audit) – Python dependency vulnerability scanning  
  - [ShellCheck](https://www.shellcheck.net/) – shell script static analysis  
- 📊 Results automatically published into **GitHub Security tab** (via SARIF reports).  

---

## 🚀 Quick Start

### 1️⃣ Clone the repository
```bash
git clone git@github.com:FlokiPatris/KrakenTrades.git
cd KrakenTrades
```

### 2️⃣ Run via Docker
```bash
docker-compose up --build
```

### 3️⃣ Or run locally
```bash
pip install -r requirements.txt
python main.py
```

---

## 🛡️ CI/CD & Security
This repo includes a **GitHub Actions workflow** that runs on every push:  
- Executes multiple **security scanning tools**.  
- Reports are uploaded into the **Security tab** in GitHub.  
- Provides developers with immediate visibility into vulnerabilities and code health.  

---

## 📂 Project Structure
```
KrakenTrades/
 ├── main.py                 # Application entry point
 ├── file_management/        # PDF parsing & Excel handling
 ├── kraken_core/            # Core logic, data classes, logger
 ├── market/                 # Market data & manual overrides
 ├── config/                 # Configuration
 ├── .ci/                    # Security scanning scripts
 └── .github/workflows/      # GitHub Actions pipelines
```

---

## 📜 License
MIT License – free to use, modify, and share.  
