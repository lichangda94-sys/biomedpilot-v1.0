"""Pure formatting helpers for Module 3 sandbox summaries."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from geo_processing import handoff_recommended_strategy, handoff_value_type_hint, load_module1_dataset_context
from geo_processing.download_models import DownloadValidationResult


def format_mapping(mapping: dict[str, Any]) -> str:
    return "\n".join(f"{key}: {value}" for key, value in mapping.items())


def warning_block(warnings: list[str], errors: list[str]) -> str:
    lines: list[str] = []
    if warnings:
        lines.append("warnings:")
        lines.extend(f"- {item}" for item in warnings)
    if errors:
        if lines:
            lines.append("")
        lines.append("errors:")
        lines.extend(f"- {item}" for item in errors)
    return "\n".join(lines) if lines else "warnings/errors: none"


def build_validation_summary_text(result: DownloadValidationResult) -> str:
    summary = {
        "gse_id": result.gse_id,
        "download_dir": result.download_dir,
        "status": result.status,
        "failure_stage": result.failure_stage,
        "failure_reason": result.failure_reason,
        "top_problem_summary": result.top_problem_summary,
        "suggested_next_fix": result.suggested_next_fix,
        "file_count": result.file_count,
        "nonempty_file_count": result.nonempty_file_count,
        "has_series_matrix": result.has_series_matrix,
        "has_family_soft": result.has_family_soft,
        "has_miniml": result.has_miniml,
        "has_supplementary": result.has_supplementary,
        "has_raw_files": result.has_raw_files,
        "has_expression_payload": result.has_expression_payload,
        "has_sample_annotation": result.has_sample_annotation,
        "has_clinical_annotation": result.has_clinical_annotation,
        "payload_type": result.payload_type,
        "external_raw_source": result.external_raw_source,
        "detected_gsm_count": result.detected_gsm_count,
        "candidate_matrix_count": result.candidate_matrix_count,
        "candidate_metadata_count": result.candidate_metadata_count,
        "candidate_clinical_count": result.candidate_clinical_count,
        "next_action": result.next_action,
        "candidate_matrix_files": result.candidate_matrix_files,
        "candidate_metadata_files": result.candidate_metadata_files,
        "candidate_clinical_files": result.candidate_clinical_files,
        "expression_sources": result.expression_sources,
        "sample_annotation_sources": result.sample_annotation_sources,
        "clinical_sources": result.clinical_sources,
        "raw_files": result.raw_files,
        "archive_files": result.archive_files,
        "platform_annotation_files": result.platform_annotation_files,
        "supporting_files": result.supporting_files,
        "external_sources": result.external_sources,
        "broken_files": result.broken_files,
    }
    return format_mapping(summary) + "\n\n" + warning_block(result.warnings, result.errors)


def build_detection_summary_text(result: Any) -> str:
    summary = {
        "accession_type": result.accession_type,
        "container_types": result.container_types,
        "data_roles": result.data_roles,
        "technology_type": result.technology_type,
        "matrix_level": result.matrix_level,
        "value_semantic": result.value_semantic,
        "has_expression_payload": result.has_expression_payload,
        "has_sample_annotation": result.has_sample_annotation,
        "has_clinical_annotation": result.has_clinical_annotation,
        "payload_type": result.payload_type,
        "has_series_matrix": result.has_series_matrix,
        "has_family_soft": result.has_family_soft,
        "has_miniml": result.has_miniml,
        "has_supplementary": result.has_supplementary,
        "has_platform_annotation": result.has_platform_annotation,
        "recommended_strategy": result.recommended_strategy,
        "confidence": result.confidence,
        "failure_stage": getattr(result, "failure_stage", None),
        "failure_reason": result.failure_reason,
        "next_action": result.next_action,
        "top_problem_summary": getattr(result, "top_problem_summary", None),
        "suggested_next_fix": getattr(result, "suggested_next_fix", None),
        "classification_debug": getattr(result, "classification_debug", {}),
        "conflicts": getattr(result, "conflicts", []),
        "candidate_expression_files": result.candidate_expression_files,
        "candidate_metadata_files": result.candidate_metadata_files,
        "candidate_clinical_files": getattr(result, "candidate_clinical_files", []),
        "candidate_annotation_files": result.candidate_annotation_files,
        "platform_annotation_files": getattr(result, "platform_annotation_files", []),
        "raw_files": result.raw_files,
        "archive_files": getattr(result, "archive_files", []),
        "supporting_files": getattr(result, "supporting_files", []),
        "external_sources": getattr(result, "external_sources", []),
    }
    return format_mapping(summary) + "\n\n" + warning_block(result.warnings, [])


def build_module3_asset_summary_text(module1_context: dict[str, Any]) -> str:
    standard_assets = module1_context.get("standard_assets", {})
    lines = [
        "module3_standard_assets:",
        f"recommended_strategy: {module1_context.get('recommended_strategy')}",
        f"value_type_hint: {module1_context.get('value_type_hint')}",
        f"available_capabilities: {module1_context.get('available_capabilities')}",
        f"missing_required_assets: {module1_context.get('missing_required_assets')}",
        f"present_assets: {module1_context.get('present_assets')}",
        f"planned_assets: {module1_context.get('planned_assets')}",
    ]
    for asset_key in ("expression_gene", "sample_annotation", "feature_annotation", "dataset_manifest"):
        asset = standard_assets.get(asset_key, {})
        lines.extend(
            [
                f"{asset_key}.status: {asset.get('status')}",
                f"{asset_key}.exists: {asset.get('exists')}",
                f"{asset_key}.expected: {asset.get('expected')}",
                f"{asset_key}.source_hint: {asset.get('source_hint')}",
                f"{asset_key}.reason_code: {asset.get('reason_code')}",
                f"{asset_key}.canonical_path: {asset.get('canonical_path')}",
            ]
        )
    return "\n".join(lines)


def build_module3_mainline_summary_text(module1_context: dict[str, Any]) -> str:
    standard_assets = module1_context.get("standard_assets", {})
    lines = [
        f"模块3推荐策略: {module1_context.get('recommended_strategy')}",
        f"模块3值类型提示: {module1_context.get('value_type_hint')}",
        f"模块3已存在标准资产: {module1_context.get('present_assets')}",
        f"模块3计划标准资产: {module1_context.get('planned_assets')}",
        f"模块3缺失必需资产: {module1_context.get('missing_required_assets')}",
    ]
    for asset_key in ("expression_gene", "sample_annotation", "feature_annotation", "dataset_manifest"):
        asset = standard_assets.get(asset_key, {})
        lines.append(
            f"{asset_key}: {asset.get('status')} / reason={asset.get('reason_code')} / path={asset.get('canonical_path')}"
        )
    return "\n".join(lines)


def build_workflow_result_text(result: dict[str, Any]) -> str:
    lines = [
        f"状态: {result['status']}",
        f"下载成功数: {result.get('download_success_count')}",
        f"元信息解析成功数: {result.get('metadata_parse_success_count')}",
        f"表达矩阵构建成功数: {result.get('expression_matrix_success_count')}",
        f"批量输出目录: {result['batch_dir']}",
        f"元数据 JSON: {result['metadata_json']}",
        f"元数据 CSV: {result['metadata_csv']}",
    ]
    for workflow_result in result.get("workflow_results", []):
        process_result = workflow_result["process_result"]
        validation_result = workflow_result.get("validation_result") or {}
        module1_handoff = workflow_result.get("module1_handoff") or load_module1_dataset_context(
            workflow_result.get("download_result", {}).get("dataset_root") or Path(workflow_result["family_soft_path"]).parent.parent.parent
        )
        dataset_info = module1_handoff.get("dataset_info", {})
        lines.extend(
            [
                "",
                f"GSE: {workflow_result['accession']}",
                f"下载成功: {workflow_result.get('download_success')}",
                f"下载验收状态: {dataset_info.get('legacy_status') or validation_result.get('status')}",
                f"模块1策略: {handoff_recommended_strategy(module1_handoff)}",
                f"值类型提示: {handoff_value_type_hint(module1_handoff)}",
                f"下载验收建议: {validation_result.get('next_action')}",
                f"可生成 expression_gene: {module1_handoff.get('may_generate_expression_gene')}",
                f"可生成 sample_annotation: {module1_handoff.get('may_generate_sample_annotation')}",
                f"可能有 clinical: {module1_handoff.get('has_clinical_info')}",
                f"可能有 mutation: {module1_handoff.get('has_mutation_info')}",
                f"可能有 batch: {module1_handoff.get('has_batch_info')}",
                f"元信息解析成功: {workflow_result.get('metadata_parse_success')}",
                f"矩阵构建成功: {workflow_result.get('matrix_build_success')}",
                f"矩阵构建跳过: {workflow_result.get('matrix_build_skipped')}",
                f"矩阵构建失败: {workflow_result.get('matrix_build_failed')}",
                f"表达矩阵错误: {workflow_result.get('expression_matrix_error')}",
                f"GPL gene 列自动识别: {process_result.get('resolved_gpl_gene_col')}",
                f"GPL gene 列识别方式: {process_result.get('gpl_gene_col_detection')}",
                f"手动 GPL gene 列: {process_result.get('manual_gpl_gene_col')}",
                f"family soft: {workflow_result['family_soft_path']}",
                f"processed dir: {workflow_result['processed_dir']}",
                f"run summary: {workflow_result['run_summary_path']}",
                f"样本数: {process_result.get('n_samples')}",
                f"probe 矩阵: {process_result.get('n_probe_rows')} x {process_result.get('n_probe_cols')}",
                f"gene 矩阵: {process_result.get('n_gene_rows')} x {process_result.get('n_gene_cols')}",
                "模块3主线接入摘要:",
                build_module3_mainline_summary_text(module1_handoff),
            ]
        )
    return "\n".join(lines)


def build_file_detail_text(detail: dict[str, Any], detector_reasons: list[str] | None = None) -> str:
    detector_reasons = detector_reasons or []
    explanation = {
        "file_path": detail.get("path"),
        "relative_path": detail.get("relative_path"),
        "source_level": detail.get("source_level") or detail.get("source_scope"),
        "source_path": detail.get("source_path"),
        "excluded": detail.get("excluded"),
        "excluded_reason": detail.get("excluded_reason"),
        "container_type": detail.get("container_type"),
        "primary_label": detail.get("primary_label"),
        "secondary_labels": detail.get("secondary_labels"),
        "accepted_as_candidate_matrix": detail.get("accepted_as_candidate_matrix"),
        "accepted_as_payload": detail.get("accepted_as_payload"),
        "organized_targets": detail.get("organized_targets"),
        "confidence": detail.get("confidence"),
        "expression_score": detail.get("expression_score"),
        "sample_annotation_score": detail.get("sample_annotation_score"),
        "clinical_score": detail.get("clinical_score"),
        "raw_data_score": detail.get("raw_data_score"),
        "platform_annotation_score": detail.get("platform_annotation_score"),
        "junk_score": detail.get("junk_score"),
        "head_signals": detail.get("head_signals"),
        "middle_signals": detail.get("middle_signals"),
        "tail_signals": detail.get("tail_signals"),
        "global_markers_found": detail.get("global_markers_found"),
        "marker_counts": detail.get("marker_counts"),
        "size_bytes": detail.get("size_bytes"),
        "sample_column_count": detail.get("sample_column_count"),
        "detected_gsm_count": detail.get("detected_gsm_count"),
        "extra": detail.get("extra"),
        "warnings": detail.get("warnings"),
        "errors": detail.get("errors"),
        "decision_trace": detail.get("decision_trace", []),
        "why_classified_this_way": detail.get("reasons", []) + detector_reasons,
    }
    preview = "\n".join(detail.get("preview_lines", [])[:12]) or "<no preview>"
    head_preview = "\n".join(detail.get("head_preview", [])[:10]) or "<no head preview>"
    middle_preview = "\n".join(detail.get("middle_preview", [])[:10]) or "<no middle preview>"
    tail_preview = "\n".join(detail.get("tail_preview", [])[:10]) or "<no tail preview>"
    text = format_mapping(explanation)
    text += f"\n\npreview:\n{preview}\n\nhead_preview:\n{head_preview}\n\nmiddle_preview:\n{middle_preview}\n\ntail_preview:\n{tail_preview}"
    return text
