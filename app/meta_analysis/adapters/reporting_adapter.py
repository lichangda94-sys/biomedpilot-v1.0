from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ReportDraft:
    title: str
    markdown: str
    summary: str
    source_runnable: bool


class ReportingAdapter:
    def build_analysis_preflight_report(self, payload: dict[str, object]) -> ReportDraft:
        preflight = payload.get("preflight")
        preflight_payload = preflight if isinstance(preflight, dict) else {}
        project_id = str(payload.get("project_id", ""))
        batch_id = str(payload.get("batch_id", ""))
        runnable = bool(preflight_payload.get("runnable", False))
        blocking_errors = list(preflight_payload.get("blocking_errors", []))
        warnings = list(preflight_payload.get("warnings", []))
        title = "BioMedPilot Meta Analysis Preflight Report"
        markdown = "\n".join(
            [
                f"# {title}",
                "",
                "This testing report summarizes Analysis preflight readiness only.",
                "It is not a formal systematic review report and no pooled meta-analysis was executed.",
                "",
                "## Source",
                "",
                f"- Project ID: {project_id}",
                f"- Batch ID: {batch_id}",
                f"- Statistical analysis executed: {payload.get('statistical_analysis_executed', False)}",
                "",
                "## Readiness",
                "",
                f"- Runnable: {'yes' if runnable else 'no'}",
                f"- Extraction records: {preflight_payload.get('extraction_records', 0)}",
                f"- Outcome records: {preflight_payload.get('outcome_records', 0)}",
                f"- Valid outcome records: {preflight_payload.get('valid_outcome_records', 0)}",
                f"- Recommended action: {preflight_payload.get('recommended_action', '')}",
                "",
                "## Blocking Items",
                "",
                *(f"- {item}" for item in blocking_errors),
                *([] if blocking_errors else ["- None"]),
                "",
                "## Warnings",
                "",
                *(f"- {item}" for item in warnings),
                *([] if warnings else ["- None"]),
                "",
            ]
        )
        summary = (
            "Analysis preflight report generated; statistics are ready to run."
            if runnable
            else "Analysis preflight report generated; statistics are not ready yet."
        )
        return ReportDraft(title=title, markdown=markdown, summary=summary, source_runnable=runnable)
