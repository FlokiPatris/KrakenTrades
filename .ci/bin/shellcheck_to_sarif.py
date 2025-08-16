#!/usr/bin/env python3
"""
Convert ShellCheck JSON to SARIF v2.1.0.

Usage:
  python3 shellcheck_to_sarif.py <input_json> <output_sarif> <tool_name> <tool_version>
"""

import hashlib
import json
import os
import sys
from pathlib import Path

SARIF_VERSION = "2.1.0"
SARIF_SCHEMA = "https://json.schemastore.org/sarif-2.1.0.json"
SHELLCHECK_WIKI = "https://www.shellcheck.net/wiki"


def load_shellcheck_json(path: str):
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
    if isinstance(data, dict) and isinstance(data.get("comments"), list):
        return data["comments"]
    return []


def to_level(lvl: str | None) -> str:
    m = (lvl or "").lower()
    return "error" if m == "error" else "warning" if m == "warning" else "note"


def rule_for(code: int | None, msg: str = "") -> dict:
    code_s = str(code or "").strip()
    if code_s.isdigit():
        rid = f"SC{code_s}"
        help_uri = f"{SHELLCHECK_WIKI}/{rid}"
    else:
        rid = "SCUNKNOWN"
        help_uri = SHELLCHECK_WIKI
    short = (msg or rid)[:120]
    return {
        "id": rid,
        "name": rid,
        "shortDescription": {"text": short},
        "helpUri": help_uri,
        "defaultConfiguration": {"level": "note"},
    }


def relativize(path: str | Path, srcroot: Path) -> tuple[str, str | None]:
    try:
        rel = Path(path).resolve().relative_to(srcroot.resolve())
        return rel.as_posix(), "%SRCROOT%"
    except Exception:
        return Path(path).resolve().as_posix(), None


def region(diag: dict) -> dict:
    sl = int(diag.get("line") or 1)
    sc = int(diag.get("column") or 1)
    el = int(diag.get("endLine") or sl)
    ec = int(diag.get("endColumn") or sc)
    return {"startLine": sl, "startColumn": sc, "endLine": el, "endColumn": ec}


def fingerprints(diag: dict) -> dict:
    basis = f"{diag.get('file','')}:{diag.get('line','')}:SC{diag.get('code','')}"
    h = hashlib.sha256(basis.encode("utf-8")).hexdigest()
    return {
        "primaryLocationLineHash": h[:20],
        "primaryLocationStartColumnFingerprint": h[20:40],
    }


def shellcheck_to_sarif(
    diags: list[dict], tool_name: str, tool_version: str, srcroot_env: str | None = None
) -> dict:
    srcroot = Path(srcroot_env or os.environ.get("SHELLCHECK_SRCROOT") or os.getcwd())
    results: list[dict] = []
    rules: dict[str, dict] = {}

    for d in diags:
        code = d.get("code")
        rid = f"SC{code}" if code is not None else "SCUNKNOWN"
        if rid not in rules:
            rules[rid] = rule_for(code, str(d.get("message") or ""))

        uri, base_id = relativize(d.get("file", ""), srcroot)
        loc = {
            "physicalLocation": {
                "artifactLocation": {"uri": uri}
                | ({"uriBaseId": base_id} if base_id else {}),
                "region": region(d),
            }
        }

        results.append(
            {
                "ruleId": rid,
                "level": to_level(d.get("level")),
                "message": {"text": str(d.get("message") or rid)},
                "locations": [loc],
                "partialFingerprints": fingerprints(d),
                "properties": {
                    "shellcheckCode": d.get("code"),
                    "shellcheckLevel": (d.get("level") or "").lower(),
                },
            }
        )

    return {
        "version": SARIF_VERSION,
        "$schema": SARIF_SCHEMA,
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": tool_name or "shellcheck",
                        "version": tool_version or "",
                        "informationUri": "https://www.shellcheck.net/",
                        "rules": list(rules.values()),
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


def save_sarif(data: dict, path: str):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)
    print(f"SARIF written to {p}")


def main() -> int:
    if len(sys.argv) != 5:
        print(
            f"Usage: {sys.argv[0]} <input_json> <output_sarif> <tool_name> <tool_version>",
            file=sys.stderr,
        )
        return 2
    inp, outp, name, ver = sys.argv[1:5]
    diags = load_shellcheck_json(inp)
    sarif = shellcheck_to_sarif(diags, name, ver)
    save_sarif(sarif, outp)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
