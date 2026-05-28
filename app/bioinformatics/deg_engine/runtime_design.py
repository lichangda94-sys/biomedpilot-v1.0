from __future__ import annotations

from typing import Any, Mapping, Sequence


def build_runtime_design_table(
    multi_factor_preflight: Mapping[str, Any],
    sample_columns: Sequence[str],
    sample_group_map: Mapping[str, str],
) -> dict[str, Any]:
    preflight = dict(multi_factor_preflight or {})
    design_config = preflight.get("design_config") if isinstance(preflight.get("design_config"), dict) else {}
    covariates = [item for item in design_config.get("covariates", []) or [] if isinstance(item, dict)]
    covariate_names = [str(item.get("name") or "").strip() for item in covariates if str(item.get("name") or "").strip()]
    sample_rows = [row for row in design_config.get("sample_table", []) or [] if isinstance(row, dict)]
    sample_by_id = {str(row.get("sample_id") or ""): row for row in sample_rows if str(row.get("sample_id") or "")}
    primary_factor = str(design_config.get("primary_factor") or "group")
    blockers: list[str] = []
    rows: list[dict[str, Any]] = []
    if covariate_names and not sample_by_id:
        blockers.append("multi_factor_covariate_sample_table_missing")
    for sample in sample_columns:
        group = str(sample_group_map.get(sample) or "")
        row: dict[str, Any] = {"sample": sample, "group": group}
        source = sample_by_id.get(sample)
        if covariate_names and source is None:
            blockers.append(f"multi_factor_design_sample_missing:{sample}")
            source = {}
        if source:
            source_group = str(source.get(primary_factor) or source.get("group") or "")
            if source_group and source_group != group:
                blockers.append(f"multi_factor_design_group_mismatch:{sample}")
        for covariate_name in covariate_names:
            value = (source or {}).get(covariate_name)
            if value is None or str(value).strip() == "":
                blockers.append(f"multi_factor_design_covariate_missing:{sample}:{covariate_name}")
            row[covariate_name] = value
        rows.append(row)
    fieldnames = ["sample", "group", *covariate_names]
    return {
        "status": "passed" if not blockers else "blocked",
        "fieldnames": fieldnames,
        "rows": rows,
        "covariates": covariates,
        "covariate_names": covariate_names,
        "design_formula": _design_formula(covariate_names),
        "blockers": list(dict.fromkeys(blockers)),
        "warnings": [],
    }


def _design_formula(covariate_names: Sequence[str]) -> str:
    if covariate_names:
        return "~ " + " + ".join([*covariate_names, "group"])
    return "~ group"
