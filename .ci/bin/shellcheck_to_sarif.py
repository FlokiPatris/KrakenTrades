#!/usr/bin/env python3
"""
Convert ShellCheck JSON output to SARIF v2.1.0.

Usage:
    python3 shellcheck_to_sarif.py <input_json> <output_sarif> <tool_name> <tool_version>

Notes:
- Accepts ShellCheck's JSON array of diagnostics (as produced by: shellcheck --format=json).
- Produces a GitHub-friendly SARIF 2.1.0 log with populated rules and stable paths.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple, Union

SARIF_VERSION = "2.1.0"
SARIF_SCHEMA = "https://json.schemastore.org/sarif-2.1.0.json"
SHELLCHECK_WIKI_BASE = "https://www.shellcheck.net/wiki"

# ----------------------------
# Helpers
# ----------------------------


def load_shellcheck_json(path: Union[str, Path]) -> List[Dict[str, Any]]:
    """Load ShellCheck JSON. ShellCheck emits a list of diagnostics."""
    p = Path(path)
    try:
        with p.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
    except FileNotFoundError:
        sys.exit(f"ERROR: Input file '{p}' not found.")
    except json.JSONDecodeError as e:
        sys.exit(f"ERROR: Failed to parse JSON from '{p}': {e}")

    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and data.get("comments"):
        # Some nonstandard wrappers might place diagnostics under "comments"
        comments = data.get("comments")
        if isinstance(comments, list):
            return comments
    # Fallback to empty list if shape is unexpected
    return []


def to_sarif_level(shellcheck_level: Optional[str]) -> str:
    """Map ShellCheck 'level' to SARIF 'level'."""
    m = (shellcheck_level or "").lower()
    if m == "error":
        return "error"
    if m == "warning":
        return "warning"
    # "info" and "style" are considered notes in SARIF
    return "note"


def rule_metadata(
    sc_code_num: Optional[int], sample_message: str = ""
) -> Dict[str, Any]:
    """Build a SARIF rule for a given SC code number."""
    code_num = str(sc_code_num or "").strip()
    if not code_num.isdigit():
        rule_id = "SCUNKNOWN"
        help_uri = SHELLCHECK_WIKI_BASE
    else:
        rule_id = f"SC{code_num}"
        help_uri = f"{SHELLCHECK_WIKI_BASE}/{rule_id}"

    short = sample_message or rule_id
    return {
        "id": rule_id,
        "name": rule_id,
        "shortDescription": {"text": short[:120] if short else rule_id},
        "helpUri": help_uri,
        # Default to note; actual result level is set per finding
        "defaultConfiguration": {"level": "note"},
    }


def relativize_uri(path: Union[str, Path], srcroot: Path) -> Tuple[str, Optional[str]]:
    """
    Return (relative_posix_uri, uriBaseId) for a path, using %SRCROOT% when inside srcroot.
    If not relative, return absolute as posix and no base id.
    """
    try:
        rel = Path(path).resolve().relative_to(srcroot.resolve())
        return rel.as_posix(), "%SRCROOT%"
    except Exception:
        return Path(path).resolve().as_posix(), None


def location_region(diag: Dict[str, Any]) -> Dict[str, int]:
    """Build SARIF region from ShellCheck diagnostic fields."""
    start_line = int(diag.get("line") or 1)
    start_col = int(diag.get("column") or 1)
    end_line = int(diag.get("endLine") or start_line)
    end_col = int(diag.get("endColumn") or start_col)
    return {
        "startLine": start_line,
        "startColumn": start_col,
        "endLine": end_line,
        "endColumn": end_col,
    }


def fingerprint_for(diag: Dict[str, Any]) -> Dict[str, str]:
    """
    Create lightweight, stable partial fingerprints to help deduplicate in GitHub.
    Not the official hashing, but good enough for practical stability.
    """
    file_path = str(diag.get("file") or "")
    code_num = str(diag.get("code") or "")
    line = str(diag.get("line") or "")
    basis = f"{file_path}:{line}:SC{code_num}"
    h = hashlib.sha256(basis.encode("utf-8")).hexdigest()
    # GitHub recognizes these keys if present
    return {
        "primaryLocationLineHash": h[:20],
        "primaryLocationStartColumnFingerprint": h[20:40],
    }


# ----------------------------
# Conversion
# ----------------------------


def shellcheck_to_sarif(
    sc_data: List[Dict[str, Any]],
    tool_name: str,
    tool_version: str,
    srcroot_env: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Convert ShellCheck diagnostics list to SARIF.
    - Populates rules (unique SC codes) with wiki help URIs.
    - Uses %SRCROOT% base for relative paths when possible.
    """
    srcroot = Path(srcroot_env or os.environ.get("SHELLCHECK_SRCROOT") or os.getcwd())

    results: List[Dict[str, Any]] = []
    rules_index: Dict[str, Dict[str, Any]] = {}

    for diag in sc_data:
        code_num = diag.get("code")
        rule_id = f"SC{code_num}" if code_num is not None else "SCUNKNOWN"

        # Ensure we have a rule entry
        if rule_id not in rules_index:
            rules_index[rule_id] = rule_metadata(
                code_num, sample_message=str(diag.get("message") or "")
            )

        level = to_sarif_level(diag.get("level"))
        rel_uri, base_id = relativize_uri(diag.get("file", ""), srcroot)
        region = location_region(diag)

        location: Dict[str, Any] = {
            "physicalLocation": {
                "artifactLocation": {"uri": rel_uri},
                "region": region,
            }
        }
        if base_id:
            location["physicalLocation"]["artifactLocation"]["uriBaseId"] = base_id

        result: Dict[str, Any] = {
            "ruleId": rule_id,
            "level": level,
            "message": {"text": str(diag.get("message") or rule_id)},
            "locations": [location],
            "partialFingerprints": fingerprint_for(diag),
            "properties": {
                "shellcheckCode": code_num,
                "shellcheckLevel": str(diag.get("level") or "").lower(),
            },
        }
        results.append(result)

    sarif: Dict[str, Any] = {
        "version": SARIF_VERSION,
        "$schema": SARIF_SCHEMA,
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": tool_name or "shellcheck",
                        "version": tool_version or "",
                        "informationUri": "https://www.shellcheck.net/",
                        "rules": list(rules_index.values()),
                    }
                },
                "originalUriBaseIds": {
                    "%SRCROOT%": {"uri": srcroot.resolve().as_uri() + "/"}
                },
                "columnKind": "utf16CodeUnits",
                "results": results,
            }
        ],
    }
    return sarif


def save_sarif(data: Dict[str, Any], path: Union[str, Path]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)
    print(f"SARIF written to {p}")


# ----------------------------
# Entrypoint
# ----------------------------


def main() -> int:
    if len(sys.argv) != 5:
        print(
            f"Usage: {sys.argv[0]} <input_json> <output_sarif> <tool_name> <tool_version>",
            file=sys.stderr,
        )
        return 2

    input_json, output_sarif, tool_name, tool_version = sys.argv[1:5]
    diagnostics = load_shellcheck_json(input_json)
    sarif_log = shellcheck_to_sarif(diagnostics, tool_name, tool_version)
    save_sarif(sarif_log, output_sarif)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
