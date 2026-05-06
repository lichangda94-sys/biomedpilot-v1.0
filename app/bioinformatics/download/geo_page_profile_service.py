from __future__ import annotations

import gzip
import json
import re
from collections import Counter
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class GeoSampleRecord:
    accession: str = ""
    title: str = ""
    source_name_ch1: str = ""
    characteristics_ch1: tuple[str, ...] = ()
    description: str = ""
    raw_links: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class GeoSupplementaryFile:
    file_name: str
    remote_url: str = ""
    asset_type: str = ""
    role: str = ""
    status: str = ""
    local_path: str = ""
    recommendation: str = ""

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class GeoCandidateComparison:
    comparison_id: str
    label: str
    control_group: str
    case_group: str
    group_sizes: dict[str, int]
    sample_assignments: dict[str, str] = field(default_factory=dict)
    confidence: str = "low"
    evidence: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    requires_user_confirmation: bool = True

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class GeoDatasetProfile:
    accession: str
    title: str = ""
    summary: str = ""
    overall_design: str = ""
    platform_ids: tuple[str, ...] = ()
    organism: str = ""
    experiment_type: str = ""
    sample_count: int | str = ""
    sample_records: tuple[GeoSampleRecord, ...] = ()
    supplementary_files: tuple[GeoSupplementaryFile, ...] = ()
    possible_expression_files: tuple[str, ...] = ()
    possible_annotation_files: tuple[str, ...] = ()
    possible_raw_files: tuple[str, ...] = ()
    sample_structure_preview: dict[str, object] = field(default_factory=dict)
    candidate_comparisons: tuple[GeoCandidateComparison, ...] = ()
    analysis_ready_score: int = 0
    recommendation_level: str = "低"
    recommendation_reason: str = ""
    suggested_download_files: tuple[str, ...] = ()
    chinese_title: str = ""
    chinese_summary: str = ""
    chinese_brief: str = ""
    consistency_review: dict[str, object] = field(default_factory=dict)
    warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["sample_records"] = [item.to_dict() for item in self.sample_records]
        payload["supplementary_files"] = [item.to_dict() for item in self.supplementary_files]
        payload["candidate_comparisons"] = [item.to_dict() for item in self.candidate_comparisons]
        return payload


class GeoDatasetProfileService:
    """Build a conservative GEO/GSE page-level profile for UI decision support."""

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
    ) -> GeoDatasetProfile:
        normalized = _normalize_gse(accession)
        metadata = candidate_metadata or {}
        root = Path(project_root).expanduser().resolve() if project_root is not None else None
        manifest = asset_manifest or _load_asset_manifest(root, normalized) or {}
        family_path = _resolve_existing_path(family_soft_path) or _family_soft_path(root, normalized) or _asset_local_path(manifest, "family_soft")
        series_path = _resolve_existing_path(series_matrix_path) or _asset_local_path(manifest, "series_matrix")

        parsed = _ParsedGeoMetadata()
        if family_path is not None:
            parsed.merge(_parse_family_soft(family_path))
        if series_path is not None:
            parsed.merge(_parse_series_matrix(series_path))

        title = _first_text(parsed.title, metadata.get("title_en"), metadata.get("title"), metadata.get("display_title"))
        summary = _first_text(parsed.summary, metadata.get("summary_en"), metadata.get("summary"))
        overall_design = _first_text(parsed.overall_design, metadata.get("overall_design_en"), metadata.get("overall_design"))
        platform_ids = tuple(dict.fromkeys([*parsed.platform_ids, *_as_text_list(metadata.get("platform_accessions"))]))
        supplementary = _supplementary_files(parsed.supplementary_urls, manifest)
        sample_records = tuple(parsed.sample_records)
        sample_count = _sample_count(sample_records, metadata.get("sample_count"))
        experiment_type = _infer_experiment_type(title, summary, overall_design, str(metadata.get("data_type") or metadata.get("experiment_type") or ""))

        comparisons = _candidate_comparisons(sample_records, summary=summary, overall_design=overall_design)
        preview = _sample_structure_preview(sample_count, sample_records, comparisons)
        possible_expression_files = _possible_files(supplementary, roles=("expression", "matrix", "count", "cpm", "fpkm", "tpm"))
        possible_annotation_files = _possible_files(supplementary, roles=("annotation", "annot", "platform", "probe", "gene"))
        possible_raw_files = _possible_files(supplementary, roles=("raw", "fastq", "sra", "cel"))
        score, level, reason = _recommendation(
            title=title,
            summary=summary,
            overall_design=overall_design,
            organism=_first_text(parsed.organism, metadata.get("organism")),
            experiment_type=experiment_type,
            sample_count=sample_count,
            comparisons=comparisons,
            expression_files=possible_expression_files,
            manifest=manifest,
        )
        suggested = _suggested_download_files(supplementary, possible_expression_files, possible_annotation_files)
        consistency = _consistency_review(
            sample_count=sample_count,
            platform_ids=platform_ids,
            experiment_type=experiment_type,
            comparisons=comparisons,
            recognition_report=recognition_report,
        )
        warnings = [*parsed.warnings]
        if consistency.get("status") == "needs_review":
            warnings.append("GEO 页面描述与下载文件识别结果不完全一致，请人工确认比较组。")
        if not comparisons:
            warnings.append("未从 GEO 页面或样本信息中识别到明确候选分组。")
        return GeoDatasetProfile(
            accession=normalized,
            title=title,
            summary=summary,
            overall_design=overall_design,
            platform_ids=platform_ids,
            organism=_first_text(parsed.organism, metadata.get("organism")),
            experiment_type=experiment_type,
            sample_count=sample_count,
            sample_records=sample_records,
            supplementary_files=tuple(supplementary),
            possible_expression_files=possible_expression_files,
            possible_annotation_files=possible_annotation_files,
            possible_raw_files=possible_raw_files,
            sample_structure_preview=preview,
            candidate_comparisons=tuple(comparisons),
            analysis_ready_score=score,
            recommendation_level=level,
            recommendation_reason=reason,
            suggested_download_files=suggested,
            chinese_title=str((summary_payload or {}).get("title_zh") or "").strip(),
            chinese_summary=str((summary_payload or {}).get("summary_zh") or "").strip(),
            chinese_brief=str((summary_payload or {}).get("brief_zh") or "").strip(),
            consistency_review=consistency,
            warnings=tuple(dict.fromkeys(warnings)),
        )


def build_geo_dataset_profile(**kwargs: Any) -> GeoDatasetProfile:
    return GeoDatasetProfileService().build_profile(**kwargs)


@dataclass
class _ParsedGeoMetadata:
    title: str = ""
    summary: str = ""
    overall_design: str = ""
    platform_ids: list[str] = field(default_factory=list)
    organism: str = ""
    sample_records: list[GeoSampleRecord] = field(default_factory=list)
    supplementary_urls: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def merge(self, other: "_ParsedGeoMetadata") -> None:
        self.title = self.title or other.title
        self.summary = self.summary or other.summary
        self.overall_design = self.overall_design or other.overall_design
        self.organism = self.organism or other.organism
        self.platform_ids = list(dict.fromkeys([*self.platform_ids, *other.platform_ids]))
        if other.sample_records:
            self.sample_records = other.sample_records
        self.supplementary_urls = list(dict.fromkeys([*self.supplementary_urls, *other.supplementary_urls]))
        self.warnings = [*self.warnings, *other.warnings]


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
                    current = {"accession": _value(stripped)}
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
                    elif normalized == "series_supplementary_file":
                        parsed.supplementary_urls.append(value)
                    elif normalized == "series_relation" and _looks_raw_link(value):
                        parsed.supplementary_urls.append(value)
                    continue
                if normalized == "sample_geo_accession":
                    current["accession"] = value
                elif normalized == "sample_title":
                    current["title"] = value
                elif normalized == "sample_source_name_ch1":
                    current["source_name_ch1"] = value
                elif normalized == "sample_characteristics_ch1":
                    current.setdefault("characteristics_ch1", []).append(value)
                elif normalized == "sample_description":
                    current["description"] = _append_text(str(current.get("description") or ""), value)
                elif normalized == "sample_supplementary_file" or (normalized == "sample_relation" and _looks_raw_link(value)):
                    current.setdefault("raw_links", []).append(value)
                    parsed.supplementary_urls.append(value)
            if current is not None:
                parsed.sample_records.append(_sample_record(current))
    except OSError as exc:
        parsed.warnings.append(f"family_soft_read_failed:{exc}")
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
                elif normalized == "sample_characteristics_ch1":
                    for index, value in enumerate(values):
                        if value:
                            characteristics_by_index.setdefault(index, []).append(value)
                elif normalized.startswith("sample_"):
                    sample_fields.setdefault(normalized, []).extend(values)
    except OSError as exc:
        parsed.warnings.append(f"series_matrix_read_failed:{exc}")
        return parsed
    sample_ids = sample_fields.get("sample_geo_accession", [])
    count = max((len(values) for values in sample_fields.values()), default=0)
    records: list[GeoSampleRecord] = []
    for index in range(count):
        characteristics = characteristics_by_index.get(index, [])
        records.append(
            GeoSampleRecord(
                accession=sample_ids[index] if index < len(sample_ids) else "",
                title=_indexed(sample_fields, "sample_title", index),
                source_name_ch1=_indexed(sample_fields, "sample_source_name_ch1", index),
                characteristics_ch1=tuple(characteristics),
                description=_indexed(sample_fields, "sample_description", index),
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
    comparisons: list[GeoCandidateComparison] = []
    field_assignments: dict[str, dict[str, str]] = {}
    for sample in sample_records:
        sample_id = sample.accession or sample.title
        for field, text in (
            ("sample_title", sample.title),
            ("source_name_ch1", sample.source_name_ch1),
            ("description", sample.description),
        ):
            group = _group_label_from_text(text)
            if sample_id and group:
                field_assignments.setdefault(field, {})[sample_id] = group
        for characteristic in sample.characteristics_ch1:
            parsed_field, value = _parse_characteristic(characteristic)
            field = parsed_field or "characteristics_ch1"
            group = _group_label_from_text(value or characteristic)
            if sample_id and group:
                field_assignments.setdefault(field, {})[sample_id] = group

    for field, assignments in field_assignments.items():
        sizes = dict(Counter(assignments.values()))
        if not _valid_group_sizes(sizes):
            continue
        comparisons.append(_comparison_from_sizes(field, sizes, assignments, evidence=(f"{field} 中识别到重复分组标签",), confidence="high" if field not in {"sample_title", "description"} else "medium"))

    text_sizes = _group_sizes_from_text(" ".join([overall_design, summary]))
    if text_sizes and not any(set(item.group_sizes) == set(text_sizes) for item in comparisons):
        comparisons.append(_comparison_from_sizes("geo_page_text", text_sizes, {}, evidence=("summary/overall design 提及候选比较结构",), confidence="medium"))

    return sorted(comparisons, key=lambda item: (_confidence_rank(item.confidence), sum(item.group_sizes.values())), reverse=True)


def _comparison_from_sizes(
    field: str,
    sizes: dict[str, int],
    assignments: dict[str, str],
    *,
    evidence: tuple[str, ...],
    confidence: str,
) -> GeoCandidateComparison:
    control = _control_group(sizes)
    case = _case_group(sizes, control)
    label = f"{case} vs {control}" if control and case else "候选分组比较"
    warnings = () if confidence != "low" else ("低置信度分组，只能作为提示。",)
    return GeoCandidateComparison(
        comparison_id=f"{field}:{_slug(label)}",
        label=label,
        control_group=control,
        case_group=case,
        group_sizes=dict(sorted(sizes.items(), key=lambda item: item[0])),
        sample_assignments=assignments,
        confidence=confidence,
        evidence=evidence,
        warnings=warnings,
    )


def _sample_structure_preview(sample_count: int | str, sample_records: tuple[GeoSampleRecord, ...], comparisons: list[GeoCandidateComparison]) -> dict[str, object]:
    top = comparisons[0] if comparisons else None
    return {
        "sample_count": sample_count or len(sample_records),
        "sample_types": top.group_sizes if top is not None else {},
        "candidate_group_fields": [item.comparison_id.split(":", 1)[0] for item in comparisons],
        "confidence": top.confidence if top is not None else "low",
        "evidence": list(top.evidence) if top is not None else [],
        "status": "preview_only" if top is not None else "no_group_detected",
    }


def _recommendation(
    *,
    title: str,
    summary: str,
    overall_design: str,
    organism: str,
    experiment_type: str,
    sample_count: int | str,
    comparisons: list[GeoCandidateComparison],
    expression_files: tuple[str, ...],
    manifest: dict[str, Any],
) -> tuple[int, str, str]:
    text = " ".join([title, summary, overall_design, experiment_type]).lower()
    score = 0
    reasons: list[str] = []
    if any(token in text for token in ("expression", "transcriptome", "microarray", "rna-seq", "rna seq")):
        score += 25
        reasons.append("数据类型适合表达分析")
    if organism.lower().startswith("homo sapiens") or "human" in organism.lower():
        score += 15
        reasons.append("样本物种为人类或疑似人类")
    if comparisons:
        score += 25
        reasons.append(f"检测到候选比较组：{comparisons[0].label}")
    if expression_files or _manifest_has_expression_candidate(manifest):
        score += 20
        reasons.append("发现可能的表达矩阵文件")
    count = _int_or_zero(sample_count)
    if count >= 6:
        score += 10
        reasons.append(f"样本数为 {count}")
    if any(token in text for token in ("single-cell", "single cell", "scrna", "spatial", "methylation", "atac", "chip-seq", "mirna")):
        score -= 35
        reasons.append("数据类型可能不是常规 bulk expression")
    score = max(0, min(100, score))
    if score >= 75:
        level = "高"
    elif score >= 50:
        level = "中"
    elif score >= 25:
        level = "低"
    else:
        level = "不建议"
    return score, level, "；".join(reasons) or "页面信息不足，需人工查看后再决定是否下载。"


def _consistency_review(
    *,
    sample_count: int | str,
    platform_ids: tuple[str, ...],
    experiment_type: str,
    comparisons: list[GeoCandidateComparison],
    recognition_report: dict[str, Any] | None,
) -> dict[str, object]:
    if not recognition_report:
        return {"status": "not_checked", "warnings": []}
    warnings: list[str] = []
    group_preview = recognition_report.get("group_preview") if isinstance(recognition_report, dict) else {}
    if isinstance(group_preview, dict):
        file_count = _int_or_zero(group_preview.get("sample_count"))
        page_count = _int_or_zero(sample_count)
        if page_count and file_count and page_count != file_count:
            warnings.append(f"页面样本数 {page_count} 与文件识别样本数 {file_count} 不一致。")
        if comparisons and group_preview.get("group_sizes") and dict(comparisons[0].group_sizes) != dict(group_preview.get("group_sizes") or {}):
            warnings.append("页面候选分组与文件内识别分组不一致。")
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
            warnings.append("页面平台 GPL 与文件识别平台提示不一致。")
    return {
        "status": "needs_review" if warnings else "consistent",
        "warnings": warnings,
        "page_experiment_type": experiment_type,
    }


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
    path = root / "raw_data" / "geo" / accession / f"{accession}_family.soft.gz"
    return path if path.is_file() else None


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


def _supplementary_files(urls: list[str], manifest: dict[str, Any]) -> list[GeoSupplementaryFile]:
    files: list[GeoSupplementaryFile] = []
    for item in manifest.get("assets", []) or []:
        if not isinstance(item, dict):
            continue
        if item.get("asset_type") not in {"series_matrix", "supplementary_file", "family_soft"}:
            continue
        files.append(
            GeoSupplementaryFile(
                file_name=str(item.get("file_name") or Path(str(item.get("remote_url") or "")).name),
                remote_url=str(item.get("remote_url") or ""),
                asset_type=str(item.get("asset_type") or ""),
                role=str(item.get("role") or ""),
                status=str(item.get("status") or ""),
                local_path=str(item.get("local_path") or ""),
                recommendation=_file_recommendation(str(item.get("role") or item.get("file_name") or "")),
            )
        )
    known_urls = {item.remote_url for item in files if item.remote_url}
    for url in urls:
        if url and url not in known_urls:
            files.append(GeoSupplementaryFile(file_name=Path(url).name or url, remote_url=url, asset_type="supplementary_file", role=_role_from_name(url), status="remote_discovered", recommendation=_file_recommendation(url)))
    return files


def _possible_files(files: list[GeoSupplementaryFile], *, roles: tuple[str, ...]) -> tuple[str, ...]:
    matches = []
    for item in files:
        text = " ".join([item.file_name, item.role, item.asset_type]).lower()
        if any(token in text for token in roles):
            matches.append(item.file_name)
    return tuple(dict.fromkeys(matches))


def _suggested_download_files(files: list[GeoSupplementaryFile], expressions: tuple[str, ...], annotations: tuple[str, ...]) -> tuple[str, ...]:
    suggestions = list(expressions[:5])
    if not suggestions:
        suggestions.extend(item.file_name for item in files if item.asset_type == "series_matrix")
    suggestions.extend(name for name in annotations[:2] if name not in suggestions)
    return tuple(dict.fromkeys(suggestions))


def _group_sizes_from_text(text: str) -> dict[str, int]:
    lowered = text.lower()
    labels = []
    for token in ("adjacent normal", "normal", "control", "vehicle", "untreated", "tumor", "tumour", "cancer", "carcinoma", "treated", "resistant", "sensitive", "mutant", "wild type", "wt"):
        if token in lowered:
            labels.append(_canonical_group(token))
    labels = list(dict.fromkeys(label for label in labels if label))
    if len(labels) < 2:
        return {}
    sizes: dict[str, int] = {}
    for label in labels:
        size = _number_near_label(lowered, label)
        sizes[label] = size if size > 0 else 1
    return sizes if _valid_group_sizes(sizes) else {}


def _group_label_from_text(text: object) -> str:
    lowered = str(text or "").lower()
    for phrase in (
        "adjacent normal",
        "para-cancer",
        "normal",
        "vehicle",
        "untreated",
        "control",
        "resistant",
        "sensitive",
        "treated",
        "treatment",
        "wild type",
        "wt",
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
        "vehicle": "control",
        "untreated": "control",
        "treatment": "treated",
        "tumour": "tumor",
        "cancer": "tumor",
        "carcinoma": "tumor",
        "malignant": "tumor",
        "wild type": "wild_type",
        "wt": "wild_type",
    }
    return mapping.get(token, token.replace(" ", "_"))


def _parse_characteristic(text: str) -> tuple[str, str]:
    label, sep, value = str(text).partition(":")
    if not sep:
        return "", str(text).strip()
    return _normalize_key(label), value.strip()


def _valid_group_sizes(sizes: dict[str, int]) -> bool:
    clean = {key: int(value) for key, value in sizes.items() if key and int(value) > 0}
    return 2 <= len(clean) <= 8


def _control_group(sizes: dict[str, int]) -> str:
    for value in ("normal", "control", "untreated", "vehicle", "wild_type", "sensitive", "baseline", "benign"):
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
        rf"(\d+)\s+(?:\w+\s+){{0,3}}{re.escape(label_text)}",
        rf"{re.escape(label_text)}(?:\s+\w+){{0,3}}\s+(\d+)",
    )
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return int(match.group(1))
    return 0


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


def _sample_record(payload: dict[str, Any]) -> GeoSampleRecord:
    return GeoSampleRecord(
        accession=str(payload.get("accession") or ""),
        title=str(payload.get("title") or ""),
        source_name_ch1=str(payload.get("source_name_ch1") or ""),
        characteristics_ch1=tuple(str(item) for item in payload.get("characteristics_ch1", []) if str(item).strip()),
        description=str(payload.get("description") or ""),
        raw_links=tuple(str(item) for item in payload.get("raw_links", []) if str(item).strip()),
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


def _file_recommendation(text: str) -> str:
    lowered = text.lower()
    if any(token in lowered for token in ("series_matrix", "expression", "matrix", "count", "cpm", "fpkm", "tpm")):
        return "建议优先下载，可能包含表达矩阵。"
    if any(token in lowered for token in ("annotation", "annot", "platform", "probe", "gene")):
        return "可作为注释参考，按需下载。"
    if any(token in lowered for token in ("fastq", "sra", "raw", "cel")):
        return "可能是原始数据，文件较大，下载前需确认。"
    return "按需查看。"


def _role_from_name(name: str) -> str:
    lowered = name.lower()
    if any(token in lowered for token in ("series_matrix", "expression", "matrix", "count", "cpm", "fpkm", "tpm")):
        return "supplementary_expression_candidate"
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
