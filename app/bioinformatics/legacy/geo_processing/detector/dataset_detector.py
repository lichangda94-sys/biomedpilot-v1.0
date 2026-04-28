"""Top-level GEO dataset detection orchestration."""

from __future__ import annotations

import json
import re
from dataclasses import asdict
from collections import Counter
from pathlib import Path

from ..download_validator import compare_expected_vs_actual, normalize_failure_stage, validate_downloaded_dataset
from .models import (
    AccessionType,
    DatasetDetectionResult,
    MatrixLevel,
    RecommendedStrategy,
    TechnologyType,
    ValueSemantic,
)
from .strategy_router import route_processing_strategy

ACCESSION_RE = re.compile(r"^(GSE|GSM|GPL|GDS)\d+$", re.IGNORECASE)


def detect_accession_type(accession_or_name: str) -> AccessionType:
    value = accession_or_name.strip().upper()
    match = ACCESSION_RE.match(value)
    if not match:
        return AccessionType.UNKNOWN
    return AccessionType(match.group(1))


def _pick_modal(values: list[str], default: str) -> str:
    usable = [value for value in values if value and value != default]
    if not usable:
        return default
    return Counter(usable).most_common(1)[0][0]


def _add_vote(bucket: list[dict[str, object]], vote: str, reason: str, source: str, weight: float = 1.0) -> None:
    bucket.append({"vote": vote, "reason": reason, "source": source, "weight": round(weight, 3)})


def _finalize_votes(votes: list[dict[str, object]]) -> dict[str, object]:
    totals: Counter[str] = Counter()
    for item in votes:
        totals[str(item["vote"])] += float(item.get("weight", 1.0))
    ranked = [
        {"vote": vote, "weight": round(weight, 3)}
        for vote, weight in totals.most_common()
    ]
    return {"votes": votes, "ranked": ranked}


def _collect_conflicts(*, technology_votes: list[dict[str, object]], matrix_level_votes: list[dict[str, object]], payload_votes: list[dict[str, object]], status_votes: list[dict[str, object]]) -> list[dict[str, object]]:
    conflicts: list[dict[str, object]] = []
    for category, votes in {
        "technology_votes": technology_votes,
        "matrix_level_votes": matrix_level_votes,
        "payload_votes": payload_votes,
        "status_votes": status_votes,
    }.items():
        distinct = sorted({str(item["vote"]) for item in votes if item.get("vote") and str(item["vote"]) != "unknown"})
        if len(distinct) > 1:
            conflicts.append(
                {
                    "category": category,
                    "votes": distinct,
                    "detail": f"{category} contains competing evidence: {', '.join(distinct)}",
                }
            )
    return conflicts


def _build_classification_debug(validation, technology_type: str, matrix_level: str, payload_type: str, status: str) -> dict[str, object]:
    technology_votes: list[dict[str, object]] = []
    matrix_level_votes: list[dict[str, object]] = []
    payload_votes: list[dict[str, object]] = []
    status_votes: list[dict[str, object]] = []

    for raw_file in validation.raw_files:
        lowered = raw_file.lower()
        if lowered.endswith(".cel"):
            _add_vote(technology_votes, TechnologyType.MICROARRAY.value, "raw CEL file detected", raw_file, 1.2)
        if any(lowered.endswith(ext) for ext in (".fastq.gz", ".fq.gz", ".bam", ".sra")):
            _add_vote(technology_votes, TechnologyType.BULK_RNASEQ_RAW_LINKED.value, "sequencing raw file detected", raw_file, 1.2)

    for platform_file in validation.platform_annotation_files:
        _add_vote(technology_votes, TechnologyType.MICROARRAY.value, "platform annotation file detected", platform_file, 0.8)

    for score in validation.extra.get("file_scores", []):
        relative_path = str(score.get("relative_path", "unknown"))
        trace = " | ".join(score.get("decision_trace", []) or []).lower()
        preview = "\n".join(score.get("preview_lines", []) or []).lower()
        if any(token in f"{relative_path} {trace} {preview}" for token in ("single_cell", "scrna", "seurat", "10x", "barcode", "droplet")):
            _add_vote(technology_votes, TechnologyType.SINGLE_CELL.value, "single-cell markers found in file context", relative_path, 1.0)
        if any(token in f"{relative_path} {trace} {preview}" for token in ("spatial", "visium")):
            _add_vote(technology_votes, TechnologyType.SPATIAL.value, "spatial markers found in file context", relative_path, 1.0)

        if score.get("primary_label") == "expression_payload":
            matrix_payload = score.get("extra", {}).get("matrix_classification", {})
            columns = [str(item).lower() for item in matrix_payload.get("columns", [])]
            preview_lines = " ".join(score.get("preview_lines", []) or []).lower()
            file_hint = f"{relative_path} {' '.join(columns)} {' '.join(score.get('decision_trace', []))} {preview_lines}".lower()
            if any(token in file_hint for token in ("probe", "_at")):
                _add_vote(matrix_level_votes, MatrixLevel.PROBE.value, "probe-style identifiers detected", relative_path, 1.0)
            if any(token in file_hint for token in ("gene_id", "symbol", "ensembl", "tp53", "egfr", "brca")):
                _add_vote(matrix_level_votes, MatrixLevel.GENE.value, "gene-style identifiers detected", relative_path, 1.0)
            if "transcript" in file_hint:
                _add_vote(matrix_level_votes, MatrixLevel.TRANSCRIPT.value, "transcript identifier detected", relative_path, 0.9)

        if score.get("primary_label") == "expression_payload":
            _add_vote(payload_votes, "expression_matrix", "file accepted as expression payload", relative_path, max(float(score.get("expression_score", 0.0)), 0.6))
        elif score.get("primary_label") == "raw_data":
            _add_vote(payload_votes, "raw_only", "file accepted as raw data", relative_path, max(float(score.get("raw_data_score", 0.0)), 0.6))
        elif score.get("primary_label") == "sample_annotation":
            _add_vote(payload_votes, "metadata_only", "file accepted as sample annotation", relative_path, max(float(score.get("sample_annotation_score", 0.0)), 0.5))
        elif score.get("primary_label") == "platform_annotation":
            _add_vote(payload_votes, "annotation_only", "file accepted as platform annotation", relative_path, max(float(score.get("platform_annotation_score", 0.0)), 0.5))
        elif any("diff-result" in warning.lower() for warning in score.get("warnings", [])):
            _add_vote(payload_votes, "diff_result_only", "diff-result evidence suppressed matrix acceptance", relative_path, 0.75)

    if validation.has_expression_payload:
        _add_vote(status_votes, "ANALYSIS_PATH", "expression payload exists", "validation", 1.0)
    if validation.has_sample_annotation:
        _add_vote(status_votes, "ANNOTATED", "sample annotation exists", "validation", 0.7)
    if validation.payload_type == "raw_only":
        _add_vote(status_votes, "RAW_ONLY", "only raw payload is available", "validation", 1.0)
    if validation.payload_type in {"metadata_only", "annotation_only", "diff_result_only"}:
        _add_vote(status_votes, "NO_EXPRESSION_PAYLOAD", f"validation payload type is {validation.payload_type}", "validation", 1.0)

    conflicts = _collect_conflicts(
        technology_votes=technology_votes,
        matrix_level_votes=matrix_level_votes,
        payload_votes=payload_votes,
        status_votes=status_votes,
    )
    final_decision_reason = (
        f"technology={technology_type}, matrix_level={matrix_level}, payload={payload_type}, validation_status={status}"
    )
    return {
        "technology_votes": _finalize_votes(technology_votes),
        "matrix_level_votes": _finalize_votes(matrix_level_votes),
        "payload_votes": _finalize_votes(payload_votes),
        "status_votes": _finalize_votes(status_votes),
        "final_decision_reason": final_decision_reason,
        "conflicts": conflicts,
    }


def _has_accepted_series_matrix_expression(validation) -> bool:
    for relative_path in validation.expression_sources:
        if "series_matrix" in str(relative_path).lower():
            return True
    for score in validation.extra.get("file_scores", []):
        relative_path = str(score.get("relative_path", "")).lower()
        if "series_matrix" not in relative_path:
            continue
        if score.get("primary_label") == "expression_payload" or score.get("accepted_as_candidate_matrix"):
            return True
    return False


def _expected_strategy_from_validation(result: DatasetDetectionResult, validation) -> str:
    if result.recommended_strategy in {
        RecommendedStrategy.UNSUPPORTED_SINGLE_CELL.value,
        RecommendedStrategy.UNSUPPORTED_SPATIAL.value,
    }:
        return result.recommended_strategy
    if validation.status in {"ANALYSIS_READY", "PARTIAL_BUT_USABLE", "EXPRESSION_ONLY"} and validation.has_expression_payload:
        if _has_accepted_series_matrix_expression(validation):
            return RecommendedStrategy.SERIES_MATRIX_FIRST.value
        if result.candidate_expression_files and validation.has_family_soft:
            return RecommendedStrategy.SOFT_METADATA_PLUS_SUPP_MATRIX.value
        if result.candidate_expression_files:
            return RecommendedStrategy.SUPPLEMENTARY_MATRIX_FIRST.value
        return RecommendedStrategy.MANUAL_REVIEW_REQUIRED.value
    if validation.status in {"METADATA_ONLY", "NO_EXPRESSION_PAYLOAD"}:
        return RecommendedStrategy.METADATA_ONLY.value
    if validation.status == "RAW_ONLY":
        if result.technology_type == TechnologyType.MICROARRAY.value:
            return RecommendedStrategy.RAW_MICROARRAY_EXTERNAL_PREPROCESS.value
        return RecommendedStrategy.RAW_RNASEQ_EXTERNAL_PREPROCESS.value
    return result.recommended_strategy or RecommendedStrategy.MANUAL_REVIEW_REQUIRED.value


def _add_conflict(result: DatasetDetectionResult, category: str, detail: str, votes: list[str]) -> None:
    conflict = {"category": category, "votes": votes, "detail": detail}
    if conflict not in result.conflicts:
        result.conflicts.append(conflict)


def _align_detection_with_validation(result: DatasetDetectionResult, validation) -> DatasetDetectionResult:
    expected_strategy = _expected_strategy_from_validation(result, validation)
    current_strategy = result.recommended_strategy
    if current_strategy != expected_strategy:
        _add_conflict(
            result,
            "validation_detection_alignment",
            f"validation.status={validation.status} expects {expected_strategy}, but strategy routing produced {current_strategy}",
            [validation.status, current_strategy or "UNKNOWN", expected_strategy],
        )
        result.recommended_strategy = expected_strategy
        result.failure_stage = result.failure_stage or "dataset_aggregation"
        result.top_problem_summary = (
            "validation、detection、strategy routing 原始结论不一致，已按 validation 证据边界统一策略。"
        )
        result.suggested_next_fix = (
            "优先检查 strategy routing 是否过度依赖 matrix_level / technology 的确定性，导致把已接受的 expression payload 降级。"
        )
        result.classification_debug["final_decision_reason"] = (
            f"{result.classification_debug.get('final_decision_reason', '')}; aligned_strategy={expected_strategy} because validation.status={validation.status}"
        ).strip("; ")
    result.classification_debug["validation_detection_alignment"] = {
        "validation_status": validation.status,
        "expected_strategy": expected_strategy,
        "final_strategy": result.recommended_strategy,
        "consistent": result.recommended_strategy == expected_strategy,
    }
    result.classification_debug["conflicts"] = result.conflicts
    return result


def _ensure_detection_defaults(result: DatasetDetectionResult) -> DatasetDetectionResult:
    result.failure_stage = result.failure_stage or ("dataset_aggregation" if result.failure_reason or result.conflicts else "dataset_aggregation")
    result.top_problem_summary = result.top_problem_summary or (
        "分类证据存在冲突，需要根据 votes 判断是哪一层规则过宽或过窄。"
        if result.conflicts
        else "检测链路未发现阻断问题。"
    )
    result.suggested_next_fix = result.suggested_next_fix or (
        "先看 classification_debug、conflicts 和 expected_vs_actual_diff，确认偏差是在 semantic_classification 还是 dataset_aggregation。"
    )
    original_stage = result.failure_stage
    result.failure_stage = normalize_failure_stage(result.failure_stage) or "dataset_aggregation"
    if original_stage and original_stage != result.failure_stage:
        result.extra["sub_failure_stage"] = original_stage
    return result


def _finalize_detection_result(result: DatasetDetectionResult, validation, root_dir: str) -> DatasetDetectionResult:
    result = _align_detection_with_validation(result, validation)
    result = _ensure_detection_defaults(result)
    result.warnings = sorted(dict.fromkeys(result.warnings))
    result.extra["validation_status"] = validation.status
    expected = validation.extra.get("expected_vs_actual_diff")
    if expected is not None:
        result.extra["expected_vs_actual_diff"] = expected
    else:
        expected_payload = Path(root_dir).expanduser().resolve() / "expected.json"
        compare_target = {**validation.to_dict(), **asdict(result)}
        if expected_payload.exists():
            try:
                result.extra["expected_vs_actual_diff"] = {
                    "enabled": True,
                    "expected_path": str(expected_payload),
                    **compare_expected_vs_actual(
                        json.loads(expected_payload.read_text(encoding="utf-8")),
                        compare_target,
                    ),
                }
            except Exception as exc:
                result.extra["expected_vs_actual_diff"] = {
                    "enabled": False,
                    "expected_path": str(expected_payload),
                    "matched_fields": [],
                    "mismatched_fields": [],
                    "likely_failure_stage": None,
                    "summary": f"failed to compare expected vs actual: {exc}",
                }
        else:
            result.extra["expected_vs_actual_diff"] = {
                "enabled": False,
                "expected_path": str(expected_payload),
                "matched_fields": [],
                "mismatched_fields": [],
                "likely_failure_stage": None,
                "summary": "expected.json not found; 对照测试未启用",
            }
    if result.extra.get("expected_vs_actual_diff"):
        diff = result.extra["expected_vs_actual_diff"]
        if diff.get("mismatched_fields"):
            result.failure_stage = diff.get("likely_failure_stage") or result.failure_stage

    root = Path(root_dir).expanduser().resolve()
    if validation.extra.get("debug_snapshot_paths") is not None:
        result.extra["debug_snapshot_paths"] = dict(validation.extra.get("debug_snapshot_paths", {}))
    if validation.extra.get("debug_snapshot_paths") is not None or True:
        snapshot_dir = root / "organized" / "reports" / "debug_snapshots"
        snapshot_dir.mkdir(parents=True, exist_ok=True)
        result.extra.setdefault("debug_snapshot_paths", {})
        result.extra["debug_snapshot_paths"]["dataset_detection"] = str(snapshot_dir / "dataset_detection.json")
        (snapshot_dir / "dataset_detection.json").write_text(
            json.dumps(result.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        result.extra["debug_snapshot_paths"]["expected_vs_actual_diff"] = str(snapshot_dir / "expected_vs_actual_diff.json")
        (snapshot_dir / "expected_vs_actual_diff.json").write_text(
            json.dumps(result.extra["expected_vs_actual_diff"], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    reports_dir = root / "organized" / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    (reports_dir / "expected_vs_actual_diff.json").write_text(
        json.dumps(result.extra["expected_vs_actual_diff"], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return _ensure_detection_defaults(result)


def _infer_technology(validation) -> str:
    raw_exts = {Path(item).suffix.lower() for item in validation.raw_files}
    all_text = " ".join(
        [
            *validation.expression_sources,
            *validation.sample_annotation_sources,
            *validation.platform_annotation_files,
            *validation.supporting_files,
            *validation.archive_files,
        ]
    ).lower()
    if any(token in all_text for token in ("single_cell", "scrna", "seurat", "10x", "droplet", "barcode")):
        return TechnologyType.SINGLE_CELL.value
    if any(token in all_text for token in ("spatial", "visium")):
        return TechnologyType.SPATIAL.value
    if any(ext in raw_exts for ext in {".cel"}):
        return TechnologyType.MICROARRAY.value
    if any(ext in raw_exts for ext in {".fastq.gz", ".fq.gz", ".bam", ".sra"}):
        return TechnologyType.BULK_RNASEQ_RAW_LINKED.value
    if validation.platform_annotation_files or any("gpl" in item.lower() for item in validation.platform_annotation_files):
        return TechnologyType.MICROARRAY.value
    if validation.raw_files:
        return TechnologyType.BULK_RNASEQ.value
    return TechnologyType.UNKNOWN.value


def _infer_matrix_level(validation) -> str:
    for score in validation.extra.get("file_scores", []):
        if score.get("primary_label") != "expression_payload":
            continue
        rows = score.get("preview_lines", [])
        joined = "\n".join(rows).lower()
        rel = str(score.get("relative_path", "")).lower()
        if any(token in joined for token in ("tp53", "egfr", "brca", "gene_id", "symbol", "ensembl")):
            return MatrixLevel.GENE.value
        if "_at" in joined or "probe" in joined or "probe" in rel:
            return MatrixLevel.PROBE.value
        if "transcript" in joined:
            return MatrixLevel.TRANSCRIPT.value
        if "id_ref" in joined:
            return MatrixLevel.GENE.value
    if validation.payload_type == "diff_result_only":
        return MatrixLevel.DIFF_RESULT.value
    return MatrixLevel.UNKNOWN.value


def _infer_value_semantic(validation) -> str:
    joined = " ".join(validation.expression_sources).lower()
    if "count" in joined:
        return ValueSemantic.RAW_COUNTS.value
    if any(token in joined for token in ("tpm", "fpkm", "rpkm", "normalized")):
        return ValueSemantic.NORMALIZED_COUNTS.value
    if "log2" in joined:
        return ValueSemantic.LOG2_EXPRESSION.value
    return ValueSemantic.UNKNOWN.value


def detect_dataset(accession: str, root_dir: str) -> DatasetDetectionResult:
    accession_type = detect_accession_type(accession)
    validation = validate_downloaded_dataset(accession, root_dir)
    result = DatasetDetectionResult(
        accession=validation.gse_id,
        accession_type=accession_type.value,
        scan_root=str(Path(root_dir).expanduser().resolve()),
        technology_type=_infer_technology(validation),
        matrix_level=_infer_matrix_level(validation),
        value_semantic=_infer_value_semantic(validation),
        has_series_matrix=validation.has_series_matrix,
        has_family_soft=validation.has_family_soft,
        has_miniml=validation.has_miniml,
        has_supplementary=validation.has_supplementary,
        has_platform_annotation=bool(validation.platform_annotation_files),
        has_expression_payload=validation.has_expression_payload,
        has_sample_annotation=validation.has_sample_annotation,
        has_clinical_annotation=validation.has_clinical_annotation,
        payload_type=validation.payload_type,
        candidate_expression_files=list(validation.expression_sources),
        candidate_metadata_files=list(validation.sample_annotation_sources),
        candidate_clinical_files=list(validation.clinical_sources),
        candidate_annotation_files=list(validation.platform_annotation_files),
        raw_files=list(validation.raw_files),
        platform_annotation_files=list(validation.platform_annotation_files),
        supporting_files=list(validation.supporting_files),
        archive_files=list(validation.archive_files),
        external_sources=list(validation.external_sources),
        ignored_files=list(validation.ignored_files),
        warnings=list(validation.warnings),
        failure_stage=validation.failure_stage,
        failure_reason=validation.failure_reason,
        next_action=validation.next_action,
        top_problem_summary=validation.top_problem_summary,
        suggested_next_fix=validation.suggested_next_fix,
    )

    if not result.candidate_metadata_files and result.has_family_soft:
        result.candidate_metadata_files = [
            score["relative_path"]
            for score in validation.extra.get("file_scores", [])
            if str(score.get("extra", {}).get("container_type")) == "family_soft"
        ]

    result.container_types = sorted(
        {
            token
            for token, present in {
                "series_matrix": result.has_series_matrix,
                "family_soft": result.has_family_soft,
                "miniml": result.has_miniml,
                "supplementary": result.has_supplementary,
                "platform_annotation": result.has_platform_annotation,
                "raw_file": bool(result.raw_files),
                "archive": bool(result.archive_files),
            }.items()
            if present
        }
    )
    result.data_roles = sorted(
        {
            token
            for token, present in {
                "processed": result.has_expression_payload,
                "metadata": result.has_sample_annotation or result.has_clinical_annotation,
                "raw": bool(result.raw_files),
            }.items()
            if present
        }
    )
    result.classification_debug = _build_classification_debug(
        validation,
        technology_type=result.technology_type,
        matrix_level=result.matrix_level,
        payload_type=result.payload_type,
        status=validation.status,
    )
    result.conflicts = list(result.classification_debug.get("conflicts", []))

    if result.failure_reason == "RAW_ONLY_DATASET":
        result.recommended_strategy = (
            RecommendedStrategy.RAW_MICROARRAY_EXTERNAL_PREPROCESS.value
            if result.technology_type == TechnologyType.MICROARRAY.value
            else RecommendedStrategy.RAW_RNASEQ_EXTERNAL_PREPROCESS.value
        )
        result.confidence = 0.92
        result.failure_stage = "semantic_classification"
        result.top_problem_summary = result.top_problem_summary or "检测只拿到了原始数据，没有可直接分析的表达矩阵。"
        result.suggested_next_fix = result.suggested_next_fix or "优先确认这是预期的 raw-only 数据集；若不是，再调 source_landing 或 semantic_classification。"
        result.extra["validation_status"] = validation.status
        return _finalize_detection_result(result, validation, root_dir)

    if result.technology_type == TechnologyType.SINGLE_CELL.value:
        result.recommended_strategy = RecommendedStrategy.UNSUPPORTED_SINGLE_CELL.value
        result.confidence = 0.9
        result.failure_stage = "dataset_aggregation"
        result.top_problem_summary = "规则把该数据集判成了 single-cell，而当前流程只支持 bulk GEO。"
        result.suggested_next_fix = "优先检查 technology_votes 里触发 single-cell 的关键词是否过宽。"
        result.extra["validation_status"] = validation.status
        return _finalize_detection_result(result, validation, root_dir)
    if result.technology_type == TechnologyType.SPATIAL.value:
        result.recommended_strategy = RecommendedStrategy.UNSUPPORTED_SPATIAL.value
        result.confidence = 0.9
        result.failure_stage = "dataset_aggregation"
        result.top_problem_summary = "规则把该数据集判成了 spatial，目前不走 bulk 表达矩阵流程。"
        result.suggested_next_fix = "优先检查 technology_votes 中 spatial 证据是否被 README 或支持文件误触发。"
        result.extra["validation_status"] = validation.status
        return _finalize_detection_result(result, validation, root_dir)

    if result.has_expression_payload:
        if result.has_series_matrix:
            result.recommended_strategy = RecommendedStrategy.SERIES_MATRIX_FIRST.value
            result.confidence = 0.9
        elif result.candidate_expression_files:
            result.recommended_strategy = RecommendedStrategy.SUPPLEMENTARY_MATRIX_FIRST.value
            result.confidence = 0.82
        else:
            result.recommended_strategy = RecommendedStrategy.MANUAL_REVIEW_REQUIRED.value
            result.confidence = 0.4
    elif result.has_family_soft or result.has_sample_annotation:
        result.recommended_strategy = RecommendedStrategy.METADATA_ONLY.value
        result.confidence = 0.75
        if not result.failure_reason:
            result.failure_reason = "MATRIX_NOT_FOUND"
    elif result.archive_files or result.raw_files:
        result.recommended_strategy = RecommendedStrategy.MANUAL_REVIEW_REQUIRED.value
        result.confidence = 0.55
    else:
        result.recommended_strategy = RecommendedStrategy.MANUAL_REVIEW_REQUIRED.value
        result.confidence = 0.35

    if result.payload_type == "metadata_only" and not result.has_expression_payload:
        result.recommended_strategy = RecommendedStrategy.METADATA_ONLY.value
        result.failure_reason = "MATRIX_NOT_FOUND"
        result.confidence = max(result.confidence, 0.78)
    if result.has_family_soft and not result.has_expression_payload:
        result.recommended_strategy = RecommendedStrategy.METADATA_ONLY.value
        result.failure_reason = result.failure_reason or "MATRIX_NOT_FOUND"
        result.confidence = max(result.confidence, 0.76)
    if result.payload_type == "diff_result_only":
        result.failure_reason = "MATRIX_IS_DIFF_RESULT_NOT_EXPRESSION"
        result.recommended_strategy = RecommendedStrategy.METADATA_ONLY.value
        result.confidence = 0.88
        result.failure_stage = "dataset_aggregation"
        result.top_problem_summary = "检测到的是差异分析结果表，不是表达矩阵。"
        result.suggested_next_fix = "优先看 payload_votes 和 decision_trace，确认 diff-result 规则是否误伤真正矩阵。"
        result.extra["validation_status"] = validation.status
        return _finalize_detection_result(result, validation, root_dir)
    if result.has_family_soft and not result.has_expression_payload:
        result.recommended_strategy = RecommendedStrategy.METADATA_ONLY.value
        result.failure_reason = result.failure_reason or "MATRIX_NOT_FOUND"
        result.next_action = result.next_action or "metadata is available; continue metadata parsing without expression matrix"
        result.confidence = max(result.confidence, 0.76)
        result.warnings = sorted(dict.fromkeys(result.warnings))
        result.failure_stage = result.failure_stage or "semantic_classification"
        result.top_problem_summary = result.top_problem_summary or "family.soft 存在，但没有任何文件通过表达矩阵分类。"
        result.suggested_next_fix = result.suggested_next_fix or "优先查看 data_asset_index 里被排除文件的 decision_trace，判断是内容检查还是 expression 放行偏了。"
        result.extra["validation_status"] = validation.status
        return _finalize_detection_result(result, validation, root_dir)

    if result.matrix_level == MatrixLevel.PROBE.value and result.has_platform_annotation:
        result.warnings.append("probe-level matrix detected; GPL annotation mapping is recommended")

    result.failure_stage = result.failure_stage or ("dataset_aggregation" if result.failure_reason else None)
    if result.conflicts and not result.top_problem_summary:
        result.top_problem_summary = "分类证据存在冲突，需要根据 votes 判断是哪一层规则过宽或过窄。"
    if result.conflicts and not result.suggested_next_fix:
        result.suggested_next_fix = "先看 classification_debug.conflicts，再决定调 technology、matrix level 还是 payload/status 规则。"
    return _finalize_detection_result(route_processing_strategy(result), validation, root_dir)
