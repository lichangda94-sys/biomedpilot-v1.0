from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.bioinformatics.results.models import normalize_result_semantics


PLOT_EXPORT_QUALITY_GATE_SCHEMA_VERSION = "biomedpilot.plot_export_quality_gate.v1"


def evaluate_plot_export_quality_gate(project_root: str | Path, plot_artifact: dict[str, Any]) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    blockers: list[str] = []
    warnings: list[str] = []
    semantics = normalize_result_semantics(plot_artifact.get("source_result_semantics"), default="")
    if plot_artifact.get("plot_artifact_scope") == "formal_deg_plot" and semantics != "formal_computed_result":
        blockers.append("formal_plot_qc_requires_formal_computed_source")
    if plot_artifact.get("plot_semantics") != plot_artifact.get("source_result_semantics"):
        blockers.append("plot_qc_semantics_must_inherit_source")
    images = plot_artifact.get("image_artifacts") if isinstance(plot_artifact.get("image_artifacts"), list) else []
    if not images:
        blockers.append("plot_qc_requires_image_artifact")
    image_checks = []
    for image in images:
        if not isinstance(image, dict):
            blockers.append("plot_qc_invalid_image_artifact")
            continue
        check = _check_image(root, image)
        image_checks.append(check)
        blockers.extend(str(item) for item in check.get("blockers", []) or [])
        warnings.extend(str(item) for item in check.get("warnings", []) or [])
    if plot_artifact.get("report_ready_eligible") is True:
        blockers.append("plot_qc_must_not_set_report_ready_eligible")
    return {
        "schema_version": PLOT_EXPORT_QUALITY_GATE_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": "blocked" if blockers else "passed",
        "plot_id": str(plot_artifact.get("plot_id") or ""),
        "plot_type": str(plot_artifact.get("plot_type") or ""),
        "source_result_id": str(plot_artifact.get("source_result_id") or ""),
        "source_result_semantics": semantics,
        "image_checks": image_checks,
        "report_ready_eligible_changed": False,
        "clinical_conclusion_enabled": False,
        "blockers": list(dict.fromkeys(blockers)),
        "warnings": list(dict.fromkeys(warnings)),
    }


def _check_image(root: Path, image: dict[str, Any]) -> dict[str, Any]:
    blockers: list[str] = []
    warnings: list[str] = []
    raw = Path(str(image.get("path") or ""))
    path = raw if raw.is_absolute() else root / raw
    if not path.is_file():
        return {"path": str(path), "status": "blocked", "blockers": ["plot_image_file_missing"], "warnings": []}
    size = path.stat().st_size
    if size <= 0:
        blockers.append("plot_image_file_empty")
    checksum = hashlib.sha256(path.read_bytes()).hexdigest()
    expected = str(image.get("sha256") or "")
    if expected and checksum != expected:
        blockers.append("plot_image_checksum_mismatch")
    if str(image.get("format") or "").lower() == "svg":
        text = path.read_text(encoding="utf-8", errors="replace").lstrip()
        if not text.startswith("<svg"):
            blockers.append("plot_svg_missing_svg_root")
        if "clinical conclusion" not in text and "clinical diagnosis" not in text:
            warnings.append("plot_svg_missing_clinical_boundary_copy")
    return {
        "path": str(path),
        "status": "blocked" if blockers else "passed",
        "size_bytes": size,
        "sha256": checksum,
        "blockers": blockers,
        "warnings": warnings,
    }
