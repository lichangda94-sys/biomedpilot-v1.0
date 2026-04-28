"""Small helpers for optional Module 4 routing from the main GUI."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable


ApiCall = Callable[..., dict[str, Any]]


def response_results(response: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not isinstance(response, dict):
        return []
    data = response.get("data")
    if not isinstance(data, dict):
        return []
    results = data.get("results")
    return [dict(record) for record in results] if isinstance(results, list) else []


def locator_kind(record: dict[str, Any]) -> str:
    metadata = record.get("metadata")
    metadata = metadata if isinstance(metadata, dict) else {}
    if record.get("local_path") or metadata.get("local_path"):
        return "local_path"
    if record.get("download_url") or metadata.get("download_url"):
        return "download_url"
    return "missing_locator"


def locator_display_text(kind: str) -> str:
    labels = {
        "local_path": "local_path (ready for local copy)",
        "download_url": "download_url (ready for mockable HTTP download)",
        "missing_locator": "missing_locator (cannot download until a local_path/download_url is available)",
    }
    return labels.get(kind, f"{kind} (unsupported locator)")


def locator_summary(records: list[dict[str, Any]]) -> dict[str, Any]:
    counts = {"local_path": 0, "download_url": 0, "missing_locator": 0}
    for record in records:
        kind = locator_kind(record)
        counts[kind] = counts.get(kind, 0) + 1
    runnable_count = counts.get("local_path", 0) + counts.get("download_url", 0)
    return {
        "total": len(records),
        "runnable_count": runnable_count,
        "missing_locator_count": counts.get("missing_locator", 0),
        "counts_by_locator": counts,
        "all_missing_locator": bool(records) and runnable_count == 0,
        "has_records": bool(records),
    }


def records_by_study(records: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        study_id = str(record.get("study_id") or "").strip()
        if not study_id:
            continue
        grouped.setdefault(study_id, []).append(record)
    return grouped


def first_runtime_candidate(grouped_records: dict[str, list[dict[str, Any]]]) -> tuple[str, list[dict[str, Any]]] | None:
    for study_id, records in grouped_records.items():
        if records:
            return study_id, records
    return None


def build_runtime_action_state(grouped_records: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    candidate = first_runtime_candidate(grouped_records)
    if candidate is None:
        return {
            "enabled": False,
            "study_id": "",
            "record_count": 0,
            "runnable_count": 0,
            "missing_locator_count": 0,
            "button_text": "运行 TCGA/GTEx 最小 runtime",
            "help_text": "先执行 TCGA/GTEx 查询分流，解析到文件候选后再运行可选 runtime。",
        }

    study_id, records = candidate
    summary = locator_summary(records)
    if summary["runnable_count"] > 0:
        button_text = f"运行 {study_id} 最小 runtime"
        help_text = (
            f"{study_id}: {summary['runnable_count']} 个候选带 locator，"
            f"{summary['missing_locator_count']} 个缺 locator。"
        )
    else:
        button_text = f"尝试 {study_id} runtime（缺 locator）"
        help_text = (
            f"{study_id}: 当前 {summary['total']} 个候选都缺 "
            "local_path/download_url/metadata locator，运行会明确 failed。"
        )

    return {
        "enabled": True,
        "study_id": study_id,
        "record_count": summary["total"],
        "runnable_count": summary["runnable_count"],
        "missing_locator_count": summary["missing_locator_count"],
        "button_text": button_text,
        "help_text": help_text,
    }


def build_mainline_summary(search_result: dict[str, Any], resolve_result: dict[str, Any], *, limit: int = 8) -> str:
    study_records = response_results(search_result)
    file_records = response_results(resolve_result)
    grouped = records_by_study(file_records)
    locators = locator_summary(file_records)
    runtime_state = build_runtime_action_state(grouped)
    source_groups = (search_result.get("data") or {}).get("results_by_source", {}) if isinstance(search_result, dict) else {}
    warnings = []
    for response in (search_result, resolve_result):
        raw_warnings = response.get("warnings", []) if isinstance(response, dict) else []
        warnings.extend(str(item) for item in raw_warnings if item)

    lines = [
        "TCGA/GTEx 查询分流结果（可选路径，不进入 GEO workflow）",
        f"- search: {search_result.get('status', 'unknown')} | {search_result.get('message', '')}",
        f"- resolve: {resolve_result.get('status', 'unknown')} | {resolve_result.get('message', '')}",
        f"- study records: {len(study_records)} | file candidates: {len(file_records)} | studies with files: {len(grouped)}",
        (
            "- locator readiness: "
            f"local_path={locators['counts_by_locator'].get('local_path', 0)}, "
            f"download_url={locators['counts_by_locator'].get('download_url', 0)}, "
            f"missing_locator={locators['missing_locator_count']}"
        ),
        f"- default runtime target: {runtime_state['study_id'] or 'none'}",
        f"- runtime button: {runtime_state['help_text']}",
        "- runtime scope: optional minimal local/mockable runtime; not a production TCGA/GDC/GTEx downloader.",
    ]

    if isinstance(source_groups, dict) and source_groups:
        tcga_count = len(source_groups.get("tcga_gdc", []) or [])
        gtex_count = len(source_groups.get("gtex", []) or [])
        lines.append(f"- source groups: TCGA/GDC={tcga_count}, GTEx={gtex_count}")

    if file_records:
        lines.append("")
        lines.append("Resolved file candidates:")
        for record in file_records[:limit]:
            lines.append(
                "  - "
                f"{record.get('study_id', 'unknown')} | "
                f"{record.get('source', 'unknown')} | "
                f"{record.get('guessed_role') or record.get('file_type') or 'data'} | "
                f"{record.get('file_name') or record.get('file_id') or 'unnamed'} | "
                f"locator={locator_display_text(locator_kind(record))}"
            )
        if len(file_records) > limit:
            lines.append(f"  - ... {len(file_records) - limit} more")
    else:
        lines.append("")
        lines.append("Resolved file candidates: none")

    if warnings:
        lines.append("")
        lines.append("Warnings:")
        for warning in dict.fromkeys(warnings):
            lines.append(f"  - {warning}")

    return "\n".join(lines)


def run_minimal_runtime(
    study_id: str,
    out_dir: str | Path,
    records: list[dict[str, Any]],
    *,
    download_fn: ApiCall | None = None,
    build_fn: ApiCall | None = None,
    summary_fn: ApiCall | None = None,
) -> dict[str, Any]:
    if download_fn is None or build_fn is None or summary_fn is None:
        from tcga_gtex import build_tcga_gtex_bundle, download_tcga_gtex_dataset, get_tcga_gtex_summary

        download_fn = download_fn or download_tcga_gtex_dataset
        build_fn = build_fn or build_tcga_gtex_bundle
        summary_fn = summary_fn or get_tcga_gtex_summary

    if not study_id or not records:
        return {
            "status": "failed",
            "stage": "input",
            "message": "No resolved TCGA/GTEx records are available for the runtime action.",
            "study_id": study_id,
            "output_dir": str(out_dir),
        }

    download_result = download_fn(study_id, str(out_dir), options={"resolved_records": records})
    if download_result.get("status") != "success":
        return {
            "status": "failed",
            "stage": "download",
            "message": download_result.get("message", "TCGA/GTEx download failed."),
            "study_id": study_id,
            "output_dir": download_result.get("output_dir") or str(out_dir),
            "download_result": download_result,
        }

    bundle_result = build_fn(download_result.get("output_dir") or str(out_dir))
    if bundle_result.get("status") != "success":
        return {
            "status": "failed",
            "stage": "bundle",
            "message": bundle_result.get("message", "TCGA/GTEx bundle build failed."),
            "study_id": study_id,
            "output_dir": bundle_result.get("output_dir") or download_result.get("output_dir") or str(out_dir),
            "download_result": download_result,
            "bundle_result": bundle_result,
        }

    summary_result = summary_fn(bundle_result.get("output_dir") or download_result.get("output_dir") or str(out_dir))
    if summary_result.get("status") != "success":
        return {
            "status": "failed",
            "stage": "summary",
            "message": summary_result.get("message", "TCGA/GTEx summary read failed."),
            "study_id": study_id,
            "output_dir": summary_result.get("output_dir") or bundle_result.get("output_dir") or str(out_dir),
            "download_result": download_result,
            "bundle_result": bundle_result,
            "summary_result": summary_result,
        }

    return {
        "status": "success",
        "stage": "summary",
        "message": "TCGA/GTEx minimal runtime completed.",
        "study_id": study_id,
        "output_dir": summary_result.get("output_dir") or bundle_result.get("output_dir") or str(out_dir),
        "download_result": download_result,
        "bundle_result": bundle_result,
        "summary_result": summary_result,
    }


def build_runtime_message(result: dict[str, Any]) -> str:
    status = result.get("status", "unknown")
    stage = result.get("stage", "unknown")
    lines = [
        "",
        "TCGA/GTEx runtime action",
        f"- status: {status}",
        f"- stage: {stage}",
        f"- study_id: {result.get('study_id', '')}",
        f"- output_dir: {result.get('output_dir', '')}",
        f"- message: {result.get('message', '')}",
    ]

    if status == "failed" and stage == "download":
        download_result = result.get("download_result") or {}
        lines.append("- what to check: file candidates need local_path, download_url, or metadata locator.")
        for record in ((download_result.get("data") or {}).get("records") or [])[:6]:
            lines.append(
                "  - "
                f"{record.get('file_name') or 'unnamed'} | "
                f"status={record.get('status')} | "
                f"locator={record.get('locator_type') or 'missing_locator'} | "
                f"{record.get('error_message') or download_result.get('message', '')}"
            )

    if status == "success":
        summary = ((result.get("summary_result") or {}).get("data") or {}).get("summary") or {}
        lines.append(f"- files: {summary.get('input_file_count', 0)}")
        study_ids = summary.get("study_ids") or []
        if study_ids:
            lines.append(f"- summary studies: {', '.join(study_ids)}")

    return "\n".join(lines)


__all__ = [
    "build_mainline_summary",
    "build_runtime_message",
    "build_runtime_action_state",
    "first_runtime_candidate",
    "locator_display_text",
    "locator_kind",
    "locator_summary",
    "records_by_study",
    "response_results",
    "run_minimal_runtime",
]
