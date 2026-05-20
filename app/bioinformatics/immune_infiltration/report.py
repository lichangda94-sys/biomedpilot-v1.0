from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from .linkage_preflight import build_linkage_preflight
from .scoring import latest_immune_scoring_manifest_path


def generate_immune_tme_report(
    project_root: str | Path,
    *,
    manifest_path: str | Path | None = None,
    linkage_preflight: dict[str, Any] | None = None,
) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    selected_manifest = Path(manifest_path).expanduser().resolve() if manifest_path else latest_immune_scoring_manifest_path(root)
    if selected_manifest is None or not selected_manifest.is_file():
        raise FileNotFoundError("未找到 immune / TME scoring manifest。")
    manifest = _read_json(selected_manifest)
    score_path = Path(str(manifest.get("score_matrix_path") or ""))
    coverage_path = Path(str(manifest.get("signature_gene_coverage_path") or ""))
    if linkage_preflight is None:
        linkage_preflight = build_linkage_preflight(
            root,
            score_matrix_path=score_path,
            expression_matrix_path=manifest.get("input_expression_matrix_path"),
        )
    report_path = Path(str(manifest.get("report_path") or selected_manifest.with_name("immune_tme_scoring_report.md")))
    coverage_summary = _coverage_summary(coverage_path)
    score_preview = _score_preview(score_path)
    text = _render_report(manifest, coverage_summary, score_preview, linkage_preflight)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(text, encoding="utf-8")
    return {
        "status": "created",
        "report_path": str(report_path),
        "manifest_path": str(selected_manifest),
        "coverage_summary": coverage_summary,
        "linkage_preflight": linkage_preflight,
    }


def _render_report(
    manifest: dict[str, Any],
    coverage_summary: dict[str, Any],
    score_preview: list[dict[str, str]],
    linkage_preflight: dict[str, Any],
) -> str:
    lines = [
        "# Immune / TME Signature Scoring Report Draft",
        "",
        f"Generated at: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "## Scope",
        "",
        "This is an exploratory bulk expression signature scoring draft. It is not a clinical conclusion and it does not run DEG, GSEA, KM, Cox, or log-rank analysis.",
        "",
        "## Input",
        "",
        f"- Dataset: {manifest.get('dataset_label') or manifest.get('dataset_id') or 'unknown'}",
        f"- Value type: {manifest.get('input_value_type') or 'unknown'}",
        f"- Scoring method: {manifest.get('scoring_method')}",
        f"- Transform: {manifest.get('value_transform')}",
        f"- Samples: {manifest.get('sample_count')}",
        f"- Genes: {manifest.get('gene_count')}",
        "",
        "## Signature Coverage",
        "",
        f"- Signatures selected: {manifest.get('signature_count')}",
        f"- Signatures scored: {manifest.get('scored_signature_count')}",
        f"- Coverage status: {coverage_summary}",
        "",
        "## Score Preview",
        "",
    ]
    if score_preview:
        headers = list(score_preview[0].keys())
        lines.append("| " + " | ".join(headers) + " |")
        lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
        for row in score_preview[:10]:
            lines.append("| " + " | ".join(str(row.get(header, "")) for header in headers) + " |")
    else:
        lines.append("No score rows available.")
    lines.extend(
        [
            "",
            "## Linkage Preflight",
            "",
            f"- Group comparison: {linkage_preflight.get('group_comparison', {}).get('status', 'unknown')}",
            f"- Target gene correlation: {linkage_preflight.get('target_gene_correlation', {}).get('status', 'unknown')}",
            f"- Clinical association: {linkage_preflight.get('clinical_association', {}).get('status', 'unknown')}",
            "",
            "## Limitations",
            "",
        ]
    )
    for limitation in manifest.get("limitations", []) or []:
        lines.append(f"- {limitation}")
    lines.extend(
        [
            "- TCGA + GTEx is not automatically merged and GTEx is not automatically used as a TCGA normal control.",
            "- This draft is not report-ready and should remain behind downstream preflight checks.",
            "",
        ]
    )
    return "\n".join(lines)


def _coverage_summary(path: Path) -> dict[str, int]:
    summary: dict[str, int] = {}
    if not path.is_file():
        return summary
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        for row in reader:
            status = str(row.get("status") or "unknown")
            summary[status] = summary.get(status, 0) + 1
    return dict(sorted(summary.items()))


def _score_preview(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        return [dict(row) for _, row in zip(range(5), reader)]


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


__all__ = ["generate_immune_tme_report"]
