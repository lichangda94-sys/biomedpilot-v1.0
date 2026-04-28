"""Platform-neutral launcher for the GEO desktop tool."""

from __future__ import annotations

import argparse
import importlib.util
import platform
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent

# Keep REPO_ROOT ahead of geo_tool/ on sys.path so shared top-level packages
# resolve to the canonical repo packages even when this module is imported.
for candidate in (SCRIPT_DIR, REPO_ROOT):
    candidate_text = str(candidate)
    if candidate_text not in sys.path:
        sys.path.insert(0, candidate_text)


def module_available(module_name: str) -> bool:
    return importlib.util.find_spec(module_name) is not None


def repo_venv_python_candidates(repo_root: Path = REPO_ROOT) -> list[Path]:
    venv_root = repo_root / ".venv"
    return [
        venv_root / "bin" / "python",
        venv_root / "Scripts" / "python.exe",
    ]


def resolve_repo_venv_python(repo_root: Path = REPO_ROOT) -> Path | None:
    for candidate in repo_venv_python_candidates(repo_root):
        if candidate.exists():
            return candidate
    return None


def canonical_entrypoint() -> str:
    if platform.system() == "Windows":
        return "py -3 geo_tool/run_geo_tool.py"
    return "python geo_tool/run_geo_tool.py"


def install_command() -> str:
    if platform.system() == "Windows":
        return "py -3 -m pip install -r geo_tool/requirements.txt"
    return "python -m pip install -r geo_tool/requirements.txt"


def run_check() -> int:
    gui_available = module_available("PySide6")
    base_dependencies = {
        "requests": module_available("requests"),
        "GEOparse": module_available("GEOparse"),
        "pandas": module_available("pandas"),
        "numpy": module_available("numpy"),
    }
    repo_venv_python = resolve_repo_venv_python()

    print(f"repo_root={REPO_ROOT}")
    print(f"script_dir={SCRIPT_DIR}")
    print(f"python={sys.executable}")
    print(f"platform={platform.system()} {platform.release()}")
    print(f"canonical_entrypoint={canonical_entrypoint()}")
    print(f"repo_venv_python={repo_venv_python or 'missing'}")
    print(f"gui_available={gui_available}")
    for name, available in base_dependencies.items():
        print(f"{name}_available={available}")

    return 0 if all(base_dependencies.values()) else 1


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Launch or verify the GEO desktop tool environment.")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Report base dependency availability without launching the GUI.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.check:
        return run_check()

    if not module_available("PySide6"):
        repo_venv_python = resolve_repo_venv_python()
        lines = [
            "PySide6 is not installed in the current Python environment.",
            f"Install GUI dependencies with: {install_command()}",
            f"Canonical launcher: {canonical_entrypoint()}",
        ]
        if repo_venv_python is not None:
            lines.append(f"Detected repo virtualenv interpreter: {repo_venv_python}")
        print("\n".join(lines), file=sys.stderr)
        return 1

    from main import main as gui_main

    gui_main()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
