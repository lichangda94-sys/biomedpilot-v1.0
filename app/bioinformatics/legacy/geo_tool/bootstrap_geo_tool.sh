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

PYTHON_BIN="${PYTHON_BIN:-python3}"
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  if command -v python >/dev/null 2>&1; then
    PYTHON_BIN="python"
  else
    echo "未找到可用的 Python 解释器。"
    echo "请先安装 Python 3.10+，或通过环境变量指定："
    echo "  PYTHON_BIN=/path/to/python ./geo_tool/bootstrap_geo_tool.sh"
    exit 1
  fi
fi

echo "== 1) 检查 Python =="
"$PYTHON_BIN" --version

echo "== 2) 创建虚拟环境 =="
"$PYTHON_BIN" -m venv .venv

VENV_PYTHON="$(resolve_venv_python || true)"
if [ -z "$VENV_PYTHON" ]; then
  echo "虚拟环境创建失败：未找到 .venv 下的 Python 解释器"
  exit 1
fi

echo "== 3) 升级 pip =="
"$VENV_PYTHON" -m pip install --upgrade pip setuptools wheel

echo "== 4) 安装依赖 =="
"$VENV_PYTHON" -m pip install -r "$REPO_ROOT/geo_tool/requirements.txt"

echo "== 5) 检查 Ollama =="
if command -v ollama >/dev/null 2>&1; then
  ollama list || true
else
  echo "未检测到 ollama，跳过。"
fi

echo "== 6) 检查核心依赖 =="
"$VENV_PYTHON" - <<'PY'
import GEOparse, PySide6, pandas, numpy
print("GEOparse:", GEOparse.__version__)
print("PySide6:", PySide6.__version__)
print("pandas:", pandas.__version__)
print("numpy:", numpy.__version__)
PY

echo "== 7) 完成 =="
echo "建议先做环境检查："
echo "  $VENV_PYTHON geo_tool/run_geo_tool.py --check"
echo "启动 GUI："
echo "  $VENV_PYTHON geo_tool/run_geo_tool.py"
echo "macOS/Linux 也可使用包装脚本："
echo "  ./geo_tool/run_geo_tool.sh"
