#!/usr/bin/env bash

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root_default="$(cd "${script_dir}/.." && pwd -P)"

repo_root="$repo_root_default"
python_command=""
log_dir=""
declare -a pipeline_args=()

write_step() {
    printf '==> %s\n' "$1"
}

die() {
    printf 'Error: %s\n' "$1" >&2
    exit 1
}

usage() {
    cat <<'EOF'
Usage: scripts/daily_pipeline.sh [options]

Options:
  --repo-root PATH         Repository root path.
  --python-command CMD     Python interpreter path or command name.
  --log-dir PATH           Directory used for log files.
  --help                   Show this help message.

Any additional arguments are forwarded to:
  python -m csbaoyan_daily.cli pipeline
EOF
}

while (($# > 0)); do
    case "$1" in
        --repo-root)
            (($# >= 2)) || die "--repo-root requires a value."
            repo_root="$2"
            shift 2
            ;;
        --python-command)
            (($# >= 2)) || die "--python-command requires a value."
            python_command="$2"
            shift 2
            ;;
        --log-dir)
            (($# >= 2)) || die "--log-dir requires a value."
            log_dir="$2"
            shift 2
            ;;
        --help|-h)
            usage
            exit 0
            ;;
        *)
            pipeline_args+=("$1")
            shift
            ;;
    esac
done

resolve_existing_dir() {
    local path="$1"

    [[ -d "$path" ]] || die "Directory does not exist: $path"
    (
        cd "$path"
        pwd -P
    )
}

resolve_python_command() {
    if [[ -n "$python_command" ]]; then
        printf '%s\n' "$python_command"
        return 0
    fi

    local candidate=""
    for candidate in \
        "${resolved_repo_root}/.venv/bin/python" \
        "${resolved_repo_root}/venv/bin/python"; do
        if [[ -x "$candidate" ]]; then
            printf '%s\n' "$candidate"
            return 0
        fi
    done

    if command -v python3 >/dev/null 2>&1; then
        command -v python3
        return 0
    fi

    if command -v python >/dev/null 2>&1; then
        command -v python
        return 0
    fi

    die "Python was not found. Install Python first, or pass --python-command."
}

resolved_repo_root="$(resolve_existing_dir "$repo_root")"
resolved_python_command="$(resolve_python_command)"

if [[ -n "$log_dir" ]]; then
    mkdir -p "$log_dir"
    resolved_log_dir="$(resolve_existing_dir "$log_dir")"
else
    resolved_log_dir="${resolved_repo_root}/logs"
    mkdir -p "$resolved_log_dir"
fi

lock_path="${resolved_log_dir}/daily_pipeline.lock"
if command -v flock >/dev/null 2>&1; then
    exec 9>"$lock_path"
    flock -n 9 || die "Another daily pipeline run is already in progress."
fi

log_path="${resolved_log_dir}/daily_pipeline_$(date '+%Y%m%d_%H%M%S').log"
exec > >(tee -a "$log_path") 2>&1

write_step "Log file: $log_path"
trap 'die "Daily pipeline failed. Check the log above for the failing step."' ERR

cd "$resolved_repo_root"
export PYTHONPATH="${resolved_repo_root}/src${PYTHONPATH:+:${PYTHONPATH}}"

write_step "Repository: $resolved_repo_root"
write_step "Python: $resolved_python_command"
write_step "Delegating to Python CLI"
"$resolved_python_command" -m csbaoyan_daily.cli pipeline --repo-root "$resolved_repo_root" "${pipeline_args[@]}"
