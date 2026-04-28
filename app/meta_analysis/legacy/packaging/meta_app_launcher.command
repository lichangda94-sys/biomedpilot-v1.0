#!/bin/zsh
set -u

SCRIPT_PATH="${0:A}"
SCRIPT_DIR="${SCRIPT_PATH:h}"
PROJECT_ROOT="${SCRIPT_DIR:h}"

cd "$PROJECT_ROOT" || {
  echo "BioMedPilot Meta could not find the project root: $PROJECT_ROOT"
  exit 1
}

if [[ -f ".venv/bin/activate" ]]; then
  source ".venv/bin/activate"
fi

PYTHON_BIN="${PYTHON:-python3}"
if [[ -x ".venv-meta/bin/python" ]]; then
  PYTHON_BIN=".venv-meta/bin/python"
elif [[ -x ".venv/bin/python" ]]; then
  PYTHON_BIN=".venv/bin/python"
fi

"$PYTHON_BIN" - <<'PY'
try:
    import PySide6  # noqa: F401
except ModuleNotFoundError:
    raise SystemExit(
        "PySide6 is not installed.\n"
        "Install dependencies first, for example:\n"
        "  ./.venv/bin/python -m pip install PySide6\n"
        "Then run packaging/meta_app_launcher.command again."
    )
PY

if [[ $? -ne 0 ]]; then
  exit 1
fi

"$PYTHON_BIN" app_meta/main.py
exit_status=$?
if [[ "$exit_status" -ne 0 ]]; then
  echo ""
  echo "BioMedPilot Meta did not start successfully."
  echo "If the message mentions the Qt platform plugin \"cocoa\", reinstall PySide6 in the project virtual environment:"
  echo "  ./.venv/bin/python -m pip install --force-reinstall PySide6"
  echo "Then try launching again."
fi
exit "$exit_status"
