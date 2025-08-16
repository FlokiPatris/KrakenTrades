#!/usr/bin/env python3
"""
Convert ShellCheck JSON output to SARIF v2.1.0 format.

Usage:
    python3 shellcheck_to_sarif.py <input_json> <output_sarif> <tool_name> <tool_version>

Example:
    python3 shellcheck_to_sarif.py \
        sarif-reports/shellcheck.json \
        sarif-reports/shellcheck.sarif \
        shellcheck \
        0.9.0
"""

import json
import sys
import pathlib
import datetime

SARIF_VERSION = "2.1.0"
SARIF_SCHEMA = "https://json.schemastore.org/sarif-2.1.0.json"


def load_shellcheck_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        sys.exit(f"ERROR: Input file '{path}' not found.")
    except json.JSONDecodeError as e:
        sys.exit(f"ERROR: Failed to parse JSON: {e}")


def shellcheck_to_sarif(sc_data, tool_name, tool_version):
    """Convert parsed ShellCheck JSON to SARIF log dict."""
    results = []
    for diag in sc_data:
        level = {
            "error": "error",
            "warning": "warning",
            "info": "note",
            "style": "note",
        }.get(diag.get("level", "").lower(), "none")

        results.append(
            {
                "ruleId": str(diag.get("code")),
                "level": level,
                "message": {"text": diag.get("message", "")},
                "locations": [
                    {
                        "physicalLocation": {
                            "artifactLocation": {
                                "uri": str(
                                    pathlib.Path(diag.get("file", "")).as_posix()
                                )
                            },
                            "region": {
                                "startLine": diag.get("line", 1),
                                "startColumn": diag.get("column", 1),
                            },
                        }
                    }
                ],
            }
        )

    return {
        "version": SARIF_VERSION,
        "$schema": SARIF_SCHEMA,
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": tool_name,
                        "version": tool_version,
                        "informationUri": "https://www.shellcheck.net/",
                        "rules": [],  # ShellCheck doesn't provide separate rule metadata here
                    }
                },
                "results": results,
                "columnKind": "utf16CodeUnits",
                "originalUriBaseIds": {
                    "%SRCROOT%": {"uri": pathlib.Path(".").resolve().as_uri() + "/"}
                },
            }
        ],
    }


def save_sarif(data, path):
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"SARIF written to {path}")


def main():
    if len(sys.argv) != 5:
        sys.exit(
            f"Usage: {sys.argv[0]} <input_json> <output_sarif> <tool_name> <tool_version>"
        )
    input_json, output_sarif, tool_name, tool_version = sys.argv[1:5]

    sc_data = load_shellcheck_json(input_json)
    sarif_log = shellcheck_to_sarif(sc_data, tool_name, tool_version)
    save_sarif(sarif_log, output_sarif)


if __name__ == "__main__":
    main()
