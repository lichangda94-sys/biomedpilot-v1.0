#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

resolve_venv_python() {
  local candidate
  for candidate in \
    "$REPO_ROOT/.venv/bin/python" \
    "$REPO_ROOT/.venv/Scripts/python.exe"
  do
    if [ -x "$candidate" ] || [ -f "$candidate" ]; then
      printf '%s\n' "$candidate"
      return 0
    fi
  done
  return 1
}

VENV_PYTHON="${VENV_PYTHON:-$(resolve_venv_python || true)}"

if [ -z "$VENV_PYTHON" ] || [ ! -f "$VENV_PYTHON" ]; then
  echo "未找到虚拟环境 Python：$VENV_PYTHON"
  echo "请先运行 ./geo_tool/bootstrap_geo_tool.sh"
  echo "或直接使用 canonical entrypoint：python geo_tool/run_geo_tool.py --check"
  exit 1
fi

exec "$VENV_PYTHON" "$REPO_ROOT/geo_tool/run_geo_tool.py" "$@"
