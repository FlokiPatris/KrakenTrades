#!/usr/bin/env python3
"""
Purpose: Convert Bandit JSON output to GitHub SARIF with path normalization,
         preserving severity and rule metadata so results appear in the
         Security tab. Safe defaults: writes an empty SARIF if input is missing.

Environment:
  - BANDIT_JSON_PATH: path to Bandit JSON (required)
  - SARIF_DIR: output directory for SARIF (default: sarif-reports)
  - BANDIT_VERSION: bandit version string for metadata (default: "unknown")
  - GITHUB_WORKSPACE: repo root for path normalization (default: CWD)
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List

JSON_ENV = "BANDIT_JSON_PATH"
OUT_DIR_ENV = "SARIF_DIR"
VER_ENV = "BANDIT_VERSION"
WORKSPACE_ENV = "GITHUB_WORKSPACE"


def _norm_repo_rel(path: str, repo_root: str) -> str:
    """
    Normalize a file path to a repository-relative, forward-slash URI
    so GitHub can match SARIF results to the correct files.
    """
    p = (path or "").replace("\\", "/")
    while p.startswith("./"):
        p = p[2:]
    # If absolute, try to relativize to repo_root
    if os.path.isabs(p):
        try:
            rel = os.path.relpath(p, repo_root).replace("\\", "/")
            return rel
        except Exception:
            return os.path.basename(p)
    # If already prefixed by repo_root, strip it
    prefix = repo_root.rstrip("/") + "/"
    if p.startswith(prefix):
        return p[len(prefix) :]
    return p


def _sev_level(sev: str | None) -> str:
    """
    Map Bandit severities to SARIF levels.
    - high   -> error
    - medium -> warning
    - else   -> note
    """
    m = (sev or "").lower()
    if m == "high":
        return "error"
    if m == "medium":
        return "warning"
    return "note"


def main() -> int:
    json_path = os.environ.get(JSON_ENV, "")
    out_dir = os.environ.get(OUT_DIR_ENV, "sarif-reports")
    out_file = os.path.join(os.getcwd(), out_dir, "bandit.sarif")
    bandit_ver = os.environ.get(VER_ENV, "unknown")
    repo_root = os.environ.get(WORKSPACE_ENV, os.getcwd()).replace("\\", "/")

    # Load Bandit JSON (tolerant)
    try:
        with open(json_path, "r", encoding="utf-8") as fh:
            data: Dict[str, Any] = json.load(fh)
    except Exception:
        data = {}

    results: List[Dict[str, Any]] = data.get("results") or []
    rules: Dict[str, Dict[str, Any]] = {}

    # Build rule metadata from results so UI can link and group correctly
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

    sarif_results: List[Dict[str, Any]] = []
    for r in results:
        uri = _norm_repo_rel(r.get("filename") or "", repo_root)
        start_line = r.get("line_number") or 1
        sarif_results.append(
            {
                "ruleId": (r.get("test_id") or "BANDIT"),
                "level": _sev_level(r.get("issue_severity")),
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
                    "cwe": (r.get("issue_cwe") or {}).get("id"),
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
    # Harden on POSIX runners; ignore on platforms that don't support chmod
    try:
        os.chmod(out_file, 0o600)
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
