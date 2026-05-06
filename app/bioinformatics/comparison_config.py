from __future__ import annotations

import csv
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable


COMPARISON_CONFIG_RELATIVE_PATH = Path("raw_data") / "local_import" / "manual_supplements" / "comparison_config_manual.tsv"


@dataclass(frozen=True)
class ComparisonSampleAssignment:
    sample_accession: str
    assigned_group: str
    include: bool = True
    evidence_field: str = ""
    evidence_text: str = ""
    confidence: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "sample_accession": self.sample_accession,
            "assigned_group": self.assigned_group,
            "include": self.include,
            "evidence_field": self.evidence_field,
            "evidence_text": self.evidence_text,
            "confidence": self.confidence,
        }


@dataclass(frozen=True)
class ConfirmedComparisonConfig:
    comparison_id: str = "comparison_1"
    group_column: str = "confirmed_group"
    case_group: str = "case"
    control_group: str = "control"
    case_label_zh: str = ""
    control_label_zh: str = ""
    assignments: tuple[ComparisonSampleAssignment, ...] = ()
    source_format: str = "empty"
    warnings: tuple[str, ...] = field(default_factory=tuple)

    @property
    def included_assignments(self) -> tuple[ComparisonSampleAssignment, ...]:
        return tuple(item for item in self.assignments if item.include)

    @property
    def group_assignments(self) -> dict[str, str]:
        return {
            item.sample_accession: item.assigned_group
            for item in self.included_assignments
            if item.sample_accession and item.assigned_group
        }

    @property
    def group_sizes(self) -> dict[str, int]:
        sizes: dict[str, int] = {}
        for group in self.group_assignments.values():
            sizes[group] = sizes.get(group, 0) + 1
        return dict(sorted(sizes.items(), key=lambda pair: pair[0]))

    def to_dict(self) -> dict[str, object]:
        return {
            "comparison_id": self.comparison_id,
            "group_column": self.group_column,
            "case_group": self.case_group,
            "control_group": self.control_group,
            "case_label_zh": self.case_label_zh,
            "control_label_zh": self.control_label_zh,
            "assignments": [item.to_dict() for item in self.assignments],
            "group_assignments": self.group_assignments,
            "group_sizes": self.group_sizes,
            "source_format": self.source_format,
            "warnings": list(self.warnings),
        }


def comparison_config_path(project_root: str | Path) -> Path:
    return Path(project_root).expanduser().resolve() / COMPARISON_CONFIG_RELATIVE_PATH


def load_confirmed_comparison_config(project_root: str | Path) -> ConfirmedComparisonConfig | None:
    path = comparison_config_path(project_root)
    if not path.is_file():
        return None
    return parse_comparison_config_text(path.read_text(encoding="utf-8"))


def parse_comparison_config_text(text: str) -> ConfirmedComparisonConfig:
    rows = _rows(text)
    if not rows:
        return ConfirmedComparisonConfig(source_format="empty", warnings=("comparison_config is empty",))
    comparison_rows, assignment_rows = _split_sections(rows)
    config = _parse_comparison_row(comparison_rows[0] if comparison_rows else {})
    assignments = tuple(
        _parse_assignment_row(row)
        for row in assignment_rows
        if row.get("sample_accession") or row.get("sample_id")
    )
    source_format = "sample_assignments_v1" if assignments else "comparison_only_v1"
    return ConfirmedComparisonConfig(
        comparison_id=config.get("comparison_id") or "comparison_1",
        group_column=config.get("group_column") or "confirmed_group",
        case_group=config.get("case_group") or "case",
        control_group=config.get("control_group") or "control",
        case_label_zh=config.get("case_label_zh") or "",
        control_label_zh=config.get("control_label_zh") or "",
        assignments=assignments,
        source_format=source_format,
    )


def build_comparison_config_text(
    *,
    comparison_id: str,
    group_column: str,
    case_group: str,
    control_group: str,
    case_label_zh: str = "",
    control_label_zh: str = "",
    assignments: tuple[ComparisonSampleAssignment, ...] | list[ComparisonSampleAssignment] = (),
) -> str:
    lines = [
        "comparison_id\tgroup_column\tcase_group\tcontrol_group\tcase_label_zh\tcontrol_label_zh",
        "\t".join([comparison_id, group_column, case_group, control_group, case_label_zh, control_label_zh]),
        "",
        "sample_accession\tassigned_group\tinclude\tevidence_field\tevidence_text\tconfidence",
    ]
    for item in assignments:
        lines.append(
            "\t".join(
                [
                    item.sample_accession,
                    item.assigned_group,
                    "yes" if item.include else "no",
                    item.evidence_field,
                    str(item.evidence_text).replace("\t", " ").replace("\n", " "),
                    item.confidence,
                ]
            )
        )
    return "\n".join(lines) + "\n"


def build_geo_comparison_config_text(
    profile: object,
    *,
    comparison_index: int = 0,
    case_group: str | None = None,
    control_group: str | None = None,
    included_sample_ids: Iterable[str] | None = None,
    assignment_overrides: dict[str, str] | None = None,
    comparison_id: str | None = None,
) -> str:
    comparisons = list(getattr(profile, "candidate_comparisons", ()) or ())
    if not comparisons:
        return build_comparison_config_text(
            comparison_id=comparison_id or "manual_comparison",
            group_column="confirmed_group",
            case_group=case_group or "case",
            control_group=control_group or "control",
        )
    comparison = comparisons[max(0, min(comparison_index, len(comparisons) - 1))]
    selected_case = case_group or str(getattr(comparison, "case_group", "") or "case")
    selected_control = control_group or str(getattr(comparison, "control_group", "") or "control")
    included = {_sample_key(item) for item in included_sample_ids} if included_sample_ids is not None else None
    overrides = {_sample_key(key): value for key, value in (assignment_overrides or {}).items()}
    assignments: list[ComparisonSampleAssignment] = []
    for raw in getattr(comparison, "sample_assignments", ()) or ():
        sample = str(getattr(raw, "sample_accession", "") or "")
        key = _sample_key(sample)
        group = str(overrides.get(key) or getattr(raw, "assigned_group", "") or "")
        include = key in included if included is not None else True
        assignments.append(
            ComparisonSampleAssignment(
                sample_accession=sample,
                assigned_group=group,
                include=include,
                evidence_field=str(getattr(raw, "evidence_field", "") or ""),
                evidence_text=str(getattr(raw, "evidence_text", "") or ""),
                confidence=str(getattr(raw, "confidence", "") or ""),
            )
        )
    field = str(getattr(comparison, "comparison_id", "") or "confirmed_group").split(":", 1)[0] or "confirmed_group"
    return build_comparison_config_text(
        comparison_id=comparison_id or _slug_text(str(getattr(comparison, "label", "") or "confirmed_comparison")),
        group_column=field,
        case_group=selected_case,
        control_group=selected_control,
        case_label_zh=group_label_zh(selected_case),
        control_label_zh=group_label_zh(selected_control),
        assignments=assignments,
    )


def confirmed_group_assignments(config: ConfirmedComparisonConfig | None) -> dict[str, str]:
    return config.group_assignments if config is not None else {}


def comparison_summary_text(config: ConfirmedComparisonConfig | None) -> str:
    if config is None:
        return ""
    case_label = config.case_label_zh or group_label_zh(config.case_group)
    control_label = config.control_label_zh or group_label_zh(config.control_group)
    sizes = config.group_sizes
    case_count = sizes.get(config.case_group, 0)
    control_count = sizes.get(config.control_group, 0)
    if case_count or control_count:
        return f"比较组已确认：{case_label} {case_count} 个 vs {control_label} {control_count} 个。"
    return f"比较组已确认：{case_label} vs {control_label}。"


def group_label_zh(group: str) -> str:
    normalized = _normalize_group(group)
    return {
        "tumor": "肿瘤组",
        "tumour": "肿瘤组",
        "normal": "正常/对照组",
        "adjacent_normal": "正常/对照组",
        "control": "正常/对照组",
        "vehicle": "对照组",
        "dmso": "对照组",
        "untreated": "对照组",
        "malignant": "恶性组",
        "benign": "良性组",
        "treated": "处理组",
        "treatment": "处理组",
        "resistant": "耐药组",
        "sensitive": "敏感组",
        "mutant": "突变组",
        "wild_type": "野生型/对照组",
        "wt": "野生型/对照组",
        "metastatic": "转移组",
        "primary": "原发组",
    }.get(normalized, group or "未命名组")


def evidence_field_label_zh(field: str) -> str:
    normalized = _normalize_group(field)
    return {
        "pathological_diagnostic": "病理诊断信息",
        "pathological_diagnosis": "病理诊断信息",
        "characteristics_ch1": "样本特征",
        "sample_characteristics_ch1": "样本特征",
        "source_name_ch1": "样本来源",
        "sample_source_name_ch1": "样本来源",
        "sample_title": "样本标题",
        "title": "样本标题",
        "description": "样本描述",
        "sample_description": "样本描述",
        "treatment_protocol_ch1": "处理方案",
        "sample_treatment_protocol_ch1": "处理方案",
        "extract_protocol_ch1": "提取方案",
        "sample_extract_protocol_ch1": "提取方案",
        "geo_page_text": "概要和实验设计辅助线索",
        "tissue": "组织信息",
        "disease": "疾病状态",
        "disease_state": "疾病状态",
        "treatment": "处理信息",
        "condition": "实验条件",
        "phenotype": "表型信息",
        "genotype": "基因型信息",
    }.get(normalized, field or "样本注释")


def comparison_sample_match_status(
    config: ConfirmedComparisonConfig | None,
    expression_samples: Iterable[str],
) -> dict[str, object]:
    expression = {_sample_key(item) for item in expression_samples if str(item).strip()}
    assignments = config.group_assignments if config is not None else {}
    metadata = {_sample_key(item) for item in assignments if str(item).strip()}
    matched = expression & metadata
    matched_group_sizes: dict[str, int] = {}
    for sample, group in assignments.items():
        if _sample_key(sample) in matched:
            matched_group_sizes[group] = matched_group_sizes.get(group, 0) + 1
    status = "not_checked"
    if expression and metadata:
        status = "matched" if not (expression ^ metadata) else ("partial" if matched else "mismatch")
    return {
        "expression_sample_count": len(expression),
        "metadata_sample_count": len(metadata),
        "matched_sample_count": len(matched),
        "unmatched_metadata_samples": sorted(metadata - expression),
        "unmatched_expression_samples": sorted(expression - metadata),
        "matched_group_sizes": matched_group_sizes,
        "sample_id_match_status": status,
    }


def expression_samples_from_recognition_report(report: dict[str, Any] | None) -> set[str]:
    samples: set[str] = set()
    if not isinstance(report, dict):
        return samples
    for record in report.get("files", []) or []:
        if not isinstance(record, dict):
            continue
        profile = record.get("content_profile")
        if isinstance(profile, dict):
            for key in ("sample_columns", "sample_ids", "expression_samples"):
                value = profile.get(key)
                if isinstance(value, list):
                    samples.update(str(item) for item in value if str(item).strip())
        for asset in record.get("detected_assets", []) or []:
            if not isinstance(asset, dict):
                continue
            for key in ("sample_columns", "sample_ids", "expression_samples"):
                value = asset.get(key)
                if isinstance(value, list):
                    samples.update(str(item) for item in value if str(item).strip())
    return samples


def _rows(text: str) -> list[dict[str, str]]:
    lines = [line for line in text.splitlines() if line.strip() and not line.lstrip().startswith("#")]
    if not lines:
        return []
    parsed: list[dict[str, str]] = []
    current_header: list[str] | None = None
    for line in lines:
        cells = next(csv.reader([line], delimiter="\t"))
        normalized = [cell.strip() for cell in cells]
        lower = [cell.lower() for cell in normalized]
        if "comparison_id" in lower or "sample_accession" in lower or "sample_id" in lower:
            current_header = lower
            continue
        if current_header is None:
            continue
        padded = normalized + [""] * max(0, len(current_header) - len(normalized))
        parsed.append(dict(zip(current_header, padded, strict=False)))
    return parsed


def _split_sections(rows: list[dict[str, str]]) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    comparisons: list[dict[str, str]] = []
    assignments: list[dict[str, str]] = []
    for row in rows:
        if "sample_accession" in row or "sample_id" in row:
            assignments.append(row)
        elif "comparison_id" in row:
            comparisons.append(row)
    return comparisons, assignments


def _parse_comparison_row(row: dict[str, str]) -> dict[str, str]:
    return {
        "comparison_id": str(row.get("comparison_id") or "").strip(),
        "group_column": str(row.get("group_column") or "").strip(),
        "case_group": str(row.get("case_group") or "").strip(),
        "control_group": str(row.get("control_group") or "").strip(),
        "case_label_zh": str(row.get("case_label_zh") or "").strip(),
        "control_label_zh": str(row.get("control_label_zh") or "").strip(),
    }


def _parse_assignment_row(row: dict[str, str]) -> ComparisonSampleAssignment:
    include = str(row.get("include") or "yes").strip().lower() not in {"0", "false", "no", "n", "exclude", "移除"}
    return ComparisonSampleAssignment(
        sample_accession=str(row.get("sample_accession") or row.get("sample_id") or "").strip(),
        assigned_group=str(row.get("assigned_group") or row.get("group") or "").strip(),
        include=include,
        evidence_field=str(row.get("evidence_field") or "").strip(),
        evidence_text=str(row.get("evidence_text") or "").strip(),
        confidence=str(row.get("confidence") or "").strip(),
    )


def _normalize_group(value: object) -> str:
    return re.sub(r"_+", "_", "".join(character.lower() if character.isalnum() else "_" for character in str(value))).strip("_")


def _sample_key(value: object) -> str:
    return str(value).strip().strip('"').upper()


def _slug_text(value: object) -> str:
    return _normalize_group(value) or "comparison"
