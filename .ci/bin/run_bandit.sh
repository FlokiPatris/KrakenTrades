# File: .ci/bin/run_bandit.sh
#!/usr/bin/env bash
# Install + run Bandit, JSON → SARIF

set -Eeuo pipefail
source ".ci/bin/common.sh"

main() {
  local sarif_dir="${SARIF_DIR:-sarif-reports}"
  local ver="${BANDIT_VERSION:-1.7.5}"
  local tmpdir="${RUNNER_TEMP:-/tmp}"
  local bandit_json
  bandit_json="$(mktemp -p "${tmpdir}" bandit-XXXX.json)"

  ensure_dir_secure "${sarif_dir}"

  python -m pip install --upgrade pip >/dev/null
  pip install --disable-pip-version-check --no-cache-dir "bandit[toml]==${ver}" >/dev/null

  bandit -r "${GITHUB_WORKSPACE:-.}" \
         --severity-level low \
         -f json \
         -o "${bandit_json}" \
         -q || true

  # Brief summary in annotations (no secret data)
  python - <<'PY'
import json, os
p = os.environ.get("bandit_json_path","")
try:
    with open(p,"r",encoding="utf-8") as f:
        d = json.load(f)
    res = d.get("results") or []
    print(f"::notice title=Bandit::results={len(res)}")
    for r in res[:5]:
        print(f"::notice title=Bandit sample::{r.get('test_id')} {r.get('issue_severity')} {r.get('filename')}")
except Exception as e:
    print(f"::warning title=Bandit JSON parse failed::{e}")
PY
  bandit_json_path="${bandit_json}" BANDIT_VERSION="${ver}" SARIF_DIR="${sarif_dir}" \
    python ".ci/bin/bandit_to_sarif.py"

  chmod 600 -- "${sarif_dir}/bandit.sarif" 2>/dev/null || true
  rm -f -- "${bandit_json}"
  echo "::notice title=Bandit SARIF::${sarif_dir}/bandit.sarif"
}

main "$@"
