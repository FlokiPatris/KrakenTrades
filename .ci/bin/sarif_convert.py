#!/usr/bin/env python3
"""
sarif_convert.py — Unified converters to SARIF 2.1.0 for Bandit, pip-audit, ShellCheck.

Design:
- Tool-specific parsers -> normalized (rules, results).
- Shared SARIF builders.
- Writes SARIF with file mode 0o600.
- Pydantic required for input validation.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

# =============================================================================
# 🌐 Constants
# =============================================================================
SARIF_VERSION = "2.1.0"
SARIF_SCHEMA = (
    "https://schemastore.azurewebsites.net/schemas/json/sarif-2.1.0-rtm.5.json"
)


# =============================================================================
# 📦 Pydantic Models
# =============================================================================
class BanditFinding(BaseModel, extra="allow"):
    test_id: Optional[str] = None
    test_name: Optional[str] = None
    filename: Optional[str] = None
    file: Optional[str] = None
    issue_text: Optional[str] = None
    issue_severity: Optional[str] = None
    line_number: Optional[int] = Field(default=None, alias="line")
    more_info: Optional[str] = None


class PipAuditVuln(BaseModel, extra="allow"):
    id: Optional[str] = None
    description: Optional[str] = None
    severity: Optional[str] = None
    fix_versions: Optional[List[str]] = None
    aliases: Optional[List[str]] = None
    advisory: Optional[Dict[str, Any]] = None


class ShellCheckFinding(BaseModel, extra="allow"):
    file: Optional[str] = None
    level: Optional[str] = None
    code: Optional[str] = None
    message: Optional[str] = None
    line: Optional[int] = None
    column: Optional[int] = None


# =============================================================================
# 🛠️ Helper Functions
# =============================================================================
def _rel_uri(path: str, base: Optional[str] = None) -> str:
    if not path:
        return ""
    if base and os.path.isabs(path):
        try:
            return os.path.relpath(path, base)
        except ValueError:
            return path
    return path


def _level_from_severity(sev: str) -> str:
    s = (sev or "").lower()
    if s in {"critical", "high", "error", "fatal"}:
        return "error"
    if s in {"medium", "moderate", "warning", "warn"}:
        return "warning"
    return "note"


def _make_rule(rule_id: str, name: str, help_uri: str = "") -> Dict[str, Any]:
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
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    if os.path.exists(out_path):
        os.remove(out_path)
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)
    try:
        os.chmod(out_path, 0o600)
    except PermissionError:
        pass


def _empty_sarif_for(tool_name: str) -> Dict[str, Any]:
    return _sarif_report(tool_name, [], [])


def _read_input(path: str) -> Optional[Any]:
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        return None
    with open(path, "r", encoding="utf-8") as fh:
        try:
            return json.load(fh)
        except json.JSONDecodeError:
            return None


# =============================================================================
# 🔄 Converters
# =============================================================================
def conv_bandit(
    in_json: Dict[str, Any], base_uri: Optional[str] = None
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    results = in_json.get("results", []) or []
    rule_map: Dict[str, Dict[str, Any]] = {}
    sarif_results: List[Dict[str, Any]] = []

    for raw in results:
        finding = BanditFinding(**raw)
        rule_id = (finding.test_id or "BANDIT").strip()
        rule_name = (finding.test_name or rule_id).strip()
        filename = _rel_uri(finding.filename or finding.file or "", base_uri)
        msg = (finding.issue_text or "").strip()
        severity = finding.issue_severity or "low"
        line = int(finding.line_number or 1)
        more_info = finding.more_info or ""

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
    deps = in_json.get("dependencies", []) if isinstance(in_json, dict) else in_json
    rule_map: Dict[str, Dict[str, Any]] = {}
    sarif_results: List[Dict[str, Any]] = []

    for d in deps:
        name = d.get("name", "unknown")
        version = d.get("version", "")
        vulns = d.get("vulns") or d.get("vulnerabilities") or []
        for v_raw in vulns:
            vuln = PipAuditVuln(**v_raw)
            vuln_id = (
                vuln.id or (vuln.advisory or {}).get("id") or "PIP-AUDIT"
            ).strip()
            desc = vuln.description or ""
            url = (vuln.advisory or {}).get("url") or ""
            severity = (vuln.severity or "MEDIUM").upper()
            fix_versions = vuln.fix_versions or []
            aliases = vuln.aliases or []

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

    for raw in findings:
        finding = ShellCheckFinding(**raw)
        filename = _rel_uri(finding.file or "", base_uri)
        level = finding.level or "warning"
        code = str(finding.code or "SC0000")
        rule_id = f"SC{code}" if code.isdigit() else code
        message = finding.message or ""
        line = int(finding.line or 1)
        column = int(finding.column or 1)
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
