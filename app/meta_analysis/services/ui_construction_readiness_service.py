from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class MetaUIPageReadinessItem:
    step_id: str
    title: str
    page_module: str
    state_function: str
    construction_priority: str
    readiness_status: str
    user_goal: str
    primary_inputs: tuple[str, ...]
    primary_outputs: tuple[str, ...]
    known_ui_risks: tuple[str, ...]
    testing_notes: tuple[str, ...]


@dataclass(frozen=True)
class MetaUIConstructionReadinessState:
    title: str
    status_label: str
    scope: str
    construction_sequence: tuple[str, ...]
    reusable_page_state_count: int
    high_risk_page_count: int
    ready_for_ui_construction: bool
    page_items: tuple[MetaUIPageReadinessItem, ...]
    global_constraints: tuple[str, ...]
    acceptance_checks: tuple[str, ...]
    output_docs: tuple[str, ...]


def build_meta_ui_construction_readiness(repo_root: Path) -> MetaUIConstructionReadinessState:
    repo_root = repo_root.expanduser().resolve()
    items = tuple(_page_items())
    high_risk_count = sum(1 for item in items if item.construction_priority == "P0")
    missing_modules = [item.page_module for item in items if not (repo_root / item.page_module.replace(".", "/")).with_suffix(".py").exists()]
    constraints = (
        "Meta Analysis remains Developer Preview / testing.",
        "Do not modify Bioinformatics while constructing Meta UI.",
        "Use page-state/service APIs; do not write business logic directly in PySide widgets.",
        "Do not implement automatic PDF download, OCR, institutional full-text access, production PDF, or production/open status labels.",
        "Generated sample project outputs should stay in temporary project directories.",
    )
    acceptance = (
        "Every visible step shows current status, input, output, warning meaning, and next step.",
        "Missing artifacts show empty/warning states, not tracebacks.",
        "Extraction and Quality pages support manual user entry without editing JSON.",
        "Analysis page distinguishes setup, preflight, dataset, run result, advanced methods, and applicability warnings.",
        "Reporting page distinguishes test summary, formal Markdown, HTML/DOCX testing exports, simplified PRISMA SVG, and PDF placeholder.",
        "All UI text keeps Developer Preview / testing visible.",
    )
    return MetaUIConstructionReadinessState(
        title="Meta UI Construction Readiness",
        status_label="Developer Preview / testing",
        scope="Pre-UI construction preparation for Meta Analysis desktop workspace.",
        construction_sequence=(
            "Workflow shell and navigation",
            "Literature import and diagnostics",
            "Duplicate review and literature library",
            "Screening and full-text eligibility",
            "Extraction and quality assessment",
            "Analysis setup and results",
            "Reporting, PRISMA, exports, and reproducibility",
        ),
        reusable_page_state_count=len(items) - len(missing_modules),
        high_risk_page_count=high_risk_count,
        ready_for_ui_construction=not missing_modules,
        page_items=items,
        global_constraints=constraints,
        acceptance_checks=acceptance,
        output_docs=(
            "docs/meta_ui_construction_preparation.md",
            "docs/meta_dev_reports/ui_construction_preparation_report.md",
        ),
    )


def _page_items() -> list[MetaUIPageReadinessItem]:
    return [
        MetaUIPageReadinessItem(
            step_id="workflow_dashboard",
            title="Workflow Dashboard",
            page_module="app.meta_analysis.pages.workflow_dashboard_page",
            state_function="workflow_dashboard_state_from_project",
            construction_priority="P0",
            readiness_status="ready_for_layout",
            user_goal="Understand current project progress and open the right next step.",
            primary_inputs=("project_dir", "manifest files", "Data Center", "Task Center", "audit log"),
            primary_outputs=("workflow step status", "warnings", "entrypoint hints"),
            known_ui_risks=("Too much status text can overwhelm users.",),
            testing_notes=("Use empty project and Stage M/AB13 sample projects.",),
        ),
        MetaUIPageReadinessItem(
            step_id="protocol",
            title="Protocol / Research Question",
            page_module="app.meta_analysis.pages.protocol_page",
            state_function="protocol_page_state_from_project",
            construction_priority="P1",
            readiness_status="ready_for_form_layout",
            user_goal="Enter PICO/PICOS and generate draft search strategies.",
            primary_inputs=("review question", "PICO/PICOS", "planned databases"),
            primary_outputs=("review_protocol.json", "search_terms_draft.json", "search_strategy_preview.md"),
            known_ui_risks=("Draft search strategies must not look final or production-grade.",),
            testing_notes=("Check missing core fields and generated strategy preview.",),
        ),
        MetaUIPageReadinessItem(
            step_id="literature_import",
            title="Literature Import / Diagnostics",
            page_module="app.meta_analysis.pages.literature_import_page",
            state_function="literature_import_wizard_state_from_project",
            construction_priority="P0",
            readiness_status="ready_for_wizard_layout",
            user_goal="Import RIS/NBIB/CSV and inspect quality diagnostics.",
            primary_inputs=("source file", "source database", "import format", "dedup mode"),
            primary_outputs=("literature records", "import diagnostics", "recent batches"),
            known_ui_risks=("Manual path input should be secondary to file picker.", "Diagnostics warnings need plain-language labels."),
            testing_notes=("Use Zotero RIS, EndNote RIS, PubMed NBIB, abnormal RIS, and AB13 CSV fixtures.",),
        ),
        MetaUIPageReadinessItem(
            step_id="literature_library",
            title="Literature Library / Duplicate Review",
            page_module="app.meta_analysis.pages.literature_library_page",
            state_function="literature_library_state_from_project",
            construction_priority="P0",
            readiness_status="needs_table_design",
            user_goal="Review imported records, duplicate risk, and merge rationale.",
            primary_inputs=("literature_records", "duplicate_candidate_groups", "merge preview"),
            primary_outputs=("read-only literature table", "duplicate risk tags", "review decisions"),
            known_ui_risks=("Green status must mean no obvious duplicate risk, not trusted evidence.", "Merge must require explicit reviewer decision."),
            testing_notes=("Verify exact and suspected duplicate groups plus legacy decision compatibility.",),
        ),
        MetaUIPageReadinessItem(
            step_id="screening_fulltext",
            title="Screening / Full-text Eligibility",
            page_module="app.meta_analysis.pages.screening_page",
            state_function="screening_page_state_from_project",
            construction_priority="P1",
            readiness_status="ready_for_record_review_layout",
            user_goal="Screen records and move eligible studies to full-text review.",
            primary_inputs=("deduplicated records", "criteria", "title/abstract decisions"),
            primary_outputs=("screening decisions", "fulltext eligibility decisions", "final included studies"),
            known_ui_risks=("Users need clear previous/next and progress state.", "Do not delete records during screening."),
            testing_notes=("Check include/exclude/maybe/needs review filters and reason selection.",),
        ),
        MetaUIPageReadinessItem(
            step_id="extraction",
            title="Extraction",
            page_module="app.meta_analysis.pages.extraction_page",
            state_function="simplified_extraction_state_from_project",
            construction_priority="P0",
            readiness_status="needs_high_attention_form_design",
            user_goal="Manually enter structured study characteristics and outcome rows.",
            primary_inputs=("final included studies", "extraction schema profile", "manual edits"),
            primary_outputs=("extraction_records.json", "drafts", "manual_edits_log.jsonl", "validation report"),
            known_ui_risks=("This is the highest-friction page.", "Field-level errors must point to exact fields.", "Users must not edit JSON directly."),
            testing_notes=("Test one complete study entry, one invalid outcome, draft save/load, copy previous, and completeness score.",),
        ),
        MetaUIPageReadinessItem(
            step_id="quality",
            title="Quality Assessment",
            page_module="app.meta_analysis.pages.quality_page",
            state_function="quality_state_from_project",
            construction_priority="P0",
            readiness_status="needs_form_design",
            user_goal="Fill domain-level quality judgement and export quality table.",
            primary_inputs=("included studies", "study design", "quality tool registry"),
            primary_outputs=("quality_assessments.json", "quality_table.csv", "quality_summary.md"),
            known_ui_risks=("NOS/QUADAS-2/RoB2 forms need clear domain grouping.", "Overall judgement suggestion must not be forced."),
            testing_notes=("Check domain notes, suggested judgement, completeness, and report manifest source.",),
        ),
        MetaUIPageReadinessItem(
            step_id="analysis",
            title="Analysis Setup / Results",
            page_module="app.meta_analysis.pages.analysis_page",
            state_function="analysis_setup_state_from_project",
            construction_priority="P1",
            readiness_status="ready_for_setup_run_explain_layout",
            user_goal="Build analysis-ready dataset, run testing meta-analysis, and read applicability warnings.",
            primary_inputs=("extraction_records", "analysis plan", "model", "effect measure"),
            primary_outputs=("analysis_ready_dataset", "analysis_result", "applicability_warnings"),
            known_ui_risks=("Users must see not-implemented methods before trying to run them.",),
            testing_notes=("Check Network Meta, HSROC, meta-regression blocked states.",),
        ),
        MetaUIPageReadinessItem(
            step_id="reporting",
            title="Reporting / PRISMA / Exports",
            page_module="app.meta_analysis.pages.reporting_page",
            state_function="reporting_prisma_trace_state_from_project",
            construction_priority="P1",
            readiness_status="ready_for_export_layout",
            user_goal="Generate testing report outputs and inspect source trace.",
            primary_inputs=("analysis results", "figures", "quality", "PRISMA summary", "report manifest"),
            primary_outputs=("formal Markdown", "HTML/DOCX testing exports", "simplified PRISMA SVG", "reproducibility package"),
            known_ui_risks=("PDF placeholder must be obvious.", "Simplified PRISMA must not be confused with formal PRISMA 2020."),
            testing_notes=("Check missing artifact warnings and report manifest section sources.",),
        ),
    ]
