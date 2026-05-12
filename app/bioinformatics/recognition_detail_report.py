from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from app.bioinformatics.project_recognition import CURRENT_RECOGNITION_RUN, TYPE_LABELS
from app.bioinformatics.recognition_next_steps import recognition_run_current_status


def build_recognition_detail_payload(project_root: str | Path, run: dict[str, object], file_record: dict[str, object] | None = None) -> dict[str, object]:
    root = Path(project_root).expanduser().resolve()
    report = _report_from_run(root, run)
    files = [dict(file_record)] if isinstance(file_record, dict) else [item for item in report.get("files", []) or [] if isinstance(item, dict)]
    run_id = str(run.get("run_id") or "current_session")
    current = _read_json(root / CURRENT_RECOGNITION_RUN)
    is_current = bool(run.get("is_current")) or (bool(run_id) and str(current.get("run_id") or "") == run_id)
    current_status = recognition_run_current_status(root, run)
    status = str(current_status.get("label") or ("当前使用中" if is_current else "历史记录"))
    warnings = [str(item) for item in report.get("warnings", []) or [] if str(item)]
    warnings.extend(str(item.get("warning")) for item in files if isinstance(item, dict) and str(item.get("warning") or "").strip())
    return {
        "project_root": str(root),
        "run": dict(run),
        "run_id": run_id,
        "status": status,
        "status_note": str(current_status.get("note") or ""),
        "is_current": is_current,
        "is_legacy": bool(run.get("legacy")),
        "generated_at": str(run.get("generated_at") or report.get("generated_at") or ""),
        "recognition_report_path": str(run.get("recognition_report_path") or ""),
        "recognized_files_path": str(Path(str(run.get("run_dir") or "")) / "recognized_files.json") if run.get("run_dir") else "",
        "current_json_path": str(root / CURRENT_RECOGNITION_RUN),
        "report": report,
        "files": files,
        "warnings": list(dict.fromkeys(warnings)),
    }


def format_recognition_detail_text(payload: dict[str, object]) -> str:
    files = [item for item in payload.get("files", []) or [] if isinstance(item, dict)]
    first = files[0] if files else {}
    lines = [
        "识别详情",
        _record_title(files),
        f"当前状态：{payload.get('status') or '历史记录'}",
    ]
    if payload.get("is_current"):
        lines.append("说明：该识别记录将作为数据标准化的输入。")
    elif payload.get("is_legacy"):
        lines.append("说明：由旧版项目结构导入。")
    else:
        lines.append(f"说明：{payload.get('status_note') or '该识别记录当前不会被标准化模块使用。'}")
    lines.extend(
        [
            f"物种：{_species_text(first)}",
            f"基因 ID：{_gene_id_type_label(_gene_id_type(first))}",
            f"数据内容：{_content_summary(files)}",
            f"生成时间：{_format_datetime(str(payload.get('generated_at') or ''))}",
            "",
            "输入文件信息",
        ]
    )
    lines.extend(_file_info_lines(files, str(payload.get("run_id") or ""), str(payload.get("generated_at") or "")))
    lines.extend(["", "内容块识别结果"])
    lines.extend(_content_block_lines(files))
    lines.extend(["", "样本列与分组推断"])
    lines.extend(_sample_column_lines(files))
    lines.extend(["", "DEG comparison 识别"])
    lines.extend(_deg_lines(files))
    lines.extend(["", "Gene annotation 识别"])
    lines.extend(_annotation_lines(files))
    lines.extend(["", "物种与 gene ID 判断依据"])
    lines.extend(_species_evidence_lines(files))
    lines.extend(["", "Warning 与风险提示"])
    lines.extend(_warning_lines([str(item) for item in payload.get("warnings", []) or [] if str(item)]))
    lines.extend(["", "后续建议"])
    lines.extend(_next_step_lines(files))
    lines.extend(["", "技术详情折叠区摘要"])
    lines.extend(_technical_summary_lines(payload, files))
    return "\n".join(lines)


def format_recognition_report_markdown(payload: dict[str, object]) -> str:
    detail = format_recognition_detail_text(payload)
    technical = _technical_appendix(payload)
    return "\n".join(
        [
            "# BioMedPilot Recognition Detail Report",
            "",
            detail,
            "",
            "## Technical Appendix / 技术附录",
            "",
            "```json",
            technical,
            "```",
            "",
        ]
    )


def export_recognition_report_markdown(project_root: str | Path, run: dict[str, object], file_record: dict[str, object] | None = None) -> Path:
    root = Path(project_root).expanduser().resolve()
    payload = build_recognition_detail_payload(root, run, file_record)
    run_id = str(payload.get("run_id") or "current_session")
    run_dir = Path(str(run.get("run_dir") or ""))
    if not run_dir.is_absolute():
        run_dir = root / "recognized_data" / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    path = run_dir / "recognition_report_user.md"
    path.write_text(format_recognition_report_markdown(payload), encoding="utf-8")
    return path


def format_recognition_detail_technical(payload: dict[str, object]) -> str:
    return _technical_appendix(payload)


def _report_from_run(root: Path, run: dict[str, object]) -> dict[str, object]:
    embedded = run.get("recognition_report")
    if isinstance(embedded, dict):
        return embedded
    path = Path(str(run.get("recognition_report_path") or ""))
    if path and not path.is_absolute():
        path = root / path
    return _read_json(path)


def _read_json(path: Path) -> dict[str, object]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _record_title(files: list[dict[str, object]]) -> str:
    if len(files) == 1:
        item = files[0]
        return str(item.get("semantic_type_zh") or item.get("recognized_type_zh") or TYPE_LABELS.get(str(item.get("recognized_type") or "unknown"), "未知文件"))
    if any(item.get("semantic_type") == "rna_seq_integrated_result_table" for item in files):
        return "识别批次：包含 RNA-seq 综合表达结果表"
    return f"识别批次：{len(files)} 个文件"


def _species_text(item: dict[str, object]) -> str:
    return str(item.get("species") or _profile_value(item, "species") or "未检测到明确物种信息")


def _gene_id_type(item: dict[str, object]) -> str:
    return str(item.get("gene_id_type") or _profile_value(item, "gene_id_type") or "")


def _gene_id_type_label(value: str) -> str:
    return {
        "ensembl_mouse_gene_id": "Ensembl mouse gene ID",
        "ensembl_human_gene_id": "Ensembl human gene ID",
        "ensembl_mouse_transcript_id": "Ensembl mouse transcript ID",
        "ensembl_id": "Ensembl ID",
    }.get(value, value or "未检测到明确 gene ID 类型")


def _content_summary(files: list[dict[str, object]]) -> str:
    labels: list[str] = []
    for block in _all_blocks(files):
        block_type = str(block.get("block_type") or "")
        label = {
            "count_expression_matrix": "count 矩阵",
            "fpkm_expression_matrix": "FPKM 矩阵",
            "tpm_expression_matrix": "TPM 矩阵",
            "deg_comparisons": "差异分析结果",
            "gene_annotation": "基因注释",
            "gene_identifier": "gene identifier metadata",
        }.get(block_type)
        if label and label not in labels:
            labels.append(label)
    return "、".join(labels) if labels else "未检测到明确的数据内容块"


def _file_info_lines(files: list[dict[str, object]], run_id: str, generated_at: str) -> list[str]:
    if not files:
        return ["未记录输入文件。"]
    lines: list[str] = []
    for item in files:
        profile = item.get("content_profile") if isinstance(item.get("content_profile"), dict) else {}
        lines.extend(
            [
                f"- 文件名：{item.get('file_name') or '未记录'}",
                f"  文件路径：{_compact_path(str(item.get('original_path') or item.get('route_path') or '未记录'))}",
                f"  文件格式：{_file_format(item)}",
                f"  文件大小：{_format_file_size(item.get('file_size'))}",
                f"  行数 / 列数：{profile.get('sampled_row_count', '未记录')} / {profile.get('column_count', '未记录')}",
                f"  recognition run id：{run_id or '未记录'}",
                f"  识别时间：{_format_datetime(generated_at)}",
            ]
        )
    return lines


def _content_block_lines(files: list[dict[str, object]]) -> list[str]:
    blocks = _all_blocks(files)
    if not blocks:
        return ["未检测到明确的数据内容块。该文件可能是普通表格、未知结构或需要手动配置。"]
    lines: list[str] = []
    for block in blocks:
        block_type = str(block.get("block_type") or "")
        if block_type in {"count_expression_matrix", "fpkm_expression_matrix", "tpm_expression_matrix"}:
            raw_value_type = str(block.get("value_type") or block_type.split("_", 1)[0]).lower()
            value_label = {"count": "Count", "fpkm": "FPKM", "tpm": "TPM"}.get(raw_value_type, raw_value_type.upper())
            uses = "重新差异分析、标准化、QC" if raw_value_type == "count" else "表达展示、热图、相关性"
            note = "重新差异分析前需要确认分组" if raw_value_type == "count" else "不建议作为 DESeq2/edgeR 重新差异分析输入"
            lines.extend([f"{value_label} 表达矩阵", f"样本列：{block.get('sample_count') or len(block.get('sample_columns', []) or [])}", f"推断分组：{_join(block.get('inferred_groups', []) or []) or '未识别'}", f"用途：{uses}", f"注意：{note}"])
        elif block_type == "deg_comparisons":
            lines.extend(["已有差异分析结果", f"比较数量：{block.get('comparison_count') or 0}", "用途：DEG 浏览、火山图、富集分析输入", "来源：导入表格中的已有结果"])
        elif block_type == "gene_annotation":
            fields = [str(item) for item in block.get("annotation_fields", []) or []]
            lines.extend(["Gene annotation", f"字段数量：{len(fields)}", "用途：基因注释、protein-coding 筛选、报告展示"])
        elif block_type == "gene_identifier":
            lines.extend(["Gene identifier metadata", f"ID 类型：{_gene_id_type_label(str(block.get('gene_id_type') or ''))}", f"物种：{block.get('species') or '未检测到明确物种信息'}"])
    return lines


def _sample_column_lines(files: list[dict[str, object]]) -> list[str]:
    lines: list[str] = []
    for block in _all_blocks(files):
        if str(block.get("block_type") or "") not in {"count_expression_matrix", "fpkm_expression_matrix", "tpm_expression_matrix"}:
            continue
        columns = _safe_sample_columns([str(item) for item in block.get("sample_columns", []) or []])
        raw_value_type = str(block.get("value_type") or str(block.get("block_type") or "expression").split("_", 1)[0]).lower()
        value_type = {"count": "Count", "fpkm": "FPKM", "tpm": "TPM"}.get(raw_value_type, raw_value_type.upper())
        lines.append(f"{value_type} 矩阵样本列：")
        lines.extend(_preview_lines(columns, limit=6))
        groups = block.get("replicate_count_by_group") if isinstance(block.get("replicate_count_by_group"), dict) else {}
        sample_ids = [str(item) for item in block.get("inferred_sample_ids", []) or []]
        if groups:
            lines.append("推断分组：")
            lines.append("分组\t样本数\t样本")
            for group, count in groups.items():
                members = [sample for sample in sample_ids if _sample_group(sample) == str(group)]
                lines.append(f"{group}\t{count}\t{', '.join(members[:6])}")
            lines.append("推断分组需要用户确认。")
    return lines or ["未检测到表达矩阵样本列。"]


def _deg_lines(files: list[dict[str, object]]) -> list[str]:
    comparisons: list[dict[str, object]] = []
    for block in _all_blocks(files):
        if block.get("block_type") == "deg_comparisons":
            comparisons.extend(item for item in block.get("comparisons", []) or [] if isinstance(item, dict))
    if not comparisons:
        return ["未检测到 DEG comparisons。"]
    lines = ["比较\tlog2FC 列\tp value 列\tadjusted p value 列\t状态"]
    for comparison in comparisons:
        lines.append(
            "\t".join(
                [
                    str(comparison.get("comparison_name") or "未命名比较"),
                    str(comparison.get("log2fc_column") or "缺少"),
                    str(comparison.get("pvalue_column") or "缺少"),
                    str(comparison.get("padj_column") or "缺少"),
                    _comparison_status(comparison),
                ]
            )
        )
    if any(not item.get("is_complete") for item in comparisons):
        lines.append("不完整 comparison 可以查看，但部分筛选、火山图或富集输入可能不可用。")
    return lines


def _annotation_lines(files: list[dict[str, object]]) -> list[str]:
    fields: list[str] = []
    for block in _all_blocks(files):
        if block.get("block_type") == "gene_annotation":
            fields.extend(str(item) for item in block.get("annotation_fields", []) or [])
    if not fields:
        return ["未检测到 gene annotation 字段。"]
    fields = list(dict.fromkeys(fields))
    return [*fields, "这些字段将用于基因名称显示、基因描述、protein-coding 筛选和报告注释。", "annotation 字段不会混入 sample columns。"]


def _species_evidence_lines(files: list[dict[str, object]]) -> list[str]:
    if not files:
        return ["未检测到明确物种信息；不默认推断为 Homo sapiens。"]
    item = files[0]
    profile = item.get("content_profile") if isinstance(item.get("content_profile"), dict) else {}
    if profile.get("organism"):
        return [f"GEO organism 字段：{profile.get('organism')}", "优先级：GEO metadata organism 高于标题关键词推断", f"推断物种：{profile.get('species') or profile.get('organism')}"]
    gene_block = next((block for block in _blocks(item) if block.get("block_type") == "gene_identifier"), {})
    examples = [str(value) for value in gene_block.get("example_values", []) or [] if str(value)]
    gene_type = str(item.get("gene_id_type") or gene_block.get("gene_id_type") or "")
    species = str(item.get("species") or gene_block.get("species") or "")
    if examples and gene_type:
        prefix = _gene_id_prefix(gene_type, examples[0])
        return [f"检测到 gene_id 示例：{examples[0]}", f"识别规则：{prefix} 前缀对应 {_gene_id_type_label(gene_type)}", f"推断物种：{species or '未检测到明确物种信息'}"]
    return ["未检测到明确物种信息", "不默认推断为 Homo sapiens", "建议用户在项目配置或数据标准化阶段确认物种"]


def _warning_lines(warnings: list[str]) -> list[str]:
    if not warnings:
        return ["暂无识别警告"]
    return [f"{_warning_level(warning)}：{warning}" for warning in warnings]


def _next_step_lines(files: list[dict[str, object]]) -> list[str]:
    block_types = {str(block.get("block_type") or "") for block in _all_blocks(files)}
    species_group = str(files[0].get("species_group") or _profile_value(files[0], "species_group") or "") if files else ""
    lines: list[str] = []
    direct: list[str] = []
    confirm: list[str] = []
    if block_types:
        direct.append("数据标准化")
    if "deg_comparisons" in block_types:
        direct.extend(["DEG 结果浏览", "DEG 筛选", "富集分析输入"])
    if {"count_expression_matrix", "fpkm_expression_matrix", "tpm_expression_matrix"} & block_types:
        confirm.extend(["重新差异表达分析", "样本 QC", "分组比较设计"])
    if direct:
        lines.append("可直接进入：" + "、".join(dict.fromkeys(direct)))
    if confirm:
        lines.append("需要确认后进入：" + "、".join(dict.fromkeys(confirm)))
    if species_group == "mouse":
        lines.extend(["适合：小鼠动物模型分析、机制探索、方法验证", "不建议：直接作为人类临床队列分析；默认接入 TCGA/GTEx 人类对照"])
    return lines or ["需要补充明确的数据结构或手动配置后再进入后续流程。"]


def _technical_summary_lines(payload: dict[str, object], files: list[dict[str, object]]) -> list[str]:
    first = files[0] if files else {}
    return [
        f"file_kind：{first.get('file_kind') or first.get('recognized_type') or '未记录'}",
        f"semantic_type：{first.get('semantic_type') or _profile_value(first, 'semantic_type') or '未记录'}",
        f"species_group：{first.get('species_group') or _profile_value(first, 'species_group') or '未记录'}",
        f"gene_id_type：{_gene_id_type(first) or '未记录'}",
        f"recognition_report.json：{payload.get('recognition_report_path') or '未记录'}",
        f"recognized_files.json：{payload.get('recognized_files_path') or '未记录'}",
        f"current.json 指向状态：{'当前使用中' if payload.get('is_current') else '未指向该记录'}",
    ]


def _technical_appendix(payload: dict[str, object]) -> str:
    files = [item for item in payload.get("files", []) or [] if isinstance(item, dict)]
    summary = {
        "run_id": payload.get("run_id"),
        "status": payload.get("status"),
        "is_current": payload.get("is_current"),
        "is_legacy": payload.get("is_legacy"),
        "recognition_report_path": payload.get("recognition_report_path"),
        "recognized_files_path": payload.get("recognized_files_path"),
        "current_json_path": payload.get("current_json_path"),
        "files": [
            {
                "file_name": item.get("file_name"),
                "recognized_type": item.get("recognized_type"),
                "semantic_type": item.get("semantic_type"),
                "species": item.get("species") or _profile_value(item, "species"),
                "gene_id_type": _gene_id_type(item),
                "content_blocks": _blocks(item),
                "sample_columns": _safe_sample_columns([str(value) for value in (item.get("content_profile") or {}).get("sample_columns", [])]) if isinstance(item.get("content_profile"), dict) else [],
            }
            for item in files
        ],
        "warnings": payload.get("warnings", []),
    }
    return json.dumps(summary, ensure_ascii=False, indent=2, default=str)


def _all_blocks(files: list[dict[str, object]]) -> list[dict[str, object]]:
    return [block for item in files for block in _blocks(item)]


def _blocks(item: dict[str, object]) -> list[dict[str, object]]:
    blocks = item.get("content_blocks")
    if not isinstance(blocks, list):
        profile = item.get("content_profile")
        blocks = profile.get("content_blocks") if isinstance(profile, dict) else []
    return [block for block in blocks or [] if isinstance(block, dict)]


def _profile_value(item: dict[str, object], key: str) -> object:
    profile = item.get("content_profile")
    return profile.get(key) if isinstance(profile, dict) else ""

def _file_format(item: dict[str, object]) -> str:
    path = Path(str(item.get("file_name") or item.get("original_path") or ""))
    suffixes = "".join(path.suffixes).lower()
    if suffixes:
        return suffixes.lstrip(".").upper()
    return str(item.get("container_format") or item.get("recognized_type") or "未知")


def _format_file_size(value: object) -> str:
    try:
        size = float(value)
    except (TypeError, ValueError):
        return "未记录"
    units = ("bytes", "KB", "MB", "GB")
    index = 0
    while size >= 1024 and index < len(units) - 1:
        size /= 1024
        index += 1
    return f"{int(size)} bytes" if index == 0 else f"{size:.1f} {units[index]}"


def _compact_path(value: str, max_chars: int = 72) -> str:
    if len(value) <= max_chars:
        return value
    return "..." + value[-max_chars + 3 :]


def _format_datetime(value: str) -> str:
    if not value:
        return "未记录"
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone().strftime("%Y-%m-%d %H:%M")
    except ValueError:
        return value


def _join(values: object) -> str:
    if not isinstance(values, list):
        return ""
    return "、".join(str(value) for value in values if str(value).strip())


def _preview_lines(values: list[str], *, limit: int = 5) -> list[str]:
    if not values:
        return ["未记录。"]
    preview = values[:limit]
    lines = [*preview]
    remaining = len(values) - len(preview)
    if remaining > 0:
        lines.append(f"另有 {remaining} 列")
    return lines


def _safe_sample_columns(columns: list[str]) -> list[str]:
    return [column for column in columns if _is_expression_sample_column(column)]


def _is_expression_sample_column(column: str) -> bool:
    normalized = column.strip().lower()
    if not normalized:
        return False
    blocked_exact = {
        "gene_start",
        "gene_end",
        "gene_length",
        "gene_chr",
        "gene_strand",
        "gene_biotype",
        "gene_description",
        "tf_family",
        "log2foldchange",
        "log2fc",
        "logfc",
        "pvalue",
        "p_value",
        "p.value",
        "padj",
        "adj.p.val",
        "fdr",
        "qvalue",
    }
    if normalized in blocked_exact:
        return False
    blocked_suffixes = (
        "_log2foldchange",
        "_log2fc",
        "_logfc",
        "_pvalue",
        "_p_value",
        "_p.value",
        "_padj",
        "_adj.p.val",
        "_fdr",
        "_qvalue",
    )
    if normalized.endswith(blocked_suffixes):
        return False
    if normalized.startswith("gene_") and normalized not in {"gene_count", "gene_counts"}:
        return False
    return True


def _sample_group(sample_id: str) -> str:
    match = re.match(r"([A-Za-z]+)", sample_id)
    if match:
        return match.group(1)
    return sample_id


def _gene_id_prefix(gene_type: str, example: str) -> str:
    mapping = {
        "ensembl_mouse_gene_id": "ENSMUSG",
        "ensembl_human_gene_id": "ENSG",
        "ensembl_mouse_transcript_id": "ENSMUST",
    }
    if gene_type in mapping:
        return mapping[gene_type]
    match = re.match(r"([A-Za-z]+)", example)
    return match.group(1) if match else example


def _comparison_status(comparison: dict[str, object]) -> str:
    missing: list[str] = []
    if not comparison.get("log2fc_column"):
        missing.append("log2FC")
    if not comparison.get("pvalue_column"):
        missing.append("p value")
    if not comparison.get("padj_column"):
        missing.append("padj")
    if not missing and comparison.get("is_complete") is not False:
        return "完整"
    return "不完整：缺少 " + "、".join(missing or ["必要字段"])


def _warning_level(warning: str) -> str:
    lowered = warning.lower()
    if "无法" in warning or "未检测" in warning or "missing" in lowered:
        return "阻塞"
    if "确认" in warning or "分组" in warning:
        return "需要用户确认"
    if "count" in lowered or "fpkm" in lowered or "小鼠" in warning or "warning" in lowered:
        return "注意"
    return "信息"
