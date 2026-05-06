from __future__ import annotations

import gzip
import json
import re
from collections import Counter
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable


CELL_LINE_PATTERNS = (
    "a375",
    "cal-62",
    "cal62",
    "tpc-1",
    "tpc1",
    "bcpap",
    "8505c",
    "k1",
    "sw1736",
    "ftc-133",
    "ftc133",
    "mda-mb-231",
    "mdamb231",
    "mcf-7",
    "mcf7",
    "a549",
    "h1299",
    "hct116",
    "ht29",
    "hela",
    "hek293",
    "jurkat",
    "u87",
    "u251",
    "ln229",
    "t47d",
)
EXPLICIT_DESIGN_GROUPS = {
    "normal",
    "control",
    "treated",
    "tumor",
    "resistant",
    "sensitive",
    "mutant",
    "wild_type",
    "knockout",
    "metastatic",
    "recurrent",
    "primary",
    "benign",
    "malignant",
}


@dataclass(frozen=True)
class GeoSampleRecord:
    sample_accession: str = ""
    sample_title: str = ""
    source_name_ch1: str = ""
    characteristics_ch1: tuple[str, ...] = ()
    description: str = ""
    treatment_protocol_ch1: str = ""
    extract_protocol_ch1: str = ""
    raw_fields: dict[str, object] = field(default_factory=dict)

    @property
    def accession(self) -> str:
        return self.sample_accession

    @property
    def title(self) -> str:
        return self.sample_title

    @property
    def raw_links(self) -> tuple[str, ...]:
        links = self.raw_fields.get("raw_links", ())
        if isinstance(links, (list, tuple)):
            return tuple(str(item) for item in links if str(item).strip())
        return ()

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class GeoSampleGroupAssignment:
    sample_accession: str
    assigned_group: str
    evidence_field: str
    evidence_text: str
    confidence: str = "low"

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class GeoCandidateComparison:
    comparison_id: str
    label: str
    control_group: str
    case_group: str
    group_sizes: dict[str, int]
    sample_assignments: tuple[GeoSampleGroupAssignment, ...] = ()
    confidence: str = "low"
    evidence: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    requires_user_confirmation: bool = True

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["sample_assignments"] = [item.to_dict() for item in self.sample_assignments]
        return payload


@dataclass(frozen=True)
class GeoSupplementaryFile:
    file_name: str
    file_size: int | None = None
    predicted_type: str = "unknown"
    download_priority: str = "低"
    should_default_select: bool = False
    recommendation: str = "按需查看。"
    recommendation_reason: str = ""
    risk_level: str = "低"
    reason: str = ""
    remote_url: str = ""
    asset_type: str = ""
    role: str = ""
    status: str = ""
    local_path: str = ""
    description: str = ""

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class GeoMetadataProfile:
    accession: str
    title: str = ""
    summary: str = ""
    overall_design: str = ""
    organism: str = ""
    platform_ids: tuple[str, ...] = ()
    experiment_type: str = ""
    sample_records: tuple[GeoSampleRecord, ...] = ()
    geo_sample_count: int | str = ""
    metadata_sample_count: int = 0
    expression_sample_count: int = 0
    matched_sample_count: int = 0
    unmatched_metadata_samples: tuple[str, ...] = ()
    unmatched_expression_samples: tuple[str, ...] = ()
    supplementary_files: tuple[GeoSupplementaryFile, ...] = ()
    supplementary_file_preview: tuple[GeoSupplementaryFile, ...] = ()
    possible_expression_files: tuple[str, ...] = ()
    possible_annotation_files: tuple[str, ...] = ()
    possible_raw_files: tuple[str, ...] = ()
    metadata_source: str = "search_metadata"
    parsing_warnings: tuple[str, ...] = ()
    sample_structure_preview: dict[str, object] = field(default_factory=dict)
    candidate_comparisons: tuple[GeoCandidateComparison, ...] = ()
    analysis_potential_score: int = 0
    analysis_potential_level: str = "低"
    analysis_potential_reason: str = ""
    analysis_availability_status: str = ""
    analysis_availability_warnings: tuple[str, ...] = ()
    suggested_download_files: tuple[str, ...] = ()
    chinese_title: str = ""
    chinese_summary: str = ""
    chinese_brief: str = ""
    consistency_review: dict[str, object] = field(default_factory=dict)
    warnings: tuple[str, ...] = ()

    @property
    def sample_count(self) -> int | str:
        return self.geo_sample_count

    @property
    def analysis_ready_score(self) -> int:
        return self.analysis_potential_score

    @property
    def recommendation_level(self) -> str:
        return self.analysis_potential_level

    @property
    def recommendation_reason(self) -> str:
        return self.analysis_potential_reason

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["sample_records"] = [item.to_dict() for item in self.sample_records]
        payload["supplementary_files"] = [item.to_dict() for item in self.supplementary_files]
        payload["supplementary_file_preview"] = [item.to_dict() for item in self.supplementary_file_preview]
        payload["candidate_comparisons"] = [item.to_dict() for item in self.candidate_comparisons]
        payload["sample_count"] = self.sample_count
        payload["analysis_ready_score"] = self.analysis_ready_score
        payload["recommendation_level"] = self.recommendation_level
        payload["recommendation_reason"] = self.recommendation_reason
        return payload


GeoDatasetProfile = GeoMetadataProfile


class GeoMetadataProfileService:
    """Build conservative GEO structured metadata profiles.

    This service intentionally prefers structured search metadata, family SOFT,
    MINiML-like fields, and Series Matrix headers. HTML parsing is not part of
    the main path.
    """

    def build_profile(
        self,
        *,
        accession: str,
        candidate_metadata: dict[str, Any] | None = None,
        project_root: str | Path | None = None,
        asset_manifest: dict[str, Any] | None = None,
        summary_payload: dict[str, Any] | None = None,
        recognition_report: dict[str, Any] | None = None,
        family_soft_path: str | Path | None = None,
        series_matrix_path: str | Path | None = None,
    ) -> GeoMetadataProfile:
        normalized = _normalize_gse(accession)
        metadata = candidate_metadata or {}
        root = Path(project_root).expanduser().resolve() if project_root is not None else None
        manifest = asset_manifest or _load_asset_manifest(root, normalized) or {}
        family_path = _resolve_existing_path(family_soft_path) or _family_soft_path(root, normalized) or _asset_local_path(manifest, "family_soft")
        series_path = _resolve_existing_path(series_matrix_path) or _asset_local_path(manifest, "series_matrix")

        parsed = _ParsedGeoMetadata(metadata_source="search_metadata")
        if family_path is not None:
            parsed.merge(_parse_family_soft(family_path), source="family_soft")
        if series_path is not None:
            parsed.merge(_parse_series_matrix(series_path), source="series_matrix_header")

        title = _first_text(metadata.get("title_en"), metadata.get("title"), metadata.get("display_title"), parsed.title)
        summary = _first_text(metadata.get("summary_en"), metadata.get("summary"), parsed.summary)
        overall_design = _first_text(metadata.get("overall_design_en"), metadata.get("overall_design"), parsed.overall_design)
        organism = _first_text(metadata.get("organism"), parsed.organism)
        platform_ids = tuple(dict.fromkeys([*_as_text_list(metadata.get("platform_accessions")), *parsed.platform_ids]))
        sample_records = tuple(parsed.sample_records)
        geo_sample_count = _sample_count(sample_records, metadata.get("sample_count"))
        metadata_sample_count = len(sample_records)
        experiment_type = _infer_experiment_type(title, summary, overall_design, str(metadata.get("data_type") or metadata.get("experiment_type") or ""))

        supplementary = _supplementary_files(parsed.supplementary_urls, manifest)
        possible_expression_files = _possible_files(supplementary, predicted_types=("expression_matrix", "series_matrix"))
        possible_annotation_files = _possible_files(supplementary, predicted_types=("sample_metadata", "clinical_metadata", "platform_annotation"))
        possible_raw_files = _possible_files(supplementary, predicted_types=("raw_data",))

        comparisons = _candidate_comparisons(
            sample_records,
            summary=summary,
            overall_design=overall_design,
        )
        count_layers = _count_layers(
            geo_sample_count=geo_sample_count,
            metadata_sample_count=metadata_sample_count,
            sample_records=sample_records,
            recognition_report=recognition_report,
        )
        preview = _sample_structure_preview(
            geo_sample_count=geo_sample_count,
            metadata_sample_count=metadata_sample_count,
            comparisons=comparisons,
            count_layers=count_layers,
        )
        potential_score, potential_level, potential_reason = _analysis_potential(
            title=title,
            summary=summary,
            overall_design=overall_design,
            organism=organism,
            experiment_type=experiment_type,
            geo_sample_count=geo_sample_count,
            metadata_sample_count=metadata_sample_count,
            comparisons=comparisons,
            expression_files=possible_expression_files,
            manifest=manifest,
        )
        consistency = _consistency_review(
            metadata_sample_count=metadata_sample_count,
            geo_sample_count=geo_sample_count,
            platform_ids=platform_ids,
            experiment_type=experiment_type,
            comparisons=comparisons,
            recognition_report=recognition_report,
            count_layers=count_layers,
        )
        availability, availability_warnings = _analysis_availability(
            experiment_type=experiment_type,
            comparisons=comparisons,
            recognition_report=recognition_report,
            count_layers=count_layers,
        )
        suggested = _suggested_download_files(supplementary)
        warnings = [*parsed.parsing_warnings]
        if consistency.get("status") == "needs_review":
            warnings.append("页面元数据与下载文件识别结果不完全一致，请确认比较组或补充文件。")
        if not comparisons:
            warnings.append("未从 sample-level metadata 中识别到明确候选分组。")
        return GeoMetadataProfile(
            accession=normalized,
            title=title,
            summary=summary,
            overall_design=overall_design,
            organism=organism,
            platform_ids=platform_ids,
            experiment_type=experiment_type,
            sample_records=sample_records,
            geo_sample_count=geo_sample_count,
            metadata_sample_count=metadata_sample_count,
            expression_sample_count=int(count_layers.get("expression_sample_count") or 0),
            matched_sample_count=int(count_layers.get("matched_sample_count") or 0),
            unmatched_metadata_samples=tuple(count_layers.get("unmatched_metadata_samples", ()) or ()),
            unmatched_expression_samples=tuple(count_layers.get("unmatched_expression_samples", ()) or ()),
            supplementary_files=tuple(supplementary),
            supplementary_file_preview=tuple(supplementary),
            possible_expression_files=possible_expression_files,
            possible_annotation_files=possible_annotation_files,
            possible_raw_files=possible_raw_files,
            metadata_source=parsed.metadata_source,
            parsing_warnings=tuple(dict.fromkeys(parsed.parsing_warnings)),
            sample_structure_preview=preview,
            candidate_comparisons=tuple(comparisons),
            analysis_potential_score=potential_score,
            analysis_potential_level=potential_level,
            analysis_potential_reason=potential_reason,
            analysis_availability_status=availability,
            analysis_availability_warnings=availability_warnings,
            suggested_download_files=suggested,
            chinese_title=str((summary_payload or {}).get("title_zh") or "").strip(),
            chinese_summary=str((summary_payload or {}).get("summary_zh") or "").strip(),
            chinese_brief=str((summary_payload or {}).get("brief_zh") or "").strip(),
            consistency_review=consistency,
            warnings=tuple(dict.fromkeys(warnings)),
        )


GeoDatasetProfileService = GeoMetadataProfileService


def build_geo_metadata_profile(**kwargs: Any) -> GeoMetadataProfile:
    return GeoMetadataProfileService().build_profile(**kwargs)


def build_geo_dataset_profile(**kwargs: Any) -> GeoMetadataProfile:
    return build_geo_metadata_profile(**kwargs)


@dataclass
class _ParsedGeoMetadata:
    title: str = ""
    summary: str = ""
    overall_design: str = ""
    platform_ids: list[str] = field(default_factory=list)
    organism: str = ""
    sample_records: list[GeoSampleRecord] = field(default_factory=list)
    supplementary_urls: list[str] = field(default_factory=list)
    parsing_warnings: list[str] = field(default_factory=list)
    metadata_source: str = "search_metadata"

    def merge(self, other: "_ParsedGeoMetadata", *, source: str) -> None:
        self.title = self.title or other.title
        self.summary = self.summary or other.summary
        self.overall_design = self.overall_design or other.overall_design
        self.organism = self.organism or other.organism
        self.platform_ids = list(dict.fromkeys([*self.platform_ids, *other.platform_ids]))
        if other.sample_records:
            self.sample_records = other.sample_records
            self.metadata_source = source
        elif self.metadata_source == "search_metadata" and (other.title or other.summary or other.overall_design):
            self.metadata_source = source
        self.supplementary_urls = list(dict.fromkeys([*self.supplementary_urls, *other.supplementary_urls]))
        self.parsing_warnings = [*self.parsing_warnings, *other.parsing_warnings]


def _parse_family_soft(path: Path) -> _ParsedGeoMetadata:
    parsed = _ParsedGeoMetadata()
    current: dict[str, Any] | None = None
    try:
        with _open_text(path) as handle:
            for line in handle:
                stripped = line.strip()
                if not stripped:
                    continue
                if stripped.startswith("^SAMPLE"):
                    if current is not None:
                        parsed.sample_records.append(_sample_record(current))
                    current = {"sample_accession": _value(stripped), "raw_fields": {}}
                    continue
                key, value = _soft_key_value(stripped)
                if not key:
                    continue
                normalized = _normalize_key(key)
                if current is None:
                    if normalized == "series_title":
                        parsed.title = parsed.title or value
                    elif normalized == "series_summary":
                        parsed.summary = _append_text(parsed.summary, value)
                    elif normalized == "series_overall_design":
                        parsed.overall_design = _append_text(parsed.overall_design, value)
                    elif normalized == "series_platform_id":
                        parsed.platform_ids.extend(_split_values(value))
                    elif normalized in {"series_organism", "series_sample_organism"}:
                        parsed.organism = parsed.organism or value
                    elif normalized == "series_supplementary_file":
                        parsed.supplementary_urls.append(value)
                    elif normalized == "series_relation" and _looks_raw_link(value):
                        parsed.supplementary_urls.append(value)
                    continue
                raw_fields = current.setdefault("raw_fields", {})
                if isinstance(raw_fields, dict):
                    raw_fields.setdefault(normalized, [])
                    if isinstance(raw_fields[normalized], list):
                        raw_fields[normalized].append(value)
                if normalized == "sample_geo_accession":
                    current["sample_accession"] = value
                elif normalized == "sample_title":
                    current["sample_title"] = value
                elif normalized == "sample_source_name_ch1":
                    current["source_name_ch1"] = value
                elif normalized == "sample_characteristics_ch1":
                    current.setdefault("characteristics_ch1", []).append(value)
                elif normalized == "sample_description":
                    current["description"] = _append_text(str(current.get("description") or ""), value)
                elif normalized == "sample_treatment_protocol_ch1":
                    current["treatment_protocol_ch1"] = _append_text(str(current.get("treatment_protocol_ch1") or ""), value)
                elif normalized == "sample_extract_protocol_ch1":
                    current["extract_protocol_ch1"] = _append_text(str(current.get("extract_protocol_ch1") or ""), value)
                elif normalized in {"sample_supplementary_file", "sample_relation"} and _looks_raw_link(value):
                    current.setdefault("raw_links", []).append(value)
                    parsed.supplementary_urls.append(value)
            if current is not None:
                parsed.sample_records.append(_sample_record(current))
    except OSError as exc:
        parsed.parsing_warnings.append(f"family_soft_read_failed:{exc}")
    return parsed


def _parse_series_matrix(path: Path) -> _ParsedGeoMetadata:
    parsed = _ParsedGeoMetadata()
    sample_fields: dict[str, list[str]] = {}
    characteristics_by_index: dict[int, list[str]] = {}
    try:
        with _open_text(path) as handle:
            for line in handle:
                stripped = line.strip()
                if not stripped:
                    continue
                if stripped.startswith("!series_matrix_table_begin"):
                    break
                key, values = _series_key_values(stripped)
                normalized = _normalize_key(key)
                if normalized == "series_title":
                    parsed.title = parsed.title or _first_text(*values)
                elif normalized == "series_summary":
                    parsed.summary = _append_text(parsed.summary, " ".join(values))
                elif normalized == "series_overall_design":
                    parsed.overall_design = _append_text(parsed.overall_design, " ".join(values))
                elif normalized == "series_platform_id":
                    parsed.platform_ids.extend(values)
                elif normalized in {"series_organism", "series_sample_organism"}:
                    parsed.organism = parsed.organism or _first_text(*values)
                elif normalized == "sample_characteristics_ch1":
                    for index, value in enumerate(values):
                        if value:
                            characteristics_by_index.setdefault(index, []).append(value)
                elif normalized.startswith("sample_"):
                    sample_fields.setdefault(normalized, []).extend(values)
    except OSError as exc:
        parsed.parsing_warnings.append(f"series_matrix_read_failed:{exc}")
        return parsed
    sample_ids = sample_fields.get("sample_geo_accession", [])
    sample_titles = sample_fields.get("sample_title", [])
    count = len(sample_ids) or len(sample_titles) or max(
        (len(values) for values in [*sample_fields.values(), *characteristics_by_index.values()]),
        default=0,
    )
    records: list[GeoSampleRecord] = []
    for index in range(count):
        raw_fields = {
            key: values[index]
            for key, values in sample_fields.items()
            if index < len(values) and values[index]
        }
        if characteristics_by_index.get(index):
            raw_fields["sample_characteristics_ch1"] = list(characteristics_by_index[index])
        records.append(
            GeoSampleRecord(
                sample_accession=sample_ids[index] if index < len(sample_ids) else "",
                sample_title=_indexed(sample_fields, "sample_title", index),
                source_name_ch1=_indexed(sample_fields, "sample_source_name_ch1", index),
                characteristics_ch1=tuple(characteristics_by_index.get(index, [])),
                description=_indexed(sample_fields, "sample_description", index),
                treatment_protocol_ch1=_indexed(sample_fields, "sample_treatment_protocol_ch1", index),
                extract_protocol_ch1=_indexed(sample_fields, "sample_extract_protocol_ch1", index),
                raw_fields=raw_fields,
            )
        )
    parsed.sample_records = records
    return parsed


def _candidate_comparisons(
    sample_records: tuple[GeoSampleRecord, ...],
    *,
    summary: str,
    overall_design: str,
) -> list[GeoCandidateComparison]:
    field_assignments: dict[str, list[GeoSampleGroupAssignment]] = {}
    for sample in sample_records:
        sample_id = sample.sample_accession or sample.sample_title
        if not sample_id:
            continue
        for field, text, confidence in (
            ("sample_title", sample.sample_title, "medium"),
            ("source_name_ch1", sample.source_name_ch1, "medium"),
            ("description", sample.description, "medium"),
            ("treatment_protocol_ch1", sample.treatment_protocol_ch1, "low"),
        ):
            group = _group_label_from_text(text)
            if group:
                field_assignments.setdefault(field, []).append(
                    GeoSampleGroupAssignment(sample_id, group, field, str(text), confidence)
                )
        for characteristic in sample.characteristics_ch1:
            parsed_field, value = _parse_characteristic(characteristic)
            field = parsed_field or "characteristics_ch1"
            if _excluded_field(field):
                continue
            group = _group_label_from_text(value or characteristic)
            if group:
                field_assignments.setdefault(field, []).append(
                    GeoSampleGroupAssignment(sample_id, group, field, characteristic, "high")
                )

    comparisons: list[GeoCandidateComparison] = []
    for field, assignments in field_assignments.items():
        by_sample: dict[str, GeoSampleGroupAssignment] = {}
        for assignment in assignments:
            by_sample.setdefault(assignment.sample_accession, assignment)
        sizes = _clean_group_sizes(dict(Counter(item.assigned_group for item in by_sample.values())))
        if not _valid_group_sizes(sizes):
            continue
        clean_assignments = tuple(item for item in by_sample.values() if item.assigned_group in sizes)
        confidence = _field_confidence(field, clean_assignments)
        comparisons.append(
            _comparison_from_assignments(
                field,
                sizes,
                clean_assignments,
                evidence=(f"{field} 中识别到重复分组标签", *_matching_text_evidence(summary, overall_design, sizes)),
                confidence=confidence,
            )
        )

    if not comparisons:
        text_sizes = _group_sizes_from_text(" ".join([overall_design, summary]))
        if text_sizes:
            comparisons.append(
                _comparison_from_assignments(
                    "geo_page_text",
                    text_sizes,
                    (),
                    evidence=("summary/overall design 提及候选比较结构，仅作为辅助证据。",),
                    confidence="low",
                    warnings=("未解析到逐样本证据，不能直接确认为正式比较组。",),
                )
            )
    return sorted(comparisons, key=lambda item: (_confidence_rank(item.confidence), sum(item.group_sizes.values())), reverse=True)


def _comparison_from_assignments(
    field: str,
    sizes: dict[str, int],
    assignments: tuple[GeoSampleGroupAssignment, ...],
    *,
    evidence: tuple[str, ...],
    confidence: str,
    warnings: tuple[str, ...] = (),
) -> GeoCandidateComparison:
    control = _control_group(sizes)
    case = _case_group(sizes, control)
    label = f"{case} vs {control}" if control and case else "候选分组比较"
    combined_warnings = list(warnings)
    if confidence == "low" and "低置信度分组，只能作为提示。" not in combined_warnings:
        combined_warnings.append("低置信度分组，只能作为提示。")
    return GeoCandidateComparison(
        comparison_id=f"{field}:{_slug(label)}",
        label=label,
        control_group=control,
        case_group=case,
        group_sizes=dict(sorted(sizes.items(), key=lambda item: item[0])),
        sample_assignments=assignments,
        confidence=confidence,
        evidence=evidence,
        warnings=tuple(combined_warnings),
    )


def _sample_structure_preview(
    *,
    geo_sample_count: int | str,
    metadata_sample_count: int,
    comparisons: list[GeoCandidateComparison],
    count_layers: dict[str, object],
) -> dict[str, object]:
    top = comparisons[0] if comparisons else None
    return {
        "geo_sample_count": geo_sample_count,
        "metadata_sample_count": metadata_sample_count,
        "expression_sample_count": count_layers.get("expression_sample_count", 0),
        "matched_sample_count": count_layers.get("matched_sample_count", 0),
        "sample_types": top.group_sizes if top is not None else {},
        "candidate_group_fields": [item.comparison_id.split(":", 1)[0] for item in comparisons],
        "candidate_comparison_count": len(comparisons),
        "confidence": top.confidence if top is not None else "low",
        "evidence": list(top.evidence) if top is not None else [],
        "status": "preview_only" if top is not None else "no_group_detected",
    }


def _analysis_potential(
    *,
    title: str,
    summary: str,
    overall_design: str,
    organism: str,
    experiment_type: str,
    geo_sample_count: int | str,
    metadata_sample_count: int,
    comparisons: list[GeoCandidateComparison],
    expression_files: tuple[str, ...],
    manifest: dict[str, Any],
) -> tuple[int, str, str]:
    text = " ".join([title, summary, overall_design, experiment_type]).lower()
    score = 0
    reasons: list[str] = []
    unsupported = any(token in text for token in ("single-cell", "single cell", "scrna", "spatial", "methylation", "atac", "chip-seq", "mirna"))
    if any(token in text for token in ("expression", "transcriptome", "microarray", "rna-seq", "rna seq")):
        score += 25
        reasons.append("数据类型可能适合表达分析")
    if organism.lower().startswith("homo sapiens") or "human" in organism.lower():
        score += 15
        reasons.append("样本物种为人类或疑似人类")
    if comparisons and comparisons[0].sample_assignments:
        score += 25
        reasons.append(f"sample-level metadata 支持候选分组：{comparisons[0].label}")
    elif comparisons:
        score += 8
        reasons.append("仅从 summary/overall design 发现辅助分组线索")
    if expression_files or _manifest_has_expression_candidate(manifest):
        score += 20
        reasons.append("发现可能的表达矩阵文件")
    count = max(_int_or_zero(geo_sample_count), metadata_sample_count)
    if count >= 6:
        score += 10
        reasons.append(f"元数据样本数为 {count}")
    if unsupported:
        score -= 45
        reasons.append("数据类型可能不是常规 bulk expression")
    if comparisons and not any(item.sample_assignments for item in comparisons):
        score = min(score, 65)
        reasons.append("分组线索未达到 sample-level 证据，分析潜力不标为高")
    score = max(0, min(100, score))
    if unsupported and score < 50:
        level = "不建议"
    elif score >= 75:
        level = "高"
    elif score >= 50:
        level = "中"
    elif score >= 25:
        level = "低"
    else:
        level = "不建议"
    return score, level, "；".join(reasons) or "结构化元数据不足，需人工查看后再决定是否下载。"


def _analysis_availability(
    *,
    experiment_type: str,
    comparisons: list[GeoCandidateComparison],
    recognition_report: dict[str, Any] | None,
    count_layers: dict[str, object],
) -> tuple[str, tuple[str, ...]]:
    if recognition_report is None:
        return "", ()
    warnings: list[str] = []
    if any(token in experiment_type.lower() for token in ("single-cell", "scrna", "methylation", "atac", "chip")):
        return "数据类型不支持", ("当前数据类型不适合常规 bulk 差异表达流程。",)
    expression_count = int(count_layers.get("expression_sample_count") or 0)
    if expression_count <= 0:
        return "缺表达矩阵", ("已下载文件中尚未识别到表达矩阵样本列。",)
    if count_layers.get("sample_id_match_status") == "mismatch":
        return "样本无法匹配", ("表达矩阵列名与样本注释 ID 未匹配。",)
    confirmed = _recognition_has_comparison_config(recognition_report)
    if confirmed:
        return "可运行", ()
    if comparisons:
        return "需要确认比较组", ("已检测到候选分组，但尚未确认比较组。",)
    warnings.append("未识别到候选分组，请手动设置比较组。")
    return "暂不建议", tuple(warnings)


def _count_layers(
    *,
    geo_sample_count: int | str,
    metadata_sample_count: int,
    sample_records: tuple[GeoSampleRecord, ...],
    recognition_report: dict[str, Any] | None,
) -> dict[str, object]:
    result: dict[str, object] = {
        "geo_sample_count": geo_sample_count,
        "metadata_sample_count": metadata_sample_count,
        "expression_sample_count": 0,
        "matched_sample_count": 0,
        "unmatched_metadata_samples": (),
        "unmatched_expression_samples": (),
        "sample_id_match_status": "not_checked",
    }
    if not recognition_report:
        return result
    group_preview = recognition_report.get("group_preview") if isinstance(recognition_report, dict) else {}
    if isinstance(group_preview, dict):
        result["expression_sample_count"] = _int_or_zero(group_preview.get("expression_sample_count"))
        result["metadata_sample_count"] = max(metadata_sample_count, _int_or_zero(group_preview.get("metadata_sample_count")))
        result["sample_id_match_status"] = str(group_preview.get("sample_id_match_status") or "not_available")
        if result["sample_id_match_status"] == "matched":
            result["matched_sample_count"] = min(int(result["expression_sample_count"]), int(result["metadata_sample_count"]))
    expression_samples = _expression_samples_from_report(recognition_report)
    metadata_samples = {record.sample_accession.upper() for record in sample_records if record.sample_accession}
    if expression_samples:
        result["expression_sample_count"] = max(int(result["expression_sample_count"]), len(expression_samples))
    if metadata_samples and expression_samples:
        matched = metadata_samples & expression_samples
        result["matched_sample_count"] = len(matched)
        result["unmatched_metadata_samples"] = tuple(sorted(metadata_samples - expression_samples))
        result["unmatched_expression_samples"] = tuple(sorted(expression_samples - metadata_samples))
        result["sample_id_match_status"] = "matched" if not result["unmatched_metadata_samples"] and not result["unmatched_expression_samples"] else ("partial" if matched else "mismatch")
    return result


def _consistency_review(
    *,
    metadata_sample_count: int,
    geo_sample_count: int | str,
    platform_ids: tuple[str, ...],
    experiment_type: str,
    comparisons: list[GeoCandidateComparison],
    recognition_report: dict[str, Any] | None,
    count_layers: dict[str, object],
) -> dict[str, object]:
    if not recognition_report:
        return {"status": "not_checked", "warnings": []}
    warnings: list[str] = []
    expression_count = int(count_layers.get("expression_sample_count") or 0)
    if metadata_sample_count and expression_count and metadata_sample_count != expression_count:
        warnings.append(f"样本注释数 {metadata_sample_count} 与表达矩阵样本列数 {expression_count} 不一致。")
    if count_layers.get("sample_id_match_status") == "mismatch":
        warnings.append("样本注释 ID 与表达矩阵列名无法匹配。")
    group_preview = recognition_report.get("group_preview") if isinstance(recognition_report, dict) else {}
    if isinstance(group_preview, dict) and comparisons and group_preview.get("group_sizes"):
        if dict(comparisons[0].group_sizes) != dict(group_preview.get("group_sizes") or {}):
            warnings.append("GEO metadata 候选分组与文件内识别分组不一致。")
    files = recognition_report.get("files") if isinstance(recognition_report, dict) else []
    if isinstance(files, list) and platform_ids:
        seen_platforms = {
            str(asset.get("platform_id") or "")
            for record in files
            if isinstance(record, dict)
            for asset in record.get("detected_assets", []) or []
            if isinstance(asset, dict) and asset.get("platform_id")
        }
        if seen_platforms and set(platform_ids).isdisjoint(seen_platforms):
            warnings.append("GEO metadata 平台 GPL 与文件识别平台提示不一致。")
    return {
        "status": "needs_review" if warnings else "consistent",
        "warnings": warnings,
        "geo_sample_count": geo_sample_count,
        "metadata_sample_count": metadata_sample_count,
        "expression_sample_count": expression_count,
        "page_experiment_type": experiment_type,
    }


def _supplementary_files(urls: list[str], manifest: dict[str, Any]) -> list[GeoSupplementaryFile]:
    files: list[GeoSupplementaryFile] = []
    for item in manifest.get("assets", []) or []:
        if not isinstance(item, dict):
            continue
        if item.get("asset_type") not in {"series_matrix", "supplementary_file", "family_soft"}:
            continue
        files.append(_supplementary_preview_from_values(
            file_name=str(item.get("file_name") or Path(str(item.get("remote_url") or "")).name),
            remote_url=str(item.get("remote_url") or ""),
            asset_type=str(item.get("asset_type") or ""),
            role=str(item.get("role") or ""),
            status=str(item.get("status") or ""),
            local_path=str(item.get("local_path") or ""),
            file_size=_int_or_none(item.get("size_bytes") or item.get("file_size")),
            description=str(item.get("description") or ""),
        ))
    known_urls = {item.remote_url for item in files if item.remote_url}
    for url in urls:
        if url and url not in known_urls:
            files.append(_supplementary_preview_from_values(
                file_name=Path(url).name or url,
                remote_url=url,
                asset_type="supplementary_file",
                role=_role_from_name(url),
                status="remote_discovered",
                local_path="",
                file_size=None,
                description="",
            ))
    return files


def _supplementary_preview_from_values(
    *,
    file_name: str,
    remote_url: str,
    asset_type: str,
    role: str,
    status: str,
    local_path: str,
    file_size: int | None,
    description: str,
) -> GeoSupplementaryFile:
    text = " ".join([file_name, role, asset_type, description]).lower()
    if asset_type == "family_soft":
        predicted = "metadata_container"
        priority = "中"
        should_default_select = True
        recommendation = "元数据容器，用于读取标题、样本和平台信息。"
        reason = "family SOFT 是 GEO 元数据容器。"
    elif _is_raw_or_heavy_supplement(text, file_name):
        predicted = "raw_data"
        priority = "不建议"
        should_default_select = False
        recommendation = "可能是原始数据，文件较大，建议确认后下载。"
        reason = "文件名或链接提示 raw/SRA/FASTQ/CEL。"
    elif _looks_like_differential_result(text, file_name):
        predicted = "differential_result_table"
        priority = "低"
        should_default_select = False
        recommendation = "看起来是已发表差异结果表，不作为表达矩阵默认下载。"
        reason = "文件名提示 differential/diffexpr/DE results。"
    elif asset_type == "series_matrix" or _looks_like_expression_supplement(text, file_name):
        predicted = "expression_matrix"
        priority = "中" if asset_type == "series_matrix" else "高"
        should_default_select = asset_type != "series_matrix"
        recommendation = "建议优先查看，可能包含表达矩阵。"
        reason = "文件名或角色包含 count/TPM/FPKM/normalized/expression/matrix 等关键词。"
    elif any(token in text for token in ("sample", "clinical", "phenotype", "metadata", "group")):
        predicted = "sample_metadata"
        priority = "中"
        should_default_select = False
        recommendation = "建议查看，可能包含样本或分组信息。"
        reason = "文件名或角色包含 sample/clinical/metadata 等关键词。"
    elif any(token in text for token in ("annotation", "annot", "platform", "probe", "gene")):
        predicted = "platform_annotation"
        priority = "中"
        should_default_select = False
        recommendation = "可作为基因或平台注释参考。"
        reason = "文件名或角色包含 annotation/platform/probe/gene 等关键词。"
    else:
        predicted = "unknown"
        priority = "低"
        should_default_select = False
        recommendation = "按需查看。"
        reason = "仅能根据文件名轻量预览，类型不明确。"
    risk = "低"
    lowered_name = file_name.lower()
    if predicted == "raw_data" or any(lowered_name.endswith(suffix) for suffix in (".tar", ".tar.gz", ".tgz", ".zip")):
        risk = "中"
        if priority != "不建议":
            priority = "低"
        should_default_select = False
    if file_size is not None and file_size > 500 * 1024 * 1024:
        risk = "高"
        priority = "不建议"
        should_default_select = False
        recommendation = "文件较大，建议确认后下载。"
    return GeoSupplementaryFile(
        file_name=file_name,
        file_size=file_size,
        predicted_type=predicted,
        download_priority=priority,
        should_default_select=should_default_select,
        recommendation=recommendation,
        recommendation_reason=reason,
        risk_level=risk,
        reason=reason,
        remote_url=remote_url,
        asset_type=asset_type,
        role=role,
        status=status,
        local_path=local_path,
        description=description,
    )


def _possible_files(files: list[GeoSupplementaryFile], *, predicted_types: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(item.file_name for item in files if item.predicted_type in predicted_types))


def _suggested_download_files(files: list[GeoSupplementaryFile]) -> tuple[str, ...]:
    prioritized = [
        item.file_name
        for item in files
        if item.asset_type != "family_soft"
        and item.status != "downloaded"
        and item.should_default_select
        and item.download_priority == "高"
        and item.risk_level not in {"高", "中"}
    ]
    if not prioritized:
        prioritized = [
            item.file_name
            for item in files
            if item.asset_type != "family_soft"
            and item.status != "downloaded"
            and item.download_priority in {"高", "中"}
            and item.predicted_type in {"expression_matrix", "sample_metadata", "platform_annotation"}
            and item.risk_level != "高"
        ]
    return tuple(dict.fromkeys(prioritized[:6]))


def _load_asset_manifest(root: Path | None, accession: str) -> dict[str, Any] | None:
    if root is None:
        return None
    geo_dir = root / "raw_data" / "geo" / accession
    candidates = [geo_dir / f"{accession}_asset_manifest.json"]
    if geo_dir.exists():
        candidates.extend(sorted(geo_dir.glob("*_asset_manifest.json")))
    for path in candidates:
        try:
            if path.is_file():
                return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
    return None


def _family_soft_path(root: Path | None, accession: str) -> Path | None:
    if root is None:
        return None
    geo_dir = root / "raw_data" / "geo" / accession
    for path in (geo_dir / f"{accession}_family.soft.gz", geo_dir / f"{accession}_family.soft"):
        if path.is_file():
            return path
    return None


def _asset_local_path(manifest: dict[str, Any], asset_type: str) -> Path | None:
    for item in manifest.get("assets", []) or []:
        if not isinstance(item, dict) or item.get("asset_type") != asset_type:
            continue
        path = _resolve_existing_path(item.get("local_path"))
        if path is not None:
            return path
    return None


def _resolve_existing_path(value: object) -> Path | None:
    if not value:
        return None
    path = Path(str(value)).expanduser()
    return path.resolve() if path.is_file() else None


def _sample_record(payload: dict[str, Any]) -> GeoSampleRecord:
    raw_fields = payload.get("raw_fields")
    raw = raw_fields if isinstance(raw_fields, dict) else {}
    if payload.get("raw_links"):
        raw = {**raw, "raw_links": list(payload.get("raw_links") or [])}
    return GeoSampleRecord(
        sample_accession=str(payload.get("sample_accession") or ""),
        sample_title=str(payload.get("sample_title") or ""),
        source_name_ch1=str(payload.get("source_name_ch1") or ""),
        characteristics_ch1=tuple(str(item) for item in payload.get("characteristics_ch1", []) if str(item).strip()),
        description=str(payload.get("description") or ""),
        treatment_protocol_ch1=str(payload.get("treatment_protocol_ch1") or ""),
        extract_protocol_ch1=str(payload.get("extract_protocol_ch1") or ""),
        raw_fields=raw,
    )


def _expression_samples_from_report(report: dict[str, Any]) -> set[str]:
    samples: set[str] = set()
    for record in report.get("files", []) if isinstance(report, dict) else []:
        if not isinstance(record, dict):
            continue
        profile = record.get("content_profile")
        if isinstance(profile, dict):
            for key in ("sample_columns", "sample_ids", "expression_samples"):
                value = profile.get(key)
                if isinstance(value, list):
                    samples.update(str(item).upper() for item in value if str(item).strip())
        for asset in record.get("detected_assets", []) or []:
            if isinstance(asset, dict):
                value = asset.get("sample_columns") or asset.get("sample_ids")
                if isinstance(value, list):
                    samples.update(str(item).upper() for item in value if str(item).strip())
    return samples


def _recognition_has_comparison_config(report: dict[str, Any]) -> bool:
    group_preview = report.get("group_preview") if isinstance(report, dict) else {}
    if isinstance(group_preview, dict) and group_preview.get("status") == "confirmed_comparison_exists":
        return True
    for record in report.get("files", []) if isinstance(report, dict) else []:
        if not isinstance(record, dict):
            continue
        roles = {str(role) for role in record.get("recognized_roles", []) or []}
        if record.get("recognized_type") == "comparison_config" or "comparison_config" in roles:
            return True
    return False


def _field_confidence(field: str, assignments: tuple[GeoSampleGroupAssignment, ...]) -> str:
    labels = [item.assigned_group for item in assignments]
    if not _has_explicit_design_labels(labels) or any(_is_low_confidence_group_label(label) for label in labels):
        return "low"
    if not _has_clear_experimental_pair(set(labels)):
        return "low" if field in {"sample_title", "source_name_ch1", "description"} else "medium"
    sizes = Counter(labels)
    total = sum(sizes.values())
    if any(value < 2 for value in sizes.values()) and total > 4:
        return "low"
    if field in {"sample_title", "source_name_ch1", "description"}:
        return "medium"
    if field.endswith("protocol_ch1"):
        return "low"
    if assignments and all(item.confidence == "high" for item in assignments):
        return "high"
    return "medium"


def _matching_text_evidence(summary: str, overall_design: str, sizes: dict[str, int]) -> tuple[str, ...]:
    text = " ".join([summary, overall_design]).lower()
    if not text:
        return ()
    groups = [group.replace("_", " ") for group in sizes]
    matched = [group for group in groups if group in text]
    return ("summary/overall design 支持这些组别：" + ", ".join(matched),) if len(matched) >= 2 else ()


def _group_sizes_from_text(text: str) -> dict[str, int]:
    lowered = text.lower()
    labels = []
    for token in ("adjacent normal", "normal", "control", "vehicle", "untreated", "tumor", "tumour", "cancer", "carcinoma", "treated", "resistant", "sensitive", "mutated", "mutant", "wild type", "wt", "metastatic", "primary"):
        if token in lowered:
            labels.append(_canonical_group(token))
    labels = list(dict.fromkeys(label for label in labels if label))
    if len(labels) < 2:
        return {}
    sizes: dict[str, int] = {}
    for label in labels:
        size = _number_near_label(lowered, label)
        sizes[label] = size if size > 0 else 1
    sizes = _clean_group_sizes(sizes)
    return sizes if _valid_group_sizes(sizes) else {}


def _group_label_from_text(text: object) -> str:
    lowered = str(text or "").lower()
    if not lowered or _looks_like_accession_or_technical_label(lowered):
        return ""
    if _contains_only_cell_line_or_technical_context(lowered):
        return ""
    for phrase in (
        "adjacent normal",
        "para-cancer",
        "normal",
        "dmso",
        "mock",
        "vehicle",
        "untreated",
        "control",
        "resistant",
        "sensitive",
        "treated",
        "treatment",
        "wild type",
        "wt",
        "mutated",
        "mutant",
        "knockout",
        "metastatic",
        "recurrent",
        "primary",
        "tumour",
        "tumor",
        "malignant",
        "cancer",
        "carcinoma",
        "benign",
    ):
        if phrase in lowered:
            return _canonical_group(phrase)
    return ""


def _canonical_group(token: str) -> str:
    token = token.lower().strip()
    mapping = {
        "adjacent normal": "normal",
        "para-cancer": "normal",
        "dmso": "control",
        "mock": "control",
        "vehicle": "control",
        "untreated": "control",
        "treatment": "treated",
        "tumour": "tumor",
        "cancer": "tumor",
        "carcinoma": "tumor",
        "malignant": "tumor",
        "wild type": "wild_type",
        "wt": "wild_type",
        "mutated": "mutant",
    }
    return mapping.get(token, token.replace(" ", "_"))


def _parse_characteristic(text: str) -> tuple[str, str]:
    label, sep, value = str(text).partition(":")
    if not sep:
        return "", str(text).strip()
    return _normalize_key(label), value.strip()


def _excluded_field(field: str) -> bool:
    return field in {
        "sample",
        "sample_id",
        "geo_accession",
        "gsm",
        "batch",
        "platform",
        "barcode",
        "file",
        "filename",
        "replicate",
        "run_accession",
        "library_strategy",
        "sex",
        "gender",
        "age",
    }


def _valid_group_sizes(sizes: dict[str, int]) -> bool:
    clean = {
        key: int(value)
        for key, value in sizes.items()
        if key and int(value) > 0 and not _is_invalid_group_label(key)
    }
    if not (2 <= len(clean) <= 8):
        return False
    if not _has_explicit_design_labels(clean):
        return False
    return True


def _clean_group_sizes(sizes: dict[str, int]) -> dict[str, int]:
    return {
        str(key): int(value)
        for key, value in sizes.items()
        if str(key).strip() and int(value) > 0 and not _is_invalid_group_label(str(key))
    }


def _has_explicit_design_labels(labels: Iterable[str] | dict[str, int]) -> bool:
    values = labels.keys() if isinstance(labels, dict) else labels
    canonical = {_canonical_group(str(label)) for label in values}
    return bool(canonical & EXPLICIT_DESIGN_GROUPS)


def _has_clear_experimental_pair(labels: set[str]) -> bool:
    canonical = {_canonical_group(label) for label in labels}
    pairs = (
        {"tumor", "normal"},
        {"treated", "control"},
        {"resistant", "sensitive"},
        {"mutant", "wild_type"},
        {"malignant", "benign"},
        {"tumor", "benign"},
        {"metastatic", "primary"},
    )
    return any(pair <= canonical for pair in pairs)


def _is_invalid_group_label(label: str) -> bool:
    lowered = str(label or "").strip().lower()
    if not lowered:
        return True
    return (
        _looks_like_accession_or_technical_label(lowered)
        or _is_cell_line_label(lowered)
        or _is_numeric_dose_or_time_label(lowered)
        or _is_replicate_or_batch_label(lowered)
    )


def _is_low_confidence_group_label(label: str) -> bool:
    lowered = str(label or "").strip().lower()
    return (
        _is_invalid_group_label(lowered)
        or _contains_cell_line(lowered)
        or _is_numeric_dose_or_time_label(lowered)
        or _is_replicate_or_batch_label(lowered)
    )


def _contains_only_cell_line_or_technical_context(text: str) -> bool:
    cleaned = _normalize_group_text(text)
    if not cleaned:
        return True
    has_semantic = any(_token_in_text(token, cleaned) for token in ("normal", "control", "vehicle", "dmso", "mock", "untreated", "treated", "treatment", "tumor", "tumour", "cancer", "carcinoma", "resistant", "sensitive", "mutant", "wild type", "wt", "metastatic", "primary", "benign", "malignant"))
    if has_semantic:
        return False
    return _contains_cell_line(cleaned) or _is_numeric_dose_or_time_label(cleaned) or _is_replicate_or_batch_label(cleaned)


def _looks_like_accession_or_technical_label(text: str) -> bool:
    value = text.strip()
    if re.fullmatch(r"(gsm|gse|gpl|srr|srx|srs|err|drx)\w+", value, flags=re.IGNORECASE):
        return True
    return any(_token_in_text(token, value) for token in ("batch", "lane", "run", "library", "barcode", "platform"))


def _contains_cell_line(text: str) -> bool:
    normalized = _normalize_group_text(text)
    compact = normalized.replace("-", "").replace("_", "").replace(" ", "")
    for pattern in CELL_LINE_PATTERNS:
        pattern_compact = pattern.replace("-", "").replace("_", "").replace(" ", "")
        if re.search(rf"(^|[^a-z0-9]){re.escape(pattern)}([^a-z0-9]|$)", normalized) or pattern_compact in compact:
            return True
    return False


def _is_cell_line_label(text: str) -> bool:
    normalized = _normalize_group_text(text)
    if not _contains_cell_line(normalized):
        return False
    stripped = _strip_cell_line_tokens(normalized)
    stripped = re.sub(r"\b(cell|cells|cell line|line)\b", " ", stripped)
    stripped = re.sub(r"\s+", " ", stripped).strip()
    return not stripped


def _strip_cell_line_tokens(text: str) -> str:
    cleaned = _normalize_group_text(text)
    for pattern in CELL_LINE_PATTERNS:
        cleaned = re.sub(rf"(^|[^a-z0-9]){re.escape(pattern)}([^a-z0-9]|$)", " ", cleaned)
        cleaned = cleaned.replace(pattern.replace("-", ""), " ")
    return re.sub(r"\s+", " ", cleaned).strip()


def _is_numeric_dose_or_time_label(text: str) -> bool:
    value = text.strip().lower().replace("μ", "u")
    if re.fullmatch(r"\d+(?:\.\d+)?", value):
        return True
    if re.fullmatch(r"\d+(?:\.\d+)?\s*(nm|um|mm|µm|ug/ml|mg/ml|mg/kg|h|hr|hrs|hour|hours|day|days|week|weeks)", value):
        return True
    if re.search(r"\b\d+(?:\.\d+)?\s*(nm|um|mm|µm|mg/kg|h|hr|hrs|hours|day|week)\b", value):
        semantic = any(_token_in_text(token, value) for token in ("control", "vehicle", "dmso", "mock", "treated", "treatment", "resistant", "sensitive", "tumor", "normal"))
        return not semantic
    return False


def _is_replicate_or_batch_label(text: str) -> bool:
    value = text.strip().lower()
    if re.fullmatch(r"(rep|replicate|biological replicate)[ _.-]?\d+", value):
        return True
    return any(_token_in_text(token, value) for token in ("replicate", "biological replicate", "technical replicate", "batch", "lane", "barcode"))


def _token_in_text(token: str, text: str) -> bool:
    return re.search(rf"(^|[^a-z0-9]){re.escape(token.lower())}([^a-z0-9]|$)", text.lower()) is not None


def _normalize_group_text(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "").lower().replace("_", " ").strip())


def _control_group(sizes: dict[str, int]) -> str:
    for value in ("normal", "control", "untreated", "vehicle", "wild_type", "sensitive", "baseline", "benign", "primary"):
        if value in sizes:
            return value
    return sorted(sizes, key=lambda key: (-sizes[key], key))[0] if sizes else ""


def _case_group(sizes: dict[str, int], control: str) -> str:
    for value in ("tumor", "treated", "resistant", "mutant", "metastatic", "recurrent", "malignant"):
        if value in sizes and value != control:
            return value
    for value in sorted(sizes, key=lambda key: (-sizes[key], key)):
        if value != control:
            return value
    return ""


def _confidence_rank(value: str) -> int:
    return {"high": 3, "medium": 2, "low": 1}.get(value, 0)


def _number_near_label(text: str, label: str) -> int:
    label_text = label.replace("_", " ")
    patterns = (
        rf"(?<![A-Za-z0-9])(\d+)(?![A-Za-z0-9])\s+(?:\w+\s+){{0,3}}{re.escape(label_text)}",
        rf"{re.escape(label_text)}(?:\s+\w+){{0,3}}\s+(?<![A-Za-z0-9])(\d+)(?![A-Za-z0-9])",
    )
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            if _number_has_dose_or_time_unit(text, match.group(1)):
                continue
            return int(match.group(1))
    return 0


def _number_has_dose_or_time_unit(text: str, number: str) -> bool:
    return (
        re.search(
            rf"\b{re.escape(number)}\s*(?:nm|um|µm|mm|mg/kg|ug/ml|mg/ml|h|hr|hrs|hour|hours|day|days|week|weeks)\b",
            text,
            flags=re.IGNORECASE,
        )
        is not None
    )


def _sample_count(records: tuple[GeoSampleRecord, ...], fallback: object) -> int | str:
    if records:
        return len(records)
    value = _int_or_zero(fallback)
    return value if value else (str(fallback) if fallback not in (None, "") else "")


def _int_or_zero(value: object) -> int:
    try:
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        match = re.search(r"\d+", str(value or ""))
        return int(match.group(0)) if match else 0


def _int_or_none(value: object) -> int | None:
    try:
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


def _infer_experiment_type(*values: object) -> str:
    text = " ".join(str(value or "") for value in values).lower()
    if "single-cell" in text or "single cell" in text or "scrna" in text:
        return "single-cell RNA-seq"
    if "methylation" in text:
        return "methylation"
    if "atac" in text:
        return "ATAC-seq"
    if "rna-seq" in text or "rna seq" in text or "transcriptome" in text:
        return "RNA-seq / transcriptome"
    if "microarray" in text or "gpl" in text:
        return "microarray / expression profiling"
    if "expression" in text:
        return "expression profiling"
    return _first_text(*values)


def _manifest_has_expression_candidate(manifest: dict[str, Any]) -> bool:
    summary = manifest.get("summary") if isinstance(manifest, dict) else {}
    return bool(isinstance(summary, dict) and (summary.get("expression_candidate_count") or summary.get("series_matrix_discovered")))


def _looks_like_expression_supplement(text: str, file_name: str) -> bool:
    lowered = " ".join([text, file_name]).lower()
    expression_tokens = (
        "raw_counts",
        "readcount",
        "read_count",
        "gene_counts",
        "gene count",
        "gene_expression",
        "gene expression",
        "normalized",
        "expression",
        "expr",
        "matrix",
        "counts",
        "count",
        "tpm",
        "fpkm",
        "rpkm",
    )
    extension_ok = lowered.endswith((".txt", ".tsv", ".csv", ".xlsx", ".txt.gz", ".tsv.gz", ".csv.gz"))
    return extension_ok and any(token in lowered for token in expression_tokens)


def _looks_like_differential_result(text: str, file_name: str) -> bool:
    lowered = " ".join([text, file_name]).lower()
    return any(token in lowered for token in ("diffexpr", "diff_expr", "differential", "deg", "de_results", "de-result", "de_result"))


def _is_raw_or_heavy_supplement(text: str, file_name: str) -> bool:
    lowered = " ".join([text, file_name]).lower()
    raw_tokens = (
        "fastq",
        ".fq",
        ".bam",
        ".cram",
        ".sra",
        ".cel",
        " cel",
        "_raw.tar",
        "raw.tar",
        ".tar.gz",
        ".tgz",
        "image",
        ".pdf",
    )
    return any(token in lowered for token in raw_tokens)


def _role_from_name(name: str) -> str:
    lowered = name.lower()
    if any(token in lowered for token in ("series_matrix", "expression", "matrix", "count", "counts", "cpm", "fpkm", "tpm", "normalized")):
        return "supplementary_expression_candidate"
    if any(token in lowered for token in ("sample", "clinical", "phenotype", "metadata", "group")):
        return "supplementary_sample_metadata_candidate"
    if any(token in lowered for token in ("annotation", "annot", "platform", "probe", "gene")):
        return "supplementary_annotation_candidate"
    if any(token in lowered for token in ("fastq", "sra", "raw", "cel")):
        return "raw_data_candidate"
    return "supplementary_file"


def _looks_raw_link(value: str) -> bool:
    lowered = value.lower()
    return any(token in lowered for token in ("sra", "fastq", "raw", "ftp", "supplementary"))


def _split_values(value: str) -> list[str]:
    return [part.strip() for part in re.split(r"[;,]\s*", str(value)) if part.strip()]


def _indexed(values: dict[str, list[str]], key: str, index: int) -> str:
    items = values.get(key, [])
    return items[index] if index < len(items) else ""


def _append_text(existing: str, value: str) -> str:
    value = str(value or "").strip()
    if not value:
        return existing
    return f"{existing} {value}".strip() if existing else value


def _first_text(*values: object) -> str:
    for value in values:
        if isinstance(value, (list, tuple)):
            text = ", ".join(str(item).strip() for item in value if str(item).strip())
        else:
            text = str(value or "").strip()
        if text:
            return text
    return ""


def _as_text_list(value: object) -> list[str]:
    if isinstance(value, (list, tuple, set)):
        return [str(item).strip() for item in value if str(item).strip()]
    if value:
        return _split_values(str(value))
    return []


def _value(line: str) -> str:
    return line.partition("=")[2].strip()


def _normalize_key(value: object) -> str:
    return re.sub(r"_+", "_", "".join(character.lower() if character.isalnum() else "_" for character in str(value))).strip("_")


def _normalize_gse(accession: str) -> str:
    text = str(accession or "").strip().upper()
    match = re.search(r"GSE\d+", text)
    return match.group(0) if match else text


def _slug(value: str) -> str:
    return re.sub(r"_+", "_", "".join(character.lower() if character.isalnum() else "_" for character in value)).strip("_") or "comparison"


def _open_text(path: Path):
    return gzip.open(path, "rt", encoding="utf-8", errors="ignore") if path.name.lower().endswith(".gz") else path.open("r", encoding="utf-8", errors="ignore")


def _soft_key_value(line: str) -> tuple[str, str]:
    key, sep, value = line.partition("=")
    return (key.strip().lstrip("!"), value.strip()) if sep else ("", "")


def _series_key_values(line: str) -> tuple[str, list[str]]:
    if "\t" in line:
        cells = [cell.strip().strip('"') for cell in line.split("\t")]
        return cells[0].lstrip("!"), [cell for cell in cells[1:] if cell]
    key, value = _soft_key_value(line)
    return key, [value] if value else []
