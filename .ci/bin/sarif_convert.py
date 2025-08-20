#!/usr/bin/env python3
"""
sarif_convert.py — Unified converters to SARIF 2.1.0 for Bandit, pip-audit, ShellCheck.

Usage:
  python .ci/bin/sarif_convert.py <bandit|pip-audit|shellcheck> --in <in.json> --out <out.sarif> [--base-uri <repo>]

Design:
- Tool-specific parsers -> normalized (rules, results).
- Shared SARIF builders.
- No external dependencies (stdlib only).
- Writes SARIF with file mode 0o600.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Dict, List, Optional, Tuple

# -------------------------------
# Constants
# -------------------------------
SARIF_VERSION = "2.1.0"
SARIF_SCHEMA = (
    "https://schemastore.azurewebsites.net/schemas/json/sarif-2.1.0-rtm.5.json"
)


# -------------------------------
# Utility functions
# -------------------------------
def _rel_uri(path: str, base: Optional[str] = None) -> str:
    """Return relative URI of path from base directory."""
    if not path:
        return ""
    try:
        if base and os.path.isabs(path):
            return os.path.relpath(path, base)
        return path
    except Exception:
        return path


def _level_from_severity(sev: str) -> str:
    """Map tool severity to SARIF level."""
    s = (sev or "").lower()
    if s in {"critical", "high", "error", "fatal"}:
        return "error"
    if s in {"medium", "moderate", "warning", "warn"}:
        return "warning"
    return "note"


def _make_rule(rule_id: str, name: str, help_uri: str = "") -> Dict[str, Any]:
    """Construct a SARIF rule object."""
    return {
        "id": rule_id,
        "name": name or rule_id,
        "shortDescription": {"text": name or rule_id},
        "helpUri": help_uri,
        "defaultConfiguration": {"level": "warning"},
    }


def _sarif_report(
    driver_name: str, rules: List[Dict[str, Any]], results: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Build a complete SARIF report dictionary."""
    return {
        "version": SARIF_VERSION,
        "$schema": SARIF_SCHEMA,
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": driver_name,
                        "informationUri": "",
                        "rules": rules,
                    }
                },
                "results": results,
            }
        ],
    }


def _write_sarif(report: Dict[str, Any], out_path: str) -> None:
    """Write SARIF JSON to file and set restrictive permissions."""
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)
    try:
        os.chmod(out_path, 0o600)
    except Exception:
        pass


def _empty_sarif_for(tool_name: str) -> Dict[str, Any]:
    """Return an empty SARIF report for a given tool."""
    return _sarif_report(tool_name, [], [])


def _read_input(path: str) -> Optional[Any]:
    """Read JSON input from a file; return None on failure."""
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        return None
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except json.JSONDecodeError:
        return None


# -------------------------------
# Converters
# -------------------------------
def conv_bandit(
    in_json: Dict[str, Any], base_uri: Optional[str] = None
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Convert Bandit JSON to SARIF rules and results."""
    results = in_json.get("results", []) or []
    rule_map: Dict[str, Dict[str, Any]] = {}
    sarif_results: List[Dict[str, Any]] = []

    for r in results:
        rule_id = (r.get("test_id") or "BANDIT").strip()
        rule_name = (r.get("test_name") or rule_id).strip()
        filename = _rel_uri(r.get("filename", "") or r.get("file", ""), base_uri)
        msg = (r.get("issue_text") or "").strip()
        severity = r.get("issue_severity") or "low"
        line = int(r.get("line_number") or r.get("line") or 1)
        more_info = r.get("more_info") or ""

        if rule_id not in rule_map:
            rule_map[rule_id] = _make_rule(rule_id, rule_name, more_info)

        sarif_results.append(
            {
                "ruleId": rule_id,
                "level": _level_from_severity(severity),
                "message": {"text": msg},
                "locations": [
                    {
                        "physicalLocation": {
                            "artifactLocation": {"uri": filename},
                            "region": {"startLine": line},
                        }
                    }
                ],
                "properties": {"severity": severity, "more_info": more_info},
            }
        )

    return list(rule_map.values()), sarif_results


def conv_pip_audit(
    in_json: Any, base_uri: Optional[str] = None
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Convert pip-audit JSON to SARIF rules and results."""
    deps = []
    if isinstance(in_json, dict) and "dependencies" in in_json:
        deps = in_json.get("dependencies") or []
    elif isinstance(in_json, list):
        deps = in_json

    rule_map: Dict[str, Dict[str, Any]] = {}
    sarif_results: List[Dict[str, Any]] = []

    for d in deps:
        name = d.get("name", "unknown")
        version = d.get("version", "")
        vulns = d.get("vulns") or d.get("vulnerabilities") or []
        for v in vulns:
            vuln_id = (
                v.get("id") or (v.get("advisory") or {}).get("id") or "PIP-AUDIT"
            ).strip()
            desc = v.get("description") or ""
            url = (v.get("advisory") or {}).get("url") or ""
            severity = (v.get("severity") or "").upper() or "MEDIUM"
            fix_versions = v.get("fix_versions") or []
            aliases = v.get("aliases") or []

            if vuln_id not in rule_map:
                rule_map[vuln_id] = _make_rule(vuln_id, f"Dependency {vuln_id}", url)

            text = f"{name} {version}: {desc}".strip() or f"{name} {version}: {vuln_id}"
            sarif_results.append(
                {
                    "ruleId": vuln_id,
                    "level": _level_from_severity(severity),
                    "message": {"text": text},
                    "locations": [
                        {
                            "physicalLocation": {
                                "artifactLocation": {
                                    "uri": _rel_uri("requirements.txt", base_uri)
                                }
                            }
                        }
                    ],
                    "properties": {
                        "package": name,
                        "version": version,
                        "fix_versions": fix_versions,
                        "aliases": aliases,
                        "advisory_url": url,
                    },
                }
            )

    return list(rule_map.values()), sarif_results


def conv_shellcheck(
    in_json: Any, base_uri: Optional[str] = None
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Convert ShellCheck JSON to SARIF rules and results."""
    findings: List[Dict[str, Any]] = []

    if isinstance(in_json, list):
        findings = in_json
    elif isinstance(in_json, dict) and "comments" in in_json:
        findings = in_json["comments"]
    elif isinstance(in_json, dict) and "files" in in_json:
        for f in in_json.get("files", []):
            for w in f.get("warnings", []) or []:
                w["file"] = f.get("file", w.get("file"))
                findings.append(w)

    rule_map: Dict[str, Dict[str, Any]] = {}
    sarif_results: List[Dict[str, Any]] = []

    for f in findings:
        filename = _rel_uri(f.get("file", ""), base_uri)
        level = f.get("level", "warning")
        code = str(f.get("code", "SC0000"))
        rule_id = f"SC{code}" if code.isdigit() else code
        message = f.get("message", "")
        line = int(f.get("line") or 1)
        column = int(f.get("column") or 1)
        wiki = f"https://www.shellcheck.net/wiki/{rule_id}"

        if rule_id not in rule_map:
            rule_map[rule_id] = _make_rule(rule_id, f"ShellCheck {rule_id}", wiki)

        sarif_results.append(
            {
                "ruleId": rule_id,
                "level": _level_from_severity(level),
                "message": {"text": message},
                "locations": [
                    {
                        "physicalLocation": {
                            "artifactLocation": {"uri": filename},
                            "region": {"startLine": line, "startColumn": column},
                        }
                    }
                ],
                "properties": {"shellcheck_level": level},
            }
        )

    return list(rule_map.values()), sarif_results


# -------------------------------
# CLI Entry Point
# -------------------------------
def main() -> int:
    parser = argparse.ArgumentParser(prog="sarif_convert.py")
    parser.add_argument(
        "tool",
        choices=["bandit", "pip-audit", "shellcheck"],
        help="Tool format to convert",
    )
    parser.add_argument(
        "--in", dest="infile", required=True, help="Input JSON file from the tool"
    )
    parser.add_argument(
        "--out", dest="outfile", required=True, help="Output SARIF file path"
    )
    parser.add_argument(
        "--base-uri",
        dest="base_uri",
        default=None,
        help="Repository root for relative URIs",
    )
    args = parser.parse_args()

    data = _read_input(args.infile)
    base = args.base_uri or os.getcwd()

    if data is None:
        print(
            f"[WARN] No usable input at {args.infile} — writing empty SARIF",
            file=sys.stderr,
        )
        _write_sarif(_empty_sarif_for(args.tool), args.outfile)
        return 0

    if args.tool == "bandit":
        rules, results = conv_bandit(data, base)
        report = _sarif_report("Bandit", rules, results)
    elif args.tool == "pip-audit":
        rules, results = conv_pip_audit(data, base)
        report = _sarif_report("pip-audit", rules, results)
    else:
        rules, results = conv_shellcheck(data, base)
        report = _sarif_report("ShellCheck", rules, results)

    _write_sarif(report, args.outfile)
    return 0


if __name__ == "__main__":
    sys.exit(main())
