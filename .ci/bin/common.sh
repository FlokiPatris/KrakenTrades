# Strict shell, logging, secret validation, secure FS helpers

set -Eeuo pipefail
shopt -s lastpipe

export LC_ALL="${LC_ALL:-C.UTF-8}"
export LANG="${LANG:-C.UTF-8}"
umask 077

trap 'c=$?; echo "::error title=Bash error,file=${BASH_SOURCE:-common.sh},line=${LINENO}::exit ${c}"; exit ${c}' ERR

# --- Logging ---
log_info()  { echo "::notice title=Info::${*}"; }
log_warn()  { echo "::warning::${*}"; }
log_error() { echo "::error::${*}"; }

die() { log_error "$*"; exit 1; }

# --- FS hardening ---
ensure_dir_secure() {
  # $1: dir path
  local d="${1:-}"
  [[ -z "${d}" ]] && die "ensure_dir_secure: missing path"
  mkdir -p -- "${d}"
  chmod 700 -- "${d}" 2>/dev/null || true
}

harden_file() {
  # $1: file path
  local f="${1:-}"
  [[ -e "${f}" ]] && chmod 600 -- "${f}" 2>/dev/null || true
}

# --- Secrets validation ---
validate_required_secrets() {
  local raw="${REQUIRED_SECRETS:-}"
  [[ -z "${raw// /}" ]] && { log_info "No required secrets configured."; return 0; }

  IFS=',' read -r -a keys <<< "${raw}"
  local missing=()
  for k in "${keys[@]}"; do
    local key="${k//[[:space:]]/}"
    [[ -z "${key}" ]] && continue
    [[ -z "${!key-}" ]] && missing+=("${key}")
  done

  if (( ${#missing[@]} > 0 )); then
    die "Missing required secrets: ${missing[*]}"
  fi
  log_info "All required secrets present."
}

# --- CLI dispatch for convenience ---
main() {
  local cmd="${1:-}"
  shift || true
  case "${cmd}" in
    validate_required_secrets) validate_required_secrets "$@";;
    *) die "Unknown command: ${cmd}";;
  esac
}
if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then main "$@"; fi
