from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the BioMedPilot formal DEG ReleaseBuild gate.")
    parser.add_argument("--skip-full-tests", action="store_true", help="Skip full pytest suites and run runtime/formal DEG gate checks only.")
    parser.add_argument("--json-output", default="", help="Optional JSON output path.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = Path(__file__).resolve().parents[1]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    checks: list[dict[str, Any]] = []
    if not args.skip_full_tests:
        checks.append(_run(root, [sys.executable, "-m", "pytest", "tests/bioinformatics", "-q"]))
        checks.append(_run(root, ["bash", "-lc", "QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q"]))
    checks.append(_run(root, [sys.executable, "-m", "app.main", "--bio-formal-deg-runtime-check"]))
    runtime_payload = _runtime_payload(root)
    blockers = [check["check_id"] for check in checks if check["status"] != "passed"]
    if runtime_payload.get("status") not in {"passed", "blocked_missing_dependency"}:
        blockers.append("formal_deg_runtime_validation_failed")
    payload = {
        "schema_version": "biomedpilot.releasebuild_formal_deg_gate.v1",
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "worktree": str(root),
        "skip_full_tests": bool(args.skip_full_tests),
        "status": "blocked" if blockers else "passed",
        "checks": checks,
        "runtime_validation": runtime_payload,
        "blockers": list(dict.fromkeys(blockers)),
        "warnings": ["runtime_dependencies_missing_but_gracefully_blocked"] if runtime_payload.get("status") == "blocked_missing_dependency" else [],
    }
    if args.json_output:
        output = Path(args.json_output).expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["status"] == "passed" else 1


def _runtime_payload(root: Path) -> dict[str, Any]:
    try:
        from app.bioinformatics.deg_engine.runtime_validation import run_formal_deg_runtime_validation

        return run_formal_deg_runtime_validation()
    except Exception as exc:  # pragma: no cover - regression path.
        return {"status": "failed", "blockers": ["runtime_validation_raised_exception"], "error": f"{exc.__class__.__name__}: {exc}"}


def _run(root: Path, cmd: list[str]) -> dict[str, Any]:
    completed = subprocess.run(cmd, cwd=root, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
    return {
        "check_id": " ".join(cmd),
        "status": "passed" if completed.returncode == 0 else "failed",
        "returncode": completed.returncode,
        "output_tail": completed.stdout[-4000:],
    }


if __name__ == "__main__":
    raise SystemExit(main())
