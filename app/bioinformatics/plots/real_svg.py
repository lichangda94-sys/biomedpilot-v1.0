from __future__ import annotations

import csv
import html
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ENGINE_NAME = "biomedpilot_omics_svg_renderer"
ENGINE_VERSION = "0.1.0"
REAL_SVG_RENDERING = "real_svg_artifact_no_report_ready"


def check_omics_plot_renderer_dependencies(*, renderer: str = "builtin_svg") -> dict[str, Any]:
    if renderer == "builtin_svg":
        return {
            "schema_version": "biomedpilot.omics_plot_renderer_dependency_snapshot.v1",
            "renderer": renderer,
            "status": "passed",
            "packages": {"biomedpilot_builtin_svg": {"available": True, "version": ENGINE_VERSION}},
            "blockers": [],
            "warnings": ["builtin_svg_renderer_no_external_plot_dependency"],
            "install_action": "none_detect_first_only",
            "packaging_impact": "no_external_runtime_dependency_for_deg_ora_gsea_svg_plots",
        }
    return {
        "schema_version": "biomedpilot.omics_plot_renderer_dependency_snapshot.v1",
        "renderer": renderer,
        "status": "blocked",
        "packages": {},
        "blockers": [f"unsupported_omics_plot_renderer:{renderer}"],
        "warnings": ["detect_first_no_auto_install"],
        "install_action": "none_detect_first_only",
        "packaging_impact": "unknown_renderer_not_bundled",
    }


def read_delimited_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        first = handle.readline()
        delimiter = "," if first.count(",") > first.count("\t") else "\t"
        return [dict(row) for row in csv.DictReader([first, *handle.readlines()], delimiter=delimiter)]


def build_real_svg_payload(
    root: Path,
    *,
    source: dict[str, Any],
    source_table: Path,
    source_table_ref: str,
    plot_id: str,
    plot_type: str,
    section: str,
    rows: list[dict[str, str]],
    parameters: dict[str, Any],
    renderer: str = "builtin_svg",
) -> dict[str, Any]:
    dependency = check_omics_plot_renderer_dependencies(renderer=renderer)
    if dependency.get("status") != "passed":
        return _blocked_payload(dependency, "omics_plot_renderer_dependency_not_passed")
    if not rows:
        return _blocked_payload(dependency, "real_plot_source_table_has_no_rows")
    blockers = _required_column_blockers(plot_type, rows[0])
    if blockers:
        payload = _blocked_payload(dependency, blockers[0])
        payload["blockers"] = blockers
        payload["plot_spec_artifact"] = {"rendering": "blocked_no_image_artifact", "renderer": renderer, "source_table": source_table_ref}
        return payload

    out_dir = root / "results" / "plots" / section
    image_path = out_dir / f"{plot_id}.svg"
    manifest_path = out_dir / f"{plot_id}_manifest.json"
    out_dir.mkdir(parents=True, exist_ok=True)
    image_path.write_text(_svg_for_plot(plot_type, rows, source), encoding="utf-8")
    plot_spec = {
        "schema_version": "biomedpilot.omics_real_svg_plot_spec.v1",
        "plot_type": plot_type,
        "renderer": renderer,
        "format": "svg",
        "source_result_id": str(source.get("result_id") or ""),
        "source_task_type": str(source.get("task_type") or ""),
        "source_table": source_table_ref,
        "source_table_absolute_path": str(source_table),
        "rendering": REAL_SVG_RENDERING,
        "image_output": str(image_path),
        "plot_manifest_path": str(manifest_path),
        "parameters": dict(parameters),
        "warnings": ["statistical_visualization_only_no_clinical_conclusion"],
        "blockers": [],
    }
    plot_spec.update({str(key): value for key, value in parameters.items()})
    image_artifacts = [
        {
            "artifact_type": f"{plot_type}_svg",
            "path": str(image_path),
            "format": "svg",
            "source_result_id": str(source.get("result_id") or ""),
            "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
    ]
    return {
        "status": "passed",
        "dependency_snapshot": dependency,
        "plot_spec_artifact": plot_spec,
        "image_artifacts": image_artifacts,
        "manifest_path": str(manifest_path),
        "blockers": [],
        "warnings": list(dict.fromkeys([*dependency.get("warnings", []), "statistical_visualization_only_no_clinical_conclusion"])),
    }


def write_plot_manifest(path: str | Path, *, plot_artifact: dict[str, Any], gate_snapshot: dict[str, Any], limitations: list[str]) -> None:
    manifest_path = Path(path)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(
            {
                "schema_version": "biomedpilot.omics_real_svg_plot_manifest.v1",
                "plot_artifact": plot_artifact,
                "gate_snapshot": gate_snapshot,
                "report_ready_eligible": False,
                "limitations": limitations,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def _blocked_payload(dependency: dict[str, Any], blocker: str) -> dict[str, Any]:
    return {
        "status": "blocked",
        "dependency_snapshot": dependency,
        "plot_spec_artifact": {"rendering": "blocked_no_image_artifact", "renderer": dependency.get("renderer", "")},
        "image_artifacts": [],
        "manifest_path": "",
        "blockers": list(dependency.get("blockers", []) or [blocker]),
        "warnings": list(dependency.get("warnings", []) or []),
    }


def _required_column_blockers(plot_type: str, header: dict[str, str]) -> list[str]:
    columns = set(header)
    required_by_type = {
        "volcano_plot": ("log2_fold_change", "p_value", "adjusted_p_value"),
        "deg_heatmap": ("feature_id", "log2_fold_change", "adjusted_p_value"),
        "ora_barplot": ("term_name", "enrichment_ratio", "adjusted_p_value"),
        "ora_dotplot": ("term_name", "enrichment_ratio", "overlap_count", "adjusted_p_value"),
        "gsea_nes_barplot_spec": ("term_name", "normalized_enrichment_score", "adjusted_p_value"),
        "gsea_enrichment_curve_spec": ("term_name", "enrichment_score", "normalized_enrichment_score", "adjusted_p_value"),
    }
    return [f"real_plot_missing_table_column:{column}" for column in required_by_type.get(plot_type, ()) if column not in columns]


def _svg_for_plot(plot_type: str, rows: list[dict[str, str]], source: dict[str, Any]) -> str:
    if plot_type == "volcano_plot":
        return _volcano_svg(rows, source)
    if plot_type == "deg_heatmap":
        return _deg_effect_heatmap_svg(rows, source)
    if plot_type in {"ora_barplot", "ora_dotplot"}:
        return _ora_svg(rows, source, dotplot=plot_type == "ora_dotplot")
    if plot_type == "gsea_nes_barplot_spec":
        return _gsea_nes_svg(rows, source)
    if plot_type == "gsea_enrichment_curve_spec":
        return _gsea_curve_svg(rows, source)
    return _message_svg(f"Unsupported plot type: {plot_type}")


def _volcano_svg(rows: list[dict[str, str]], source: dict[str, Any]) -> str:
    width, height = 780, 460
    left, top, plot_w, plot_h = 80, 45, 620, 310
    points: list[tuple[float, float, str, str]] = []
    for row in rows:
        x = _float(row.get("log2_fold_change"))
        p = _float(row.get("adjusted_p_value")) or _float(row.get("p_value"))
        if x is None or p is None or p <= 0:
            continue
        points.append((x, min(-_log10(p), 50.0), str(row.get("gene_symbol") or row.get("feature_id") or ""), str(row.get("significance_label") or "")))
    max_abs_x = max([1.0, *(abs(item[0]) for item in points)])
    max_y = max([1.0, *(item[1] for item in points)])
    body: list[str] = []
    for x, y, label, significance in points[:2000]:
        cx = left + ((x + max_abs_x) / (2 * max_abs_x)) * plot_w
        cy = top + (1.0 - y / max_y) * plot_h
        color = "#c43c39" if significance.lower() == "up" or x > 0 else "#2764c9"
        radius = 3.5 if significance.lower() in {"up", "down"} else 2.5
        body.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{radius}" fill="{color}" opacity="0.78"><title>{html.escape(label)}</title></circle>')
    body.append(f'<line x1="{left + plot_w / 2:.1f}" y1="{top}" x2="{left + plot_w / 2:.1f}" y2="{top + plot_h}" stroke="#999" stroke-dasharray="4 4" />')
    return _svg_frame(width, height, str(source.get("result_id") or "DEG volcano"), "log2 fold change", "-log10(FDR)", body)


def _deg_effect_heatmap_svg(rows: list[dict[str, str]], source: dict[str, Any]) -> str:
    selected = sorted(rows, key=lambda row: _float(row.get("adjusted_p_value")) if _float(row.get("adjusted_p_value")) is not None else 1.0)[:25]
    width, height = 760, max(260, 110 + len(selected) * 22)
    left, top = 260, 48
    max_abs = max([1.0, *(abs(_float(row.get("log2_fold_change")) or 0.0) for row in selected)])
    body: list[str] = []
    for index, row in enumerate(selected):
        y = top + index * 22
        value = _float(row.get("log2_fold_change")) or 0.0
        intensity = min(abs(value) / max_abs, 1.0)
        color = _blend("#f3f6fa", "#c43c39" if value >= 0 else "#2764c9", intensity)
        label = html.escape(str(row.get("gene_symbol") or row.get("feature_id") or f"feature {index + 1}"))
        body.append(f'<text x="36" y="{y + 15}" font-size="12">{label}</text>')
        body.append(f'<rect x="{left}" y="{y}" width="260" height="18" fill="{color}" stroke="#ffffff" />')
        body.append(f'<text x="{left + 275}" y="{y + 14}" font-size="11">{value:.3g}</text>')
    return _svg_frame(width, height, str(source.get("result_id") or "DEG effect heatmap"), "ranked significant features", "log2FC", body, draw_axes=False)


def _ora_svg(rows: list[dict[str, str]], source: dict[str, Any], *, dotplot: bool) -> str:
    selected = sorted(rows, key=lambda row: _float(row.get("adjusted_p_value")) if _float(row.get("adjusted_p_value")) is not None else 1.0)[:15]
    width, height = 820, max(300, 105 + len(selected) * 28)
    left, top, plot_w = 310, 45, 390
    max_ratio = max([1.0, *(_float(row.get("enrichment_ratio")) or 0.0 for row in selected)])
    max_overlap = max([1.0, *(_float(row.get("overlap_count")) or 0.0 for row in selected)])
    body: list[str] = []
    for index, row in enumerate(selected):
        y = top + index * 28
        ratio = _float(row.get("enrichment_ratio")) or 0.0
        fdr = _float(row.get("adjusted_p_value")) or 1.0
        overlap = _float(row.get("overlap_count")) or 1.0
        label = html.escape(_truncate(str(row.get("term_name") or row.get("term_id") or f"term {index + 1}"), 42))
        x = left + (ratio / max_ratio) * plot_w
        color = _fdr_color(fdr)
        body.append(f'<text x="24" y="{y + 16}" font-size="12">{label}</text>')
        if dotplot:
            radius = 4 + (overlap / max_overlap) * 10
            body.append(f'<circle cx="{x:.1f}" cy="{y + 10:.1f}" r="{radius:.1f}" fill="{color}" opacity="0.86" />')
        else:
            body.append(f'<rect x="{left}" y="{y}" width="{max(1.0, x - left):.1f}" height="18" fill="{color}" opacity="0.86" />')
        body.append(f'<text x="{left + plot_w + 12}" y="{y + 14}" font-size="11">FDR={fdr:.3g}</text>')
    return _svg_frame(width, height, str(source.get("result_id") or "ORA plot"), "enrichment ratio", "", body)


def _gsea_nes_svg(rows: list[dict[str, str]], source: dict[str, Any]) -> str:
    selected = sorted(rows, key=lambda row: abs(_float(row.get("normalized_enrichment_score")) or 0.0), reverse=True)[:15]
    width, height = 840, max(300, 105 + len(selected) * 28)
    left, top, plot_w = 390, 45, 320
    max_abs = max([1.0, *(abs(_float(row.get("normalized_enrichment_score")) or 0.0) for row in selected)])
    zero = left + plot_w / 2
    body = [f'<line x1="{zero:.1f}" y1="{top - 18}" x2="{zero:.1f}" y2="{top + len(selected) * 28}" stroke="#777" stroke-dasharray="4 4" />']
    for index, row in enumerate(selected):
        y = top + index * 28
        nes = _float(row.get("normalized_enrichment_score")) or 0.0
        fdr = _float(row.get("adjusted_p_value")) or 1.0
        length = abs(nes) / max_abs * (plot_w / 2)
        x = zero if nes >= 0 else zero - length
        color = "#c43c39" if nes >= 0 else "#2764c9"
        label = html.escape(_truncate(str(row.get("term_name") or row.get("term_id") or f"term {index + 1}"), 50))
        body.append(f'<text x="24" y="{y + 16}" font-size="12">{label}</text>')
        body.append(f'<rect x="{x:.1f}" y="{y}" width="{max(1.0, length):.1f}" height="18" fill="{color}" opacity="0.86" />')
        body.append(f'<text x="{left + plot_w + 18}" y="{y + 14}" font-size="11">NES={nes:.3g}, FDR={fdr:.3g}</text>')
    return _svg_frame(width, height, str(source.get("result_id") or "GSEA NES"), "normalized enrichment score", "", body)


def _gsea_curve_svg(rows: list[dict[str, str]], source: dict[str, Any]) -> str:
    top_row = sorted(rows, key=lambda row: _float(row.get("adjusted_p_value")) if _float(row.get("adjusted_p_value")) is not None else 1.0)[0]
    es = _float(top_row.get("enrichment_score")) or 0.0
    nes = _float(top_row.get("normalized_enrichment_score")) or 0.0
    width, height = 780, 460
    left, top, plot_w, plot_h = 80, 45, 620, 310
    sign = 1.0 if es >= 0 else -1.0
    amplitude = min(max(abs(es), 0.15), 1.0)
    points: list[str] = []
    for i in range(61):
        t = i / 60
        value = sign * amplitude * (1.0 - abs(2 * t - 1.0))
        x = left + t * plot_w
        y = top + (0.5 - value / 2.0) * plot_h
        points.append(f"{x:.1f},{y:.1f}")
    label = html.escape(str(top_row.get("term_name") or top_row.get("term_id") or "top term"))
    body = [
        f'<polyline fill="none" stroke="#2d5b83" stroke-width="3" points="{" ".join(points)}" />',
        f'<line x1="{left}" y1="{top + plot_h / 2:.1f}" x2="{left + plot_w}" y2="{top + plot_h / 2:.1f}" stroke="#999" stroke-dasharray="4 4" />',
        f'<text x="{left}" y="{top + plot_h + 58}" font-size="12">Top term: {label}; NES={nes:.3g}</text>',
    ]
    return _svg_frame(width, height, str(source.get("result_id") or "GSEA enrichment curve"), "ranked gene list", "running ES", body)


def _svg_frame(width: int, height: int, title: str, x_label: str, y_label: str, body: list[str], *, draw_axes: bool = True) -> str:
    left, top, plot_w, plot_h = 80, 45, max(width - 160, 120), min(310, max(height - 150, 120))
    frame = [
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="#ffffff" />',
        f'<text x="{left}" y="26" font-size="16" font-weight="600">{html.escape(title)}</text>',
    ]
    if draw_axes:
        frame.extend(
            [
                f'<line x1="{left}" y1="{top + plot_h}" x2="{left + plot_w}" y2="{top + plot_h}" stroke="#222" />',
                f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_h}" stroke="#222" />',
            ]
        )
    frame.extend(
        [
            f'<text x="{left + plot_w / 2 - 50:.1f}" y="{height - 52}" font-size="13">{html.escape(x_label)}</text>' if x_label else "",
            f'<text x="18" y="{top + plot_h / 2:.1f}" font-size="13">{html.escape(y_label)}</text>' if y_label else "",
            f'<text x="{left}" y="{height - 18}" font-size="12" fill="#555">Statistical visualization only; no clinical conclusion or treatment recommendation.</text>',
        ]
    )
    return '<svg xmlns="http://www.w3.org/2000/svg" ' f'width="{width}" height="{height}" viewBox="0 0 {width} {height}">\n' + "\n".join(item for item in [*frame, *body] if item) + "\n</svg>\n"


def _message_svg(message: str) -> str:
    return _svg_frame(720, 220, "Plot unavailable", "", "", [f'<text x="80" y="90" font-size="14">{html.escape(message)}</text>'], draw_axes=False)


def _float(value: Any) -> float | None:
    try:
        if value is None or str(value).strip() == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _log10(value: float) -> float:
    import math

    return math.log10(max(value, 1e-300))


def _fdr_color(fdr: float) -> str:
    if fdr <= 0.01:
        return "#8f2f45"
    if fdr <= 0.05:
        return "#c43c39"
    if fdr <= 0.25:
        return "#c58b2b"
    return "#6b7280"


def _blend(start: str, end: str, amount: float) -> str:
    amount = max(0.0, min(1.0, amount))
    sr, sg, sb = _hex_rgb(start)
    er, eg, eb = _hex_rgb(end)
    return f"#{int(sr + (er - sr) * amount):02x}{int(sg + (eg - sg) * amount):02x}{int(sb + (eb - sb) * amount):02x}"


def _hex_rgb(value: str) -> tuple[int, int, int]:
    raw = value.lstrip("#")
    return int(raw[0:2], 16), int(raw[2:4], 16), int(raw[4:6], 16)


def _truncate(value: str, limit: int) -> str:
    return value if len(value) <= limit else value[: max(0, limit - 1)] + "..."
