from __future__ import annotations

import argparse
import json
import subprocess
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
PROJECT_CONTROL = REPO_ROOT / "docs" / "project-control"

DEFAULT_JSON = PROJECT_CONTROL / "UI_ROUTE_CONTRACT_BIO_C1_CLOSURE_MATRIX.json"
DEFAULT_MARKDOWN = PROJECT_CONTROL / "UI_ROUTE_CONTRACT_BIO_C1_CLOSURE_MATRIX.md"

INPUTS = {
    "batch4_formal_deg": PROJECT_CONTROL / "UI_ROUTE_CONTRACT_BIO_BATCH4_FORMAL_DEG.json",
    "batch5_enrichment": PROJECT_CONTROL / "UI_ROUTE_CONTRACT_BIO_BATCH5_ENRICHMENT.json",
    "batch6_survival": PROJECT_CONTROL / "UI_ROUTE_CONTRACT_BIO_BATCH6_SURVIVAL.json",
    "batch7_report_export": PROJECT_CONTROL / "UI_ROUTE_CONTRACT_BIO_BATCH7_REPORT_EXPORT.json",
    "batch8_visible_buttons": PROJECT_CONTROL / "UI_ROUTE_CONTRACT_BIO_BATCH8_VISIBLE_BUTTONS.json",
    "batch9_data_prep_adapters": PROJECT_CONTROL / "UI_ROUTE_CONTRACT_BIO_BATCH9_DATA_PREP_ADAPTERS.json",
    "batch10_geo_online_retrieval": PROJECT_CONTROL / "UI_ROUTE_CONTRACT_BIO_BATCH10_GEO_ONLINE_RETRIEVAL.json",
    "batch11_tcga_gtex_adapters": PROJECT_CONTROL / "UI_ROUTE_CONTRACT_BIO_BATCH11_TCGA_GTEX_ADAPTERS.json",
    "batch12_tcga_gtex_light_validation": PROJECT_CONTROL / "UI_ROUTE_CONTRACT_BIO_BATCH12_TCGA_GTEX_LIGHT_VALIDATION.json",
}

PAGE_BASELINES = {
    "project_home": {
        "ui_page": "Project Home",
        "visual_baseline": "UIShell 7-step Bio high-fidelity gated shell",
        "source_branch": "codex/integration-labtools-ui-c2-carryover",
        "source_commits": ["08e9bd1", "900ba60", "2063ce8", "74c19ad"],
    },
    "data_source": {
        "ui_page": "Data Source",
        "visual_baseline": "UIShell 7-step Bio high-fidelity gated shell",
        "source_branch": "codex/integration-labtools-ui-c2-carryover",
        "source_commits": ["08e9bd1", "900ba60", "2063ce8", "74c19ad"],
    },
    "data_check_preparation": {
        "ui_page": "Data Check & Preparation",
        "visual_baseline": "UIShell 7-step Bio high-fidelity gated shell",
        "source_branch": "codex/integration-labtools-ui-c2-carryover",
        "source_commits": ["08e9bd1", "62739aa", "2063ce8", "74c19ad"],
    },
    "group_design": {
        "ui_page": "Group & Design",
        "visual_baseline": "UIShell 7-step Bio high-fidelity gated shell",
        "source_branch": "codex/integration-labtools-ui-c2-carryover",
        "source_commits": ["08e9bd1", "62739aa", "2063ce8", "74c19ad"],
    },
    "analysis_tasks": {
        "ui_page": "Analysis Tasks",
        "visual_baseline": "UIShell 7-step Bio high-fidelity gated shell",
        "source_branch": "codex/integration-labtools-ui-c2-carryover",
        "source_commits": ["08e9bd1", "4061d72", "2063ce8", "74c19ad"],
    },
    "result_report": {
        "ui_page": "Result & Report",
        "visual_baseline": "UIShell 7-step Bio high-fidelity gated shell",
        "source_branch": "codex/integration-labtools-ui-c2-carryover",
        "source_commits": ["08e9bd1", "2d5a560", "2063ce8", "74c19ad"],
    },
    "report_export": {
        "ui_page": "Report Export",
        "visual_baseline": "UIShell 7-step Bio high-fidelity gated shell",
        "source_branch": "codex/integration-labtools-ui-c2-carryover",
        "source_commits": ["08e9bd1", "2d5a560", "2063ce8", "74c19ad"],
    },
}

CAPABILITY_MATRIX = [
    {
        "ui_page": "Project Home",
        "requirement": "Project shell, project create/open/current-project routing",
        "status": "connected",
        "evidence_batches": ["batch8_visible_buttons"],
        "button_contracts": ["BIO-BATCH8-PROJECT_HOME"],
        "backend_capability": "app.bioinformatics.project_home / BioinformaticsWorkspaceWidget route adapters",
        "current_strategy": "Mature page retained; visible buttons live-clicked or explicitly disabled.",
        "remaining_gap": "Project Center recent-project backend is still placeholder and must not be treated as connected.",
    },
    {
        "ui_page": "Data Source",
        "requirement": "GEO / Local / TCGA / GTEx entry points connect to acquisition/retrieval/recognition, not direct analysis",
        "status": "partial",
        "evidence_batches": ["batch8_visible_buttons", "batch9_data_prep_adapters", "batch10_geo_online_retrieval", "batch11_tcga_gtex_adapters", "batch12_tcga_gtex_light_validation"],
        "button_contracts": [
            "BIO-BATCH8-DATA_SOURCE",
            "BIO-B9-ACQUISITION-REGISTER-LOCAL",
            "BIO-B9-DATA-SOURCE-LOCAL-DRAFT",
            "BIO-B10-GSE6004-DOWNLOAD-GEO-ASSETS",
            "BIO-B10-GSE153659-DOWNLOAD-GEO-ASSETS",
            "BIO-B11-TCGA-METADATA-PREVIEW",
            "BIO-B11-TCGA-DOWNLOAD-PLAN",
            "BIO-B11-GTEX-METADATA-PREVIEW",
            "BIO-B11-GTEX-DOWNLOAD-PLAN",
            "BIO-B12-LIGHT-TCGA-LIGHT-DOWNLOAD-GATE",
            "BIO-B12-LIGHT-TCGA-EXPRESSION-BUILD-GATE",
            "BIO-B12-LIGHT-GTEX-LIGHT-DOWNLOAD-GATE",
            "BIO-B12-LIGHT-GTEX-EXPRESSION-BUILD-GATE",
        ],
        "backend_capability": "create_data_source_request; register_acquisition; local source manifest handoff; TCGAMetadataPreviewService; GTExMetadataPreviewService; TCGA/GTEx download plan draft writers; TCGADownloadPlanExecutor; GTExDownloadPlanExecutor; TCGA/GTEx expression builders",
        "current_strategy": "All four source buttons write request drafts; Local has adapter proof into acquisition and recognition chain; visible GEO adapter live-click downloads GSE6004/GSE153659 metadata and assets; visible TCGA/GTEx adapter live-clicks metadata preview, download-plan artifacts, light-validation download receipts, and expression build manifests.",
        "remaining_gap": "TCGA/GTEx light-validation build outputs still need Data Check recognition/readiness live-click evidence before claiming complete external data import coverage.",
    },
    {
        "ui_page": "Data Check & Preparation",
        "requirement": "Data recognition, dependency/readiness detection, and preflight artifacts",
        "status": "connected",
        "evidence_batches": ["batch8_visible_buttons", "batch9_data_prep_adapters"],
        "button_contracts": [
            "BIO-B9-DATA-CHECK-RUN-RECOGNITION",
            "BIO-B9-DATA-CHECK-RUN-READINESS",
            "BIO-B9-DATA-CHECK-OPEN-STANDARDIZATION",
            "BIO-B9-DATA-CHECK-GENERATE-STANDARDIZED-ASSETS",
        ],
        "backend_capability": "project_recognition; project_readiness; project_standardization",
        "current_strategy": "Buttons write recognition, readiness, capability matrix, standardized asset, analysis-ready, and repository manifests.",
        "remaining_gap": "TCGA/GTEx metadata preview, light download, and expression build are proven; recognition/readiness of the built TCGA/GTEx outputs still needs a separate gated validation batch.",
    },
    {
        "ui_page": "Group & Design",
        "requirement": "Group/comparison/covariate state and blocker handling",
        "status": "connected",
        "evidence_batches": ["batch8_visible_buttons", "batch9_data_prep_adapters"],
        "button_contracts": [
            "BIO-B9-GROUP-DESIGN-SUGGEST-COMPARISON",
            "BIO-B9-GROUP-DESIGN-SAVE-CONFIRMED-DESIGN",
            "BIO-B9-GROUP-DESIGN-CONTINUE-ANALYSIS-TASKS",
        ],
        "backend_capability": "group_comparison_design build/save adapters",
        "current_strategy": "Suggestion/save/continue buttons live-clicked and artifact-verified.",
        "remaining_gap": "Expanded covariate modeling remains gate-scoped unless current design manifest proves the schema.",
    },
    {
        "ui_page": "Analysis Tasks",
        "requirement": "Formal DEG, ORA/GSEA, survival/clinical task gates",
        "status": "partial",
        "evidence_batches": ["batch4_formal_deg", "batch5_enrichment", "batch6_survival", "batch8_visible_buttons"],
        "button_contracts": [
            "BIO-FORMAL-DEG-DEPENDENCY-DETECT",
            "BIO-FORMAL-DEG-PARAMETER-CONFIRM",
            "BIO-FORMAL-DEG-CONTROLLED-RUN",
            "BIO-ENRICHMENT-RUN-PREFLIGHT",
            "BIO-ENRICHMENT-DETECT-R-BACKEND",
            "BIO-SURVIVAL-RUN-PREFLIGHT",
            "BIO-SURVIVAL-DETECT-BACKEND",
        ],
        "backend_capability": "formal DEG executor; EnrichmentService preflight/detect; SurvivalService preflight/detect",
        "current_strategy": "Formal DEG positive path is connected; enrichment and survival preflight/detect are connected; formal ORA/GSEA and KM/Cox/risk-score remain disabled with reasons.",
        "remaining_gap": "Formal ORA/GSEA executor and survival KM/log-rank/Cox/risk-score/report-ready execution are intentionally not enabled.",
    },
    {
        "ui_page": "Result & Report",
        "requirement": "DEG review, plot, report draft, result index, artifact registry",
        "status": "connected",
        "evidence_batches": ["batch4_formal_deg", "batch7_report_export", "batch8_visible_buttons"],
        "button_contracts": [
            "BIO-FORMAL-DEG-RESULT-REVIEW",
            "BIO-FORMAL-DEG-REVIEW-CSV-EXPORT",
            "BIO-FORMAL-DEG-PLOT-ARTIFACT",
            "BIO-FORMAL-DEG-REPORT-READY-PACKAGE",
            "BIO-RESULT-REPORT-REFRESH-CROSS-GATE",
        ],
        "backend_capability": "result index loader; formal DEG review/export/plot/report-ready adapters",
        "current_strategy": "Formal DEG result review, table export, plot artifact, and report-ready package are live-click verified.",
        "remaining_gap": "ORA/GSEA and survival preflight artifacts are not promoted into formal result rows.",
    },
    {
        "ui_page": "Report Export",
        "requirement": "Report-ready gate and export only after gate passes",
        "status": "connected",
        "evidence_batches": ["batch4_formal_deg", "batch7_report_export", "batch8_visible_buttons"],
        "button_contracts": [
            "BIO-FORMAL-DEG-REPORT-EXPORT-GATE",
            "BIO-REPORT-EXPORT-DRAFT-CROSS-GATE",
            "BIO-REPORT-EXPORT-FORMAL-DEG-PACKAGE-GATE",
        ],
        "backend_capability": "report draft manifest and formal DEG report-ready package export",
        "current_strategy": "Formal DEG package export is live-click verified after report-ready gate; report draft stays separate from report-ready promotion.",
        "remaining_gap": "Non-DEG report-ready exports remain closed until their formal result schemas are connected.",
    },
]


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    contracts = _load_contracts()
    payload = _build_payload(contracts)
    failures = _validate(payload, contracts)
    payload["summary"]["failures"] = failures
    payload["summary"]["broken"] = sum(_summary_value(data, "broken") for data in contracts.values())
    payload["summary"]["closure_status"] = "passed_with_documented_gaps" if not failures else "failed"

    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.write_text(_render_markdown(payload), encoding="utf-8")
    print(f"json={args.json_out}")
    print(f"markdown={args.markdown_out}")
    print(f"closure_status={payload['summary']['closure_status']}")
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    return 0


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Aggregate Bio C1 route contracts into one closure matrix.")
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN)
    return parser.parse_args(argv)


def _load_contracts() -> dict[str, dict[str, Any]]:
    contracts: dict[str, dict[str, Any]] = {}
    for key, path in INPUTS.items():
        contracts[key] = json.loads(path.read_text(encoding="utf-8"))
    return contracts


def _build_payload(contracts: dict[str, dict[str, Any]]) -> dict[str, Any]:
    visible_rows = contracts["batch8_visible_buttons"]["rows"]
    page_button_summary = _summarize_visible_buttons(visible_rows)
    return {
        "schema_version": "ui_route_contract_bio_c1_closure_matrix.v1",
        "created_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "branch": _git("branch", "--show-current"),
        "head": _git("rev-parse", "HEAD"),
        "scope": (
            "Bioinformatics C1 mature UIShell 7-step page route contract closure: "
            "UI page -> backend capability -> branch/source -> live-click or disabled-reason evidence."
        ),
        "inputs": {
            key: {
                "path": str(path.relative_to(REPO_ROOT)),
                "schema_version": contracts[key].get("schema_version", ""),
                "head": contracts[key].get("head", ""),
                "summary": contracts[key].get("summary", {}),
            }
            for key, path in INPUTS.items()
        },
        "summary": {
            "ui_page_count": len(PAGE_BASELINES),
            "capability_row_count": len(CAPABILITY_MATRIX),
            "input_row_count": sum(len(data.get("rows", [])) for data in contracts.values()),
            "connected_rows": sum(_summary_value(data, "connected") for data in contracts.values()),
            "disabled_rows_with_reason": _disabled_with_reason_count(contracts),
            "broken": 0,
            "failures": [],
        },
        "page_baselines": [
            {
                "page_key": page_key,
                **baseline,
                "visible_button_summary": page_button_summary.get(page_key, {}),
            }
            for page_key, baseline in PAGE_BASELINES.items()
        ],
        "capability_matrix": CAPABILITY_MATRIX,
        "remaining_gaps": [
            row for row in CAPABILITY_MATRIX if row["status"] != "connected"
        ],
        "screenshots": _collect_screenshots(contracts),
    }


def _summarize_visible_buttons(rows: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    summary: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        page_key = str(row.get("page_key") or row.get("route_key") or "unknown")
        status = str(row.get("status") or "unknown")
        summary[page_key][status] += 1
        summary[page_key]["total"] += 1
    return {page: dict(counts) for page, counts in summary.items()}


def _disabled_with_reason_count(contracts: dict[str, dict[str, Any]]) -> int:
    count = 0
    for data in contracts.values():
        for row in data.get("rows", []):
            if row.get("status") == "disabled" and (row.get("disabled_reason") or row.get("artifact_evidence")):
                count += 1
    return count


def _summary_value(data: dict[str, Any], key: str) -> int:
    value = data.get("summary", {}).get(key, 0)
    return value if isinstance(value, int) else 0


def _collect_screenshots(contracts: dict[str, dict[str, Any]]) -> list[dict[str, str]]:
    screenshots: list[dict[str, str]] = []
    for key, data in contracts.items():
        for screenshot in data.get("screenshots", []):
            screenshots.append(
                {
                    "batch": key,
                    "page": str(screenshot.get("page") or screenshot.get("name") or ""),
                    "path": str(screenshot.get("path") or ""),
                }
            )
    return screenshots


def _validate(payload: dict[str, Any], contracts: dict[str, dict[str, Any]]) -> list[str]:
    failures: list[str] = []
    for key, data in contracts.items():
        summary = data.get("summary", {})
        if summary.get("failures"):
            failures.append(f"{key} has failures: {summary['failures']}")
        if _summary_value(data, "broken"):
            failures.append(f"{key} has broken rows: {summary.get('broken')}")

    observed_pages = {
        row.get("page_key")
        for row in contracts["batch8_visible_buttons"].get("rows", [])
        if row.get("page_key") in PAGE_BASELINES
    }
    missing_pages = sorted(set(PAGE_BASELINES) - observed_pages)
    if missing_pages:
        failures.append(f"Batch 8 does not cover visible buttons for pages: {', '.join(missing_pages)}")

    for row in payload["capability_matrix"]:
        for batch_key in row["evidence_batches"]:
            if batch_key not in contracts:
                failures.append(f"{row['ui_page']} references missing batch {batch_key}")
    return failures


def _render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Bioinformatics C1 Closure Matrix",
        "",
        f"- branch: `{payload['branch']}`",
        f"- head: `{payload['head']}`",
        f"- closure_status: `{payload['summary']['closure_status']}`",
        f"- ui_page_count: `{payload['summary']['ui_page_count']}`",
        f"- capability_row_count: `{payload['summary']['capability_row_count']}`",
        f"- input_row_count: `{payload['summary']['input_row_count']}`",
        f"- connected_rows_from_inputs: `{payload['summary']['connected_rows']}`",
        f"- disabled_rows_with_reason: `{payload['summary']['disabled_rows_with_reason']}`",
        f"- broken_rows_from_inputs: `{payload['summary']['broken']}`",
        "",
        "## Inputs",
        "",
        "| Batch | Report | Head | Rows | Connected | Disabled | Broken |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for key, info in payload["inputs"].items():
        summary = info["summary"]
        lines.append(
            "| `{}` | `{}` | `{}` | `{}` | `{}` | `{}` | `{}` |".format(
                key,
                info["path"],
                str(info["head"])[:12],
                summary.get("row_count", 0),
                summary.get("connected", 0),
                summary.get("disabled", 0),
                summary.get("broken", 0),
            )
        )

    lines.extend(
        [
            "",
            "## Page Baseline Matrix",
            "",
            "| UI page | Visual baseline | Source branch | Source commits | Visible button summary |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for row in payload["page_baselines"]:
        visible = row.get("visible_button_summary", {})
        visible_text = ", ".join(f"{key}={value}" for key, value in sorted(visible.items())) or "not observed"
        lines.append(
            "| {} | {} | `{}` | `{}` | {} |".format(
                row["ui_page"],
                row["visual_baseline"],
                row["source_branch"],
                ", ".join(row["source_commits"]),
                visible_text,
            )
        )

    lines.extend(
        [
            "",
            "## UI Page To Backend Capability Matrix",
            "",
            "| UI page | Required connection | Status | Backend capability | Evidence batches | Current strategy | Remaining gap |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in payload["capability_matrix"]:
        lines.append(
            "| {} | {} | `{}` | {} | `{}` | {} | {} |".format(
                row["ui_page"],
                row["requirement"],
                row["status"],
                row["backend_capability"],
                ", ".join(row["evidence_batches"]),
                row["current_strategy"],
                row["remaining_gap"],
            )
        )

    lines.extend(["", "## Remaining Gaps", ""])
    if payload["remaining_gaps"]:
        for row in payload["remaining_gaps"]:
            lines.append(f"- `{row['ui_page']}`: {row['remaining_gap']}")
    else:
        lines.append("- None.")

    lines.extend(["", "## Screenshot Evidence", ""])
    for screenshot in payload["screenshots"]:
        path = screenshot["path"]
        label = screenshot["page"] or "screenshot"
        lines.append(f"- `{screenshot['batch']}` / `{label}`: `{path}`")

    if payload["summary"]["failures"]:
        lines.extend(["", "## Failures", ""])
        for failure in payload["summary"]["failures"]:
            lines.append(f"- {failure}")
    return "\n".join(lines) + "\n"


def _git(*args: str) -> str:
    return subprocess.check_output(("git", *args), cwd=REPO_ROOT, text=True).strip()


if __name__ == "__main__":
    raise SystemExit(main())
