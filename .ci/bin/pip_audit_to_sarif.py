from __future__ import annotations

import json
import os
import sys
from typing import Any, Dict, List


def sev_level(s: str | None) -> str:
    m = (s or "").lower()
    if m in ("critical", "high"):
        return "error"
    if m in ("medium",):
        return "warning"
    return "note"


def main() -> int:
    if len(sys.argv) < 5:
        print(
            "usage: pip_audit_to_sarif.py <json_in> <sarif_out> <tool> <version>",
            file=sys.stderr,
        )
        return 2
    jpath, spath, tool, ver = sys.argv[1:5]
    artifact = os.environ.get("PIP_AUDIT_ARTIFACT_URI", "environment")

    try:
        with open(jpath, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except Exception:
        data = []

    deps = data.get("dependencies") or [] if isinstance(data, dict) else (data or [])

    rules: Dict[str, Dict[str, Any]] = {}
    results: List[Dict[str, Any]] = []

    for dep in deps:
        name = dep.get("name") or "unknown"
        version = dep.get("version") or "unknown"
        vulns = dep.get("vulns") or []
        for v in vulns:
            vid = (v.get("id") or "VULN").strip()
            aliases = v.get("aliases") or []
            summary = v.get("description") or v.get("summary") or ""
            adv = v.get("advisory") or {}
            if not summary and isinstance(adv, dict):
                summary = adv.get("summary") or adv.get("description") or ""
            refs = (
                v.get("references")
                or (adv.get("references") if isinstance(adv, dict) else [])
                or []
            )
            severity = (
                v.get("severity")
                or (adv.get("severity") if isinstance(adv, dict) else "")
                or ""
            ).lower()
            fixes = v.get("fix_versions") or []

            if vid not in rules:
                rules[vid] = {
                    "id": vid,
                    "name": vid,
                    "shortDescription": {"text": summary or vid},
                    "helpUri": refs[0] if isinstance(refs, list) and refs else "",
                    "properties": {"aliases": aliases},
                    "defaultConfiguration": {"level": sev_level(severity)},
                }

            msg = f"{name} {version}: {vid}"
            if fixes:
                msg += f" | fix_versions={', '.join(fixes)}"
            if summary:
                msg += f" | {summary}"

            results.append(
                {
                    "ruleId": vid,
                    "level": sev_level(severity),
                    "message": {"text": msg},
                    "locations": [
                        {
                            "physicalLocation": {
                                "artifactLocation": {"uri": artifact},
                                "region": {"startLine": 1},
                            }
                        }
                    ],
                    "properties": {
                        "package": name,
                        "version": version,
                        "severity": severity.upper() if severity else "UNKNOWN",
                        "aliases": aliases,
                        "fix_versions": fixes,
                    },
                }
            )

    out = {
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": tool,
                        "version": ver,
                        "informationUri": "https://github.com/pypa/pip-audit",
                        "rules": list(rules.values()),
                    }
                },
                "results": results,
            }
        ],
    }

    os.makedirs(os.path.dirname(spath) or ".", exist_ok=True)
    with open(spath, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
