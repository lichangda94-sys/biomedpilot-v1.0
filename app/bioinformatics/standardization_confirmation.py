from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.bioinformatics.group_preview import GROUP_PREVIEW_REPORT
from app.bioinformatics.project_recognition import load_recognition_report


STANDARDIZATION_CONFIRMATION = Path("manifests") / "standardization_confirmation.json"
EXPRESSION_ASSET_TYPES = {"expression_matrix", "normalized_expression_matrix", "raw_count_matrix", "tcga_expression_matrix", "gtex_expression_matrix"}
METADATA_ASSET_TYPES = {"sample_metadata", "clinical_metadata", "survival_metadata", "tcga_clinical_metadata", "tcga_sample_metadata", "gtex_sample_metadata"}


def load_standardization_confirmation(project_root: str | Path) -> dict[str, object] | None:
    path = Path(project_root).expanduser().resolve() / STANDARDIZATION_CONFIRMATION
    return _read_json(path) if path.exists() else None


def load_standardization_confirmation_artifacts(project_root: str | Path) -> dict[str, object]:
    root = Path(project_root).expanduser().resolve()
    path = root / STANDARDIZATION_CONFIRMATION
    return {
        "confirmation": _read_json(path) if path.exists() else None,
        "confirmation_path": str(path),
        "candidates": collect_standardization_candidates(root),
    }


def collect_standardization_candidates(project_root: str | Path) -> dict[str, object]:
    root = Path(project_root).expanduser().resolve()
    recognition = _load_recognized_files(root)
    files = [item for item in recognition.get("files", []) or [] if isinstance(item, dict)]
    expression: list[dict[str, object]] = []
    sample_metadata: list[dict[str, object]] = []
    group_candidates: list[dict[str, object]] = []
    species_candidates: list[dict[str, object]] = []
    gene_id_candidates: list[dict[str, object]] = []
    platform_candidates: list[dict[str, object]] = []
    imported_deg: list[dict[str, object]] = []
    for record in files:
        source_name = _source_file_name(record)
        parser_type = _parser_type(record)
        parser_depth = str(record.get("parser_depth") or _content_profile(record).get("parser_depth") or "")
        warnings = _record_warnings(record)
        assets = [asset for asset in record.get("detected_assets", []) or [] if isinstance(asset, dict)]
        roles = {str(role) for role in record.get("recognized_roles", []) or []}
        for asset in assets:
            asset_type = str(asset.get("asset_type") or asset.get("role") or "")
            if asset_type in EXPRESSION_ASSET_TYPES and asset.get("input_eligible") is not False:
                expression.append(_candidate(record, asset, "expression_matrix", source_name, parser_type, parser_depth, warnings))
            elif asset_type in METADATA_ASSET_TYPES and asset.get("input_eligible") is not False:
                sample_metadata.append(_candidate(record, asset, "sample_metadata", source_name, parser_type, parser_depth, warnings))
            elif asset_type == "phenotype_metadata" and asset.get("input_eligible") is not False:
                group_candidates.append(_candidate(record, asset, "group_candidate", source_name, parser_type, parser_depth, warnings))
            elif asset_type in {"platform_annotation", "platform_reference_hint", "gene_annotation"}:
                platform_candidates.append(_candidate(record, asset, "platform_annotation", source_name, parser_type, parser_depth, warnings))
            elif asset_type == "differential_result_table":
                imported_deg.append(_candidate(record, asset, "imported_deg_result", source_name, parser_type, parser_depth, warnings))
        if not assets:
            if roles & EXPRESSION_ASSET_TYPES:
                expression.append(_candidate(record, {}, "expression_matrix", source_name, parser_type, parser_depth, warnings))
            if roles & METADATA_ASSET_TYPES:
                sample_metadata.append(_candidate(record, {}, "sample_metadata", source_name, parser_type, parser_depth, warnings))
        species_candidates.extend(_species_candidates(record, source_name, parser_type, parser_depth, warnings))
        gene_candidate = _gene_id_candidate(record, source_name, parser_type, parser_depth, warnings)
        if gene_candidate:
            gene_id_candidates.append(gene_candidate)
    group_candidates.extend(_group_preview_candidates(root))
    return {
        "schema_version": "biomedpilot.standardization_candidates.v1",
        "generated_at": _now(),
        "expression_matrix_candidates": _dedupe_candidates(expression),
        "sample_metadata_candidates": _dedupe_candidates(sample_metadata),
        "group_candidates": _dedupe_candidates(group_candidates),
        "species_candidates": _dedupe_candidates(species_candidates),
        "gene_id_candidates": _dedupe_candidates(gene_id_candidates),
        "platform_annotation_candidates": _dedupe_candidates(platform_candidates),
        "imported_deg_candidates": _dedupe_candidates(imported_deg),
    }


def save_standardization_confirmation(
    project_root: str | Path,
    *,
    selected_expression_candidate_id: str | None = None,
    expression_value_type: str | None = None,
    expression_value_type_confirmed: bool | None = None,
    selected_sample_metadata_candidate_id: str | None = None,
    group_design: dict[str, object] | None = None,
    species: str | None = None,
    species_confirmed: bool | None = None,
    species_manual_confirmed: bool = False,
    gene_id_type: str | None = None,
    gene_id_type_confirmed: bool | None = None,
    platform_annotation_candidate_id: str | None = None,
    platform_annotation_confirmed: bool | None = None,
) -> dict[str, object]:
    root = Path(project_root).expanduser().resolve()
    candidates = collect_standardization_candidates(root)
    existing = load_standardization_confirmation(root) or _empty_manifest()
    created_at = str(existing.get("created_at") or _now())
    manifest = dict(existing)
    manifest["schema_version"] = "biomedpilot.standardization_confirmation.v1"
    manifest["created_at"] = created_at
    manifest["updated_at"] = _now()
    if selected_expression_candidate_id:
        selected = _find_candidate(candidates, selected_expression_candidate_id)
        if selected:
            manifest["selected_expression_candidate"] = selected
            inferred = str(selected.get("expression_value_type_candidate") or "")
            if inferred and not expression_value_type:
                manifest["expression_value_type_confirmed"] = {"value_type": inferred, "confirmed": False}
    if expression_value_type:
        current = manifest.get("expression_value_type_confirmed") if isinstance(manifest.get("expression_value_type_confirmed"), dict) else {}
        manifest["expression_value_type_confirmed"] = {
            "value_type": expression_value_type,
            "confirmed": bool(expression_value_type_confirmed if expression_value_type_confirmed is not None else current.get("confirmed")),
        }
    elif expression_value_type_confirmed is not None:
        current = manifest.get("expression_value_type_confirmed") if isinstance(manifest.get("expression_value_type_confirmed"), dict) else {}
        manifest["expression_value_type_confirmed"] = {
            "value_type": str(current.get("value_type") or ""),
            "confirmed": bool(expression_value_type_confirmed),
        }
    if selected_sample_metadata_candidate_id:
        selected = _find_candidate(candidates, selected_sample_metadata_candidate_id)
        if selected:
            manifest["selected_sample_metadata_candidate"] = selected
    if group_design is not None:
        manifest["confirmed_group_design"] = {**group_design, "group_confirmed": bool(group_design.get("group_confirmed"))}
    if species is not None:
        manifest["species_confirmed"] = {
            "species": species,
            "confirmed": bool(species_confirmed),
            "manual_confirmed": bool(species_manual_confirmed),
        }
    elif species_confirmed is not None:
        current = manifest.get("species_confirmed") if isinstance(manifest.get("species_confirmed"), dict) else {}
        manifest["species_confirmed"] = {
            "species": str(current.get("species") or ""),
            "confirmed": bool(species_confirmed),
            "manual_confirmed": bool(current.get("manual_confirmed")),
        }
    if gene_id_type is not None:
        manifest["gene_id_type_confirmed"] = {
            "gene_id_type": gene_id_type,
            "confirmed": bool(gene_id_type_confirmed),
            "requires_platform_mapping": gene_id_type in {"probe_id", "unknown"},
        }
    elif gene_id_type_confirmed is not None:
        current = manifest.get("gene_id_type_confirmed") if isinstance(manifest.get("gene_id_type_confirmed"), dict) else {}
        gene_type = str(current.get("gene_id_type") or "")
        manifest["gene_id_type_confirmed"] = {
            "gene_id_type": gene_type,
            "confirmed": bool(gene_id_type_confirmed),
            "requires_platform_mapping": gene_type in {"probe_id", "unknown"},
        }
    if platform_annotation_candidate_id:
        selected = _find_candidate(candidates, platform_annotation_candidate_id)
        manifest["platform_annotation_confirmed"] = {
            "candidate_id": platform_annotation_candidate_id,
            "source_file": str(selected.get("source_file") or "") if selected else "",
            "confirmed": bool(platform_annotation_confirmed),
        }
    elif platform_annotation_confirmed is not None:
        current = manifest.get("platform_annotation_confirmed") if isinstance(manifest.get("platform_annotation_confirmed"), dict) else {}
        manifest["platform_annotation_confirmed"] = {
            "candidate_id": str(current.get("candidate_id") or ""),
            "source_file": str(current.get("source_file") or ""),
            "confirmed": bool(platform_annotation_confirmed),
        }
    manifest["warnings"] = _confirmation_warnings(manifest, candidates)
    manifest["readiness"] = _confirmation_readiness(manifest, candidates)
    path = root / STANDARDIZATION_CONFIRMATION
    _write_json(path, manifest)
    return manifest


def confirm_group_design_from_preview(project_root: str | Path) -> dict[str, object]:
    root = Path(project_root).expanduser().resolve()
    preview = _read_json(root / GROUP_PREVIEW_REPORT) if (root / GROUP_PREVIEW_REPORT).exists() else {}
    group_sizes = preview.get("group_sizes") if isinstance(preview.get("group_sizes"), dict) else {}
    groups = [str(group) for group in group_sizes]
    control = next((group for group in groups if any(token in group.lower() for token in ("control", "normal", "vehicle", "untreated"))), groups[0] if groups else "control")
    case = next((group for group in groups if group != control), groups[1] if len(groups) > 1 else "case")
    design = {
        "group_confirmed": bool(groups),
        "group_column": str(preview.get("selected_preview_field") or "confirmed_group"),
        "case_group": case,
        "control_group": control,
        "group_sizes": group_sizes,
        "sample_group_assignments": preview.get("sample_group_assignments") if isinstance(preview.get("sample_group_assignments"), dict) else {},
        "requires_user_confirmation": False,
        "source": "group_preview",
    }
    return save_standardization_confirmation(root, group_design=design)


def _empty_manifest() -> dict[str, object]:
    return {
        "schema_version": "biomedpilot.standardization_confirmation.v1",
        "selected_expression_candidate": {},
        "expression_value_type_confirmed": {"value_type": "", "confirmed": False},
        "selected_sample_metadata_candidate": {},
        "confirmed_group_design": {"group_confirmed": False},
        "species_confirmed": {"species": "", "confirmed": False, "manual_confirmed": False},
        "gene_id_type_confirmed": {"gene_id_type": "", "confirmed": False, "requires_platform_mapping": False},
        "platform_annotation_confirmed": {"candidate_id": "", "source_file": "", "confirmed": False},
        "warnings": [],
        "readiness": {"standardization_confirmed": False, "deg_preflight_ready": False, "imported_result_ready": False},
        "created_at": _now(),
        "updated_at": _now(),
    }


def _confirmation_readiness(manifest: dict[str, object], candidates: dict[str, object]) -> dict[str, bool]:
    selected = manifest.get("selected_expression_candidate") if isinstance(manifest.get("selected_expression_candidate"), dict) else {}
    value = manifest.get("expression_value_type_confirmed") if isinstance(manifest.get("expression_value_type_confirmed"), dict) else {}
    species = manifest.get("species_confirmed") if isinstance(manifest.get("species_confirmed"), dict) else {}
    gene = manifest.get("gene_id_type_confirmed") if isinstance(manifest.get("gene_id_type_confirmed"), dict) else {}
    group = manifest.get("confirmed_group_design") if isinstance(manifest.get("confirmed_group_design"), dict) else {}
    value_type = str(value.get("value_type") or "")
    standardization_confirmed = bool(
        selected
        and value.get("confirmed")
        and species.get("confirmed")
        and gene.get("confirmed")
    )
    deg_value_ready = value_type == "count" or (value_type == "count_like_candidate" and bool(value.get("confirmed")))
    group_ready = bool(group.get("group_confirmed") and group.get("case_group") and group.get("control_group"))
    imported = candidates.get("imported_deg_candidates")
    return {
        "standardization_confirmed": standardization_confirmed,
        "deg_preflight_ready": bool(selected and deg_value_ready and group_ready),
        "imported_result_ready": bool(isinstance(imported, list) and imported),
    }


def _confirmation_warnings(manifest: dict[str, object], candidates: dict[str, object]) -> list[str]:
    warnings: list[str] = []
    selected = manifest.get("selected_expression_candidate") if isinstance(manifest.get("selected_expression_candidate"), dict) else {}
    value = manifest.get("expression_value_type_confirmed") if isinstance(manifest.get("expression_value_type_confirmed"), dict) else {}
    gene = manifest.get("gene_id_type_confirmed") if isinstance(manifest.get("gene_id_type_confirmed"), dict) else {}
    group = manifest.get("confirmed_group_design") if isinstance(manifest.get("confirmed_group_design"), dict) else {}
    if not selected and _candidate_list(candidates, "expression_matrix_candidates"):
        warnings.append("识别阶段已发现候选表达矩阵，请在标准化阶段确认后再用于分析。")
    if str(value.get("value_type") or "") == "unknown":
        warnings.append("表达值类型为 unknown，必须确认后才能进入 DEG preflight。")
    if str(gene.get("gene_id_type") or "") in {"probe_id", "unknown"}:
        warnings.append("Series Matrix 中的 ID_REF 通常为平台探针 ID，需结合平台注释确认。")
    if not group.get("group_confirmed") and _candidate_list(candidates, "group_candidates"):
        warnings.append("样本分组为候选推断，确认后才可进入 DEG preflight。")
    warnings.append("当前不会运行真实差异分析。")
    return list(dict.fromkeys(warnings))


def _candidate(
    record: dict[str, object],
    asset: dict[str, object],
    candidate_type: str,
    source_name: str,
    parser_type: str,
    parser_depth: str,
    warnings: list[str],
) -> dict[str, object]:
    asset_type = str(asset.get("asset_type") or asset.get("role") or record.get("recognized_type") or "")
    expression_value_type = _expression_value_type(record, asset_type, asset)
    gene_id_type = _gene_id_type(record, asset)
    candidate = {
        "candidate_id": _candidate_id(record, asset_type, candidate_type),
        "candidate_type": candidate_type,
        "asset_type": asset_type,
        "source_file": source_name,
        "source_parser": parser_type,
        "parser_depth": parser_depth,
        "requires_user_confirmation": bool(asset.get("requires_user_confirmation") or record.get("requires_user_confirmation") or candidate_type in {"expression_matrix", "group_candidate"}),
        "warnings": warnings,
        "can_enter_next_step": bool(asset.get("input_eligible", True) and record.get("can_enter_standardization", candidate_type != "expression_matrix") is not False),
        "expression_value_type_candidate": expression_value_type,
        "gene_id_type_candidate": gene_id_type,
        "sample_count": int(record.get("sample_count") or 0),
        "matrix_dimensions": record.get("expression_matrix_dimensions") or asset.get("matrix_dimensions") or {},
        "reason": str(asset.get("reason") or record.get("reason") or ""),
    }
    if candidate_type == "imported_deg_result":
        candidate["can_enter_next_step"] = True
    return candidate


def _species_candidates(record: dict[str, object], source_name: str, parser_type: str, parser_depth: str, warnings: list[str]) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    for item in record.get("species_evidence", []) or []:
        if isinstance(item, dict):
            species = str(item.get("species") or "")
            source_field = str(item.get("source_field") or "")
            confidence = str(item.get("confidence") or "")
        else:
            species = str(item)
            source_field = "recognition"
            confidence = "low"
        if not species:
            continue
        output.append(
            {
                "candidate_id": _hash_id("species", source_name, species, source_field),
                "candidate_type": "species",
                "species": species,
                "source_field": source_field,
                "source_file": source_name,
                "source_parser": parser_type,
                "parser_depth": parser_depth,
                "confidence": confidence,
                "requires_user_confirmation": True,
                "warnings": warnings,
                "can_enter_next_step": True,
            }
        )
    return output


def _gene_id_candidate(record: dict[str, object], source_name: str, parser_type: str, parser_depth: str, warnings: list[str]) -> dict[str, object] | None:
    gene_type = str(record.get("gene_id_type_candidate") or "")
    if not gene_type:
        profile = _content_profile(record)
        first_pattern = str(profile.get("first_column_id_pattern") or "")
        if first_pattern:
            gene_type = {
                "ensembl_id": "ensembl_id",
                "entrez_id": "entrez_id",
                "gene_symbol": "gene_symbol",
                "probe_id": "probe_id",
            }.get(first_pattern, first_pattern)
    if not gene_type:
        return None
    return {
        "candidate_id": _hash_id("gene_id", source_name, gene_type),
        "candidate_type": "gene_id",
        "gene_id_type": gene_type,
        "source_file": source_name,
        "source_parser": parser_type,
        "parser_depth": parser_depth,
        "requires_user_confirmation": True,
        "requires_platform_mapping": gene_type in {"probe_id", "unknown"},
        "warnings": warnings,
        "can_enter_next_step": True,
    }


def _group_preview_candidates(root: Path) -> list[dict[str, object]]:
    path = root / GROUP_PREVIEW_REPORT
    if not path.exists():
        return []
    preview = _read_json(path)
    if str(preview.get("status") or "") != "preview_only":
        return []
    field = str(preview.get("selected_preview_field") or "")
    if not field:
        return []
    source = Path(str(preview.get("source_file") or "")).name or "group_preview"
    return [
        {
            "candidate_id": _hash_id("group_preview", source, field),
            "candidate_type": "group_candidate",
            "asset_type": "phenotype_metadata",
            "source_file": source,
            "source_parser": "group_preview",
            "parser_depth": "candidate_preview",
            "requires_user_confirmation": True,
            "warnings": ["样本分组为候选推断，确认后才可进入 DEG preflight。"],
            "can_enter_next_step": True,
            "group_field": field,
            "group_sizes": preview.get("group_sizes") if isinstance(preview.get("group_sizes"), dict) else {},
            "sample_group_assignments": preview.get("sample_group_assignments") if isinstance(preview.get("sample_group_assignments"), dict) else {},
        }
    ]


def _find_candidate(candidates: dict[str, object], candidate_id: str) -> dict[str, object] | None:
    for key in (
        "expression_matrix_candidates",
        "sample_metadata_candidates",
        "group_candidates",
        "species_candidates",
        "gene_id_candidates",
        "platform_annotation_candidates",
        "imported_deg_candidates",
    ):
        for item in _candidate_list(candidates, key):
            if str(item.get("candidate_id") or "") == candidate_id:
                return dict(item)
    return None


def _candidate_list(candidates: dict[str, object], key: str) -> list[dict[str, object]]:
    values = candidates.get(key)
    return [item for item in values if isinstance(item, dict)] if isinstance(values, list) else []


def _load_recognized_files(root: Path) -> dict[str, object]:
    recognized_files = root / "logs" / "recognition" / "recognized_files.json"
    if recognized_files.exists():
        return _read_json(recognized_files)
    return load_recognition_report(root) or {}


def _source_file_name(record: dict[str, object]) -> str:
    name = str(record.get("file_name") or "")
    if name:
        return name
    return Path(str(record.get("original_path") or "")).name


def _parser_type(record: dict[str, object]) -> str:
    container = str(record.get("container_format") or record.get("container_type") or "")
    if container in {"geo_series_matrix", "geo_family_soft"}:
        return container
    primary = str(record.get("recognized_type") or "")
    source = str(Path(str(record.get("file_name") or record.get("original_path") or "")).suffix.lower())
    if primary == "geo_series_matrix_container":
        return "geo_series_matrix"
    if primary == "geo_soft_container":
        return "geo_family_soft"
    if source == ".xlsx":
        return "xlsx"
    if source in {".csv", ".tsv"}:
        return source.lstrip(".")
    if primary in {"expression_matrix", "normalized_expression_matrix", "raw_count_matrix", "tcga_expression_matrix", "gtex_expression_matrix", "tabular_text_file"}:
        return "processed_table"
    return primary or "unknown"


def _expression_value_type(record: dict[str, object], asset_type: str, asset: dict[str, object]) -> str:
    existing = str(asset.get("expression_value_type_candidate") or record.get("expression_value_type_candidate") or "")
    if existing:
        return existing
    label = str(asset.get("label_zh") or asset.get("reason") or "").lower()
    if "fpkm" in label:
        return "FPKM"
    if "tpm" in label:
        return "TPM"
    if asset_type == "raw_count_matrix":
        return "count"
    if asset_type == "tcga_expression_matrix":
        return "tcga_expression_candidate"
    if asset_type == "gtex_expression_matrix":
        return "gtex_reference_expression_candidate"
    if asset_type == "normalized_expression_matrix":
        return "normalized_or_log_expression"
    profile = _content_profile(record)
    role = str(profile.get("possible_table_role") or "")
    if role == "raw_count_matrix":
        return "count"
    if role == "normalized_expression_matrix":
        return "normalized_or_log_expression"
    return "unknown"


def _gene_id_type(record: dict[str, object], asset: dict[str, object]) -> str:
    existing = str(asset.get("gene_id_type_candidate") or record.get("gene_id_type_candidate") or "")
    if existing:
        return existing
    profile = _content_profile(record)
    pattern = str(profile.get("first_column_id_pattern") or "")
    return {
        "ensembl_id": "ensembl_id",
        "entrez_id": "entrez_id",
        "gene_symbol": "gene_symbol",
        "probe_id": "probe_id",
    }.get(pattern, "unknown")


def _content_profile(record: dict[str, object]) -> dict[str, object]:
    profile = record.get("content_profile")
    return profile if isinstance(profile, dict) else {}


def _record_warnings(record: dict[str, object]) -> list[str]:
    warnings = [str(item) for item in record.get("warnings", []) or [] if str(item)]
    warning = str(record.get("warning") or "")
    if warning:
        warnings.append(warning)
    return list(dict.fromkeys(warnings))


def _candidate_id(record: dict[str, object], asset_type: str, candidate_type: str) -> str:
    return _hash_id(candidate_type, str(record.get("original_path") or record.get("file_name") or ""), asset_type)


def _hash_id(*parts: str) -> str:
    raw = "|".join(parts)
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def _dedupe_candidates(candidates: list[dict[str, object]]) -> list[dict[str, object]]:
    deduped: dict[str, dict[str, object]] = {}
    for item in candidates:
        key = str(item.get("candidate_id") or "")
        if key:
            deduped.setdefault(key, item)
    return list(deduped.values())


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
