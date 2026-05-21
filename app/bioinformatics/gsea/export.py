from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from .review import GSEA_REVIEW_COLUMNS, build_gsea_result_review


EXPORT_DIR = Path("results") / "exports" / "gsea_review"


def export_gsea_review_table(
    project_root: str | Path,
    *,
    result_id: str | None = None,
    file_format: str = "tsv",
) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    review = build_gsea_result_review(root, result_id=result_id, sort_by="input_order", significance_filter="all")
    if review.get("status") != "passed":
        return {"status": "blocked", "blockers": list(review.get("blockers", []) or []), "warnings": []}
    selected_result_id = str(review.get("selected_result_id") or "gsea")
    normalized_format = "csv" if str(file_format).lower() == "csv" else "tsv"
    delimiter = "," if normalized_format == "csv" else "\t"
    export_path = root / EXPORT_DIR / f"{selected_result_id}_review.{normalized_format}"
    export_path.parent.mkdir(parents=True, exist_ok=True)
    with export_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(GSEA_REVIEW_COLUMNS), delimiter=delimiter)
        writer.writeheader()
        for row in review.get("rows", []) or []:
            if isinstance(row, dict):
                writer.writerow({column: row.get(column, "") for column in GSEA_REVIEW_COLUMNS})
    return {
        "status": "passed",
        "export_path": str(export_path),
        "file_format": normalized_format,
        "result_id": selected_result_id,
        "row_count": len(review.get("rows", []) or []),
        "report_ready_eligible": False,
        "plot_artifacts": [],
        "report_artifacts": [],
        "blockers": [],
        "warnings": ["gsea_export_table_only_not_report_ready"],
    }
