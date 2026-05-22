from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping

from .r_limma_confirmation import R_LIMMA_DESIGN_CONFIG_PATHS


R_LIMMA_DESIGN_CONFIG_SCHEMA_VERSION = "biomedpilot.r_limma_design_config.v1"
R_LIMMA_DESIGN_CONFIG_PATH = R_LIMMA_DESIGN_CONFIG_PATHS[0]


def build_r_limma_design_config(
    deg_ready_package: Mapping[str, Any],
    *,
    comparison_id: str = "case_vs_control",
    case_group: str = "case",
    control_group: str = "control",
) -> dict[str, Any]:
    ready = dict(deg_ready_package)
    alignment = ready.get("sample_alignment_status") if isinstance(ready.get("sample_alignment_status"), dict) else {}
    assignments = alignment.get("sample_group_assignments") if isinstance(alignment.get("sample_group_assignments"), dict) else {}
    blockers = list(str(item) for item in ready.get("blockers", []) or [])
    warnings = list(str(item) for item in ready.get("warnings", []) or [])
    if not assignments:
        blockers.append("r_limma_design_sample_group_assignments_missing")
    if case_group == control_group:
        blockers.append("r_limma_design_case_control_groups_same")

    group_counts: dict[str, int] = {}
    for group in assignments.values():
        group_text = str(group)
        group_counts[group_text] = group_counts.get(group_text, 0) + 1
    if case_group not in group_counts:
        blockers.append(f"r_limma_design_case_group_missing:{case_group}")
    if control_group not in group_counts:
        blockers.append(f"r_limma_design_control_group_missing:{control_group}")
    if group_counts.get(case_group, 0) < 2:
        blockers.append("r_limma_design_case_group_too_small")
    if group_counts.get(control_group, 0) < 2:
        blockers.append("r_limma_design_control_group_too_small")

    sample_table = [
        {"sample_id": str(sample), "group": str(group)}
        for sample, group in sorted(assignments.items(), key=lambda item: str(item[0]))
    ]
    case_samples = [row["sample_id"] for row in sample_table if row["group"] == case_group]
    control_samples = [row["sample_id"] for row in sample_table if row["group"] == control_group]
    payload = {
        "schema_version": R_LIMMA_DESIGN_CONFIG_SCHEMA_VERSION,
        "status": "blocked" if blockers else "confirmed",
        "created_at": _now(),
        "updated_at": _now(),
        "source": "deg_ready_sample_alignment",
        "primary_factor": "group",
        "case_group": case_group,
        "control_group": control_group,
        "sample_table": sample_table,
        "contrast": {
            "contrast_id": comparison_id,
            "factor": "group",
            "case_level": case_group,
            "control_level": control_group,
            "case_samples": case_samples,
            "control_samples": control_samples,
        },
        "covariates": [],
        "blockers": list(dict.fromkeys(blockers)),
        "warnings": list(dict.fromkeys(warnings)),
        "semantic_boundary": "r_limma_design_config_only_not_execution",
    }
    return payload


def save_r_limma_design_config(
    project_root: str | Path,
    deg_ready_package: Mapping[str, Any],
    *,
    comparison_id: str = "case_vs_control",
    case_group: str = "case",
    control_group: str = "control",
) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    payload = build_r_limma_design_config(
        deg_ready_package,
        comparison_id=comparison_id,
        case_group=case_group,
        control_group=control_group,
    )
    path = root / R_LIMMA_DESIGN_CONFIG_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")
