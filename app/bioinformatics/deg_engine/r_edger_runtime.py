from __future__ import annotations

import subprocess
from typing import Any

from .rscript_adapter import resolve_rscript_path


R_EDGER_RUNTIME_DETECTION_SCHEMA_VERSION = "biomedpilot.r_edger_runtime_detection.v1"


def detect_r_edger_runtime_capabilities(
    rscript_path: str = "Rscript",
    *,
    timeout_seconds: int = 10,
) -> dict[str, Any]:
    """Detect R/Bioconductor/edgeR without installing or executing DEG."""

    script = (
        "cat('R=', R.version$version.string, '\\n', sep='')\n"
        "cat('platform=', R.version$platform, '\\n', sep='')\n"
        "for (pkg in c('BiocManager','edgeR')) {\n"
        "  if (requireNamespace(pkg, quietly=TRUE)) {\n"
        "    cat(pkg, '=', as.character(utils::packageVersion(pkg)), '\\n', sep='')\n"
        "  } else {\n"
        "    cat(pkg, '=MISSING\\n', sep='')\n"
        "  }\n"
        "}\n"
    )
    resolved_rscript_path = resolve_rscript_path(rscript_path)
    command = [resolved_rscript_path, "-e", script]
    try:
        completed = subprocess.run(command, capture_output=True, text=True, timeout=timeout_seconds, check=False)
    except FileNotFoundError as exc:
        return _runtime_detection_blocked(resolved_rscript_path, ["rscript_not_found"], str(exc), command=command)
    except subprocess.TimeoutExpired as exc:
        return _runtime_detection_blocked(
            resolved_rscript_path,
            ["rscript_detection_timeout"],
            str(exc),
            command=command,
            stdout=_text(exc.stdout),
            stderr=_text(exc.stderr),
        )

    parsed = _parse_key_values(completed.stdout)
    blockers: list[str] = []
    if completed.returncode != 0:
        blockers.append(f"rscript_detection_exit_code:{completed.returncode}")
    if not parsed.get("R"):
        blockers.append("r_version_missing")
    if parsed.get("BiocManager") in {None, "", "MISSING"}:
        blockers.append("biocmanager_missing")
    if parsed.get("edgeR") in {None, "", "MISSING"}:
        blockers.append("edger_missing")
    available = not blockers
    capabilities = {
        "runtime.r.available": {
            "available": completed.returncode == 0 and bool(parsed.get("R")),
            "path": resolved_rscript_path,
            "version": parsed.get("R", ""),
            "platform": parsed.get("platform", ""),
        },
        "runtime.bioconductor.available": {
            "available": parsed.get("BiocManager") not in {None, "", "MISSING"},
            "version": parsed.get("BiocManager", ""),
        },
        "package.r.edger.available": {
            "available": parsed.get("edgeR") not in {None, "", "MISSING"},
            "version": parsed.get("edgeR", ""),
        },
    }
    dependency_snapshot = {
        "status": "passed" if available else "blocked",
        "runtime": "system_rscript",
        "rscript_path": resolved_rscript_path,
        "platform": parsed.get("platform", ""),
        "dependencies": {
            "R": capabilities["runtime.r.available"],
            "BiocManager": capabilities["runtime.bioconductor.available"],
            "edgeR": capabilities["package.r.edger.available"],
        },
        "blockers": blockers,
    }
    return {
        "schema_version": R_EDGER_RUNTIME_DETECTION_SCHEMA_VERSION,
        "status": "passed" if available else "blocked",
        "rscript_path": resolved_rscript_path,
        "command": command,
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "external_capabilities": capabilities,
        "dependency_snapshot": dependency_snapshot,
        "warnings": [],
        "blockers": blockers,
    }


def _runtime_detection_blocked(
    rscript_path: str,
    blockers: list[str],
    message: str,
    *,
    command: list[str],
    stdout: str = "",
    stderr: str = "",
) -> dict[str, Any]:
    capabilities = {
        "runtime.r.available": {"available": False, "path": rscript_path, "version": ""},
        "runtime.bioconductor.available": {"available": False, "version": ""},
        "package.r.edger.available": {"available": False, "version": ""},
    }
    return {
        "schema_version": R_EDGER_RUNTIME_DETECTION_SCHEMA_VERSION,
        "status": "blocked",
        "rscript_path": rscript_path,
        "command": command,
        "returncode": None,
        "stdout": stdout,
        "stderr": stderr or message,
        "external_capabilities": capabilities,
        "dependency_snapshot": {
            "status": "blocked",
            "runtime": "system_rscript",
            "rscript_path": rscript_path,
            "dependencies": {
                "R": capabilities["runtime.r.available"],
                "BiocManager": capabilities["runtime.bioconductor.available"],
                "edgeR": capabilities["package.r.edger.available"],
            },
            "blockers": blockers,
        },
        "warnings": [],
        "blockers": blockers,
    }


def _parse_key_values(text: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in text.splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def _text(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value
