# File: .ci/bin/bandit_to_sarif.py
from __future__ import annotations
import json, os
from typing import Any, Dict, List

JSON_ENV = "BANDIT_JSON_PATH"
OUT_DIR_ENV = "SARIF_DIR"
VER_ENV = "BANDIT_VERSION"
WORKSPACE_ENV = "GITHUB_WORKSPACE"

json_path = os.environ.get(JSON_ENV, "")
out_dir = os.environ.get(OUT_DIR_ENV, "sarif-reports")
out_file = os.path.join(os.getcwd(), out_dir, "bandit.sarif")
bandit_ver = os.environ.get(VER_ENV, "unknown")
repo_root = os.environ.get(WORKSPACE_ENV, os.getcwd()).replace("\\", "/")


def norm_repo_rel(p: str) -> str:
    p = (p or "").replace("\\", "/")
    while p.startswith("./"):
        p = p[2:]
    if os.path.isabs(p):
        try:
            rel = os.path.relpath(p, repo_root).replace("\\", "/")
            return rel
        except Exception:
            return os.path.basename(p)
    if p.startswith(repo_root.rstrip("/") + "/"):
        return p[len(repo_root.rstrip("/")) + 1 :]
    return p


try:
    with open(json_path, "r", encoding="utf-8") as fh:
        data: Dict[str, Any] = json.load(fh)
except Exception:
    data = {}

results: List[Dict[str, Any]] = data.get("results") or []
rules: Dict[str, Dict[str, Any]] = {}
for r in results:
    tid = (r.get("test_id") or "BANDIT").strip()
    name = r.get("test_name") or tid
    if tid not in rules:
        rules[tid] = {
            "id": tid,
            "name": name,
            "shortDescription": {"text": name},
            "helpUri": r.get("more_info") or "",
            "defaultConfiguration": {"level": "warning"},
        }


def sev_level(s: str | None) -> str:
    m = (s or "").lower()
    if m == "high":
        return "error"
    if m == "medium":
        return "warning"
    return "note"


sarif_results: List[Dict[str, Any]] = []
for r in results:
    uri = norm_repo_rel(r.get("filename") or "")
    start_line = r.get("line_number") or 1
    sarif_results.append(
        {
            "ruleId": (r.get("test_id") or "BANDIT"),
            "level": sev_level(r.get("issue_severity")),
            "message": {"text": r.get("issue_text") or "Bandit issue"},
            "locations": [
                {
                    "physicalLocation": {
                        "artifactLocation": {"uri": uri},
                        "region": {"startLine": max(1, int(start_line))},
                    }
                }
            ],
            "properties": {
                "tags": ["bandit", (r.get("test_name") or "").strip()],
                "severity": (r.get("issue_severity") or "").upper(),
                "confidence": (r.get("issue_confidence") or "").upper(),
                "cwe": (r.get("issue_cwe") or {}).get("id")
                if isinstance(r.get("issue_cwe"), dict)
                else None,
            },
        }
    )

out = {
    "version": "2.1.0",
    "runs": [
        {
            "tool": {
                "driver": {
                    "name": "bandit",
                    "version": bandit_ver,
                    "informationUri": "https://bandit.readthedocs.io/",
                    "rules": list(rules.values()),
                }
            },
            "results": sarif_results,
        }
    ],
}

os.makedirs(out_dir, exist_ok=True)
with open(out_file, "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=2)
