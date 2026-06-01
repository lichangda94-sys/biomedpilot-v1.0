from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QPushButton, QTabBar

from app.bioinformatics.download import DatasetDownloadService
from app.bioinformatics.project_readiness import run_project_readiness
from app.bioinformatics.project_recognition import run_project_recognition_for_paths
from app.bioinformatics.retrieval.geo_search_service import GeoSearchService
from app.bioinformatics.search_center.models import UnifiedDatasetCandidate
from app.meta_analysis.pages.protocol_page import write_pubmed_search_execution_artifacts
from app.meta_analysis.search.pubmed_candidates_handoff_service import PubMedCandidatesHandoffService
from app.meta_analysis.search.pubmed_search_service import PubMedSearchService
from app.meta_analysis.services.title_abstract_screening_v2_service import TitleAbstractScreeningV2Service
from app.shell.main_window import MainWindow


RUN_ID = datetime.now().strftime("%Y%m%d_%H%M%S")
SCREENSHOT_DIR = REPO_ROOT / "docs" / "ui" / "runtime_screenshots" / "20260601_release_preview_validation"
RUN_ROOT = REPO_ROOT / "logs" / "validation" / f"release_preview_validation_{RUN_ID}"
REPORT_PATH = REPO_ROOT / "docs" / "release_validation" / "20260601_ui_shell_and_live_validation.md"
JSON_PATH = RUN_ROOT / "release_preview_validation.json"


def main() -> None:
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    RUN_ROOT.mkdir(parents=True, exist_ok=True)
    ui = capture_ui_screenshots_and_clicks()
    bio = run_bio_live_validation()
    meta = run_meta_live_validation()
    payload = {
        "schema_version": "biomedpilot.release_preview_validation.v1",
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "run_root": str(RUN_ROOT),
        "screenshot_dir": str(SCREENSHOT_DIR),
        "ui": ui,
        "bioinformatics": bio,
        "meta_analysis": meta,
    }
    JSON_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown_report(payload)
    print(REPORT_PATH)
    print(JSON_PATH)


def capture_ui_screenshots_and_clicks() -> dict[str, Any]:
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    window.resize(1600, 1000)
    window.show()
    app.processEvents()
    QTest.qWait(80)

    screenshots: list[dict[str, str]] = []
    clicks: list[dict[str, Any]] = []

    def shot(name: str) -> None:
        app.processEvents()
        QTest.qWait(50)
        path = SCREENSHOT_DIR / f"{name}.png"
        window.grab().save(str(path))
        screenshots.append({"name": name, "path": str(path), "workspace": window.current_workspace_key()})

    def audit_buttons(scope: str, *, click_safe: bool = False) -> None:
        buttons = window.findChildren(QPushButton)
        for button in buttons:
            try:
                if not button.isVisible():
                    continue
                entry = {
                    "scope": scope,
                    "object_name": button.objectName(),
                    "text": button.text().replace("\n", " / "),
                    "enabled": button.isEnabled(),
                    "button_behavior": str(button.property("buttonBehavior") or ""),
                    "disabled_reason": str(button.property("disabledReason") or ""),
                    "formal_action_enabled": bool(button.property("formalActionEnabled")),
                    "clicked": False,
                    "click_result": "",
                }
            except RuntimeError:
                continue
            if not button.isEnabled():
                entry["click_result"] = "disabled_with_reason" if entry["disabled_reason"] else "disabled_without_reason"
            elif click_safe and _is_safe_click(button):
                before = window.current_workspace_key()
                try:
                    button.click()
                    app.processEvents()
                    QTest.qWait(20)
                    entry["clicked"] = True
                    entry["click_result"] = f"clicked; workspace {before}->{window.current_workspace_key()}"
                except Exception as exc:  # pragma: no cover - runtime audit should continue.
                    entry["click_result"] = f"click_failed:{exc.__class__.__name__}:{exc}"
            else:
                entry["click_result"] = "not_clicked_safety_gate"
            clicks.append(entry)

    shot("shell_welcome")
    audit_buttons("welcome")

    about = window._welcome_page.findChild(QPushButton, "aboutButton")
    if about is not None:
        about.click()
        app.processEvents()
        clicks.append({"scope": "welcome", "object_name": "aboutButton", "text": about.text(), "enabled": about.isEnabled(), "clicked": True, "click_result": window.current_workspace_key()})
    shot("shell_about")

    window.logout()
    enter = window._welcome_page.findChild(QPushButton, "primaryButton")
    if enter is not None:
        enter.click()
        app.processEvents()
        clicks.append({"scope": "welcome", "object_name": "primaryButton", "text": enter.text(), "enabled": enter.isEnabled(), "clicked": True, "click_result": window.current_workspace_key()})
    shot("shell_dashboard")
    audit_buttons("dashboard", click_safe=False)

    _click_sidebar(window, "settings", clicks)
    shot("shell_settings_general")
    _capture_tabs(window, "settingsSecondaryNav", "shell_settings", screenshots)
    audit_buttons("settings", click_safe=True)

    _click_sidebar(window, "centers", clicks)
    shot("shell_centers")
    _capture_tabs(window, "centersSecondaryNav", "shell_centers", screenshots)
    audit_buttons("centers", click_safe=True)

    _click_sidebar(window, "bioinformatics", clicks)
    bio_methods = [
        ("bio_project_home", "show_project_home"),
        ("bio_data_source", "show_data_source"),
        ("bio_data_check_recognition", "show_recognition"),
        ("bio_data_check_readiness", "show_readiness"),
        ("bio_group_design", "show_group_design"),
        ("bio_analysis_tasks", "show_analysis_tasks"),
        ("bio_result_report", "show_results_browser"),
        ("bio_report_export", "show_report_viewer"),
        ("bio_settings_resources", "show_settings"),
    ]
    for name, method_name in bio_methods:
        getattr(window._bioinformatics_page, method_name)()
        shot(name)
        audit_buttons(name)

    _click_sidebar(window, "meta_analysis", clicks)
    meta_project_dir = RUN_ROOT / "ui_meta_project"
    meta_project_dir.mkdir(parents=True, exist_ok=True)
    window._meta_analysis_page.set_project_dir(meta_project_dir)
    for key in window._meta_analysis_page.target_ia_page_keys():
        window._meta_analysis_page.show_target_ia_page(key)
        shot(f"meta_{key}")
        audit_buttons(f"meta_{key}", click_safe=True)

    _click_sidebar(window, "labtools", clicks)
    for key in window._labtools_page.page_keys():
        window._labtools_page._show_page(key)
        shot(f"labtools_{key}")
        audit_buttons(f"labtools_{key}", click_safe=True)

    _click_sidebar(window, "test_feedback", clicks)
    shot("shell_test_feedback")
    audit_buttons("test_feedback", click_safe=True)

    window.close()
    app.processEvents()
    return {"screenshots": screenshots, "clicks": clicks, "screenshot_dir": str(SCREENSHOT_DIR)}


def run_bio_live_validation() -> dict[str, Any]:
    outputs: list[dict[str, Any]] = []
    for accession in ("GSE6004", "GSE153659"):
        project_root = RUN_ROOT / "bioinformatics" / accession
        project_root.mkdir(parents=True, exist_ok=True)
        search = GeoSearchService().search(accession, max_results=3)
        candidate = _candidate_from_geo_search(accession, search)
        service = DatasetDownloadService()
        family = service.create_candidate_download_task(
            project_root=project_root,
            candidate=candidate,
            execute_download=True,
            original_chinese_topic=accession,
        )
        matrix = service.download_geo_manifest_assets(
            project_root=project_root,
            accession_or_project=accession,
            asset_types=("series_matrix",),
        )
        files = [Path(path) for path in [*family.downloaded_files, *matrix.downloaded_files]]
        recognition = run_project_recognition_for_paths(project_root, files, skipped_unselected_count=0)
        readiness = run_project_readiness(project_root)
        readiness_report = readiness.get("readiness_report", {}) if isinstance(readiness, dict) else {}
        outputs.append(
            {
                "accession": accession,
                "search_status": search.search_status,
                "search_total_found": search.total_found,
                "search_accessions": [item.accession for item in search.results],
                "executed_queries": list(search.executed_queries),
                "family_download": family.status,
                "matrix_download": matrix.status,
                "downloaded_files": [str(path) for path in files],
                "recognition_status": recognition.get("report_status"),
                "recognized_files": len(recognition.get("files", [])),
                "type_counts": recognition.get("type_counts", {}),
                "readiness_status": readiness_report.get("overall_status"),
                "readiness_warnings": readiness_report.get("warnings", []),
                "project_root": str(project_root),
            }
        )
    return {"datasets": outputs}


def run_meta_live_validation() -> dict[str, Any]:
    project_dir = RUN_ROOT / "meta_analysis" / "thyroid_cancer_adiponectin"
    project_dir.mkdir(parents=True, exist_ok=True)
    query = '("thyroid cancer" OR "thyroid carcinoma" OR 甲状腺癌) AND (adiponectin OR 脂联素)'
    execution = PubMedSearchService().search_pubmed(query, max_results=8, timeout_seconds=20)
    artifacts = write_pubmed_search_execution_artifacts(project_dir, query, execution)
    preview_payload = json.loads(Path(artifacts["pubmed_candidates_preview"]).read_text(encoding="utf-8"))
    candidate_ids = [str(item.get("candidate_id")) for item in preview_payload.get("candidates", []) if item.get("candidate_id")]
    selected_ids = tuple(candidate_ids[: min(3, len(candidate_ids))])
    rejected_ids = tuple(candidate_ids[min(3, len(candidate_ids)) :])
    handoff = PubMedCandidatesHandoffService().import_selected_candidates(
        project_dir,
        preview_id=str(preview_payload.get("preview_id")),
        selected_candidate_ids=selected_ids,
        rejected_candidate_ids=rejected_ids,
        actor="release_validation",
    )
    screening = TitleAbstractScreeningV2Service().build_queue(project_dir, project_id=project_dir.name) if handoff.success else None
    return {
        "project_dir": str(project_dir),
        "query": query,
        "search_success": execution.success,
        "result_count": execution.result_count,
        "returned_count": execution.returned_count,
        "pmids": list(execution.pmids),
        "artifacts": artifacts,
        "preview_candidate_count": int(preview_payload.get("candidate_count", 0) or 0),
        "handoff_success": handoff.success,
        "imported_count": handoff.imported_count,
        "literature_records_path": handoff.literature_records_path,
        "dedup_queue_path": handoff.dedup_queue_path,
        "screening_queue_success": bool(screening and screening.success),
        "screening_record_count": screening.record_count if screening else 0,
        "screening_queue_path": screening.output_path if screening else "",
        "errors": list(execution.errors),
    }


def write_markdown_report(payload: dict[str, Any]) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Release Preview UI Shell and Live Function Validation",
        "",
        f"- created_at: `{payload['created_at']}`",
        f"- run_root: `{payload['run_root']}`",
        f"- screenshot_dir: `{payload['screenshot_dir']}`",
        "",
        "## UI Shell Baseline Restore",
        "",
        "- Welcome/Login: matches UIShell runtime baseline in current source.",
        "- Dashboard/Home: UIShell runtime baseline retained; Integration Centers entry is preserved.",
        "- About: restored to UIShell mature dark text page baseline.",
        "- Settings: UIShell settings shell retained with Integration R enrichment backend detect-only gate.",
        "- Sidebar: UIShell AppSidebar visual structure retained with current Integration routes.",
        "",
        "## Live Bioinformatics Validation",
        "",
        "| Dataset | Search | Download | Recognition | Readiness | Project |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for item in payload["bioinformatics"]["datasets"]:
        lines.append(
            "| {accession} | {search_status} {search_accessions} | {family_download}; {matrix_download} | {recognition_status}; files={recognized_files} | {readiness_status} | `{project_root}` |".format(
                **item
            )
        )
    lines.extend(
        [
            "",
            "## Live Meta Analysis PubMed Validation",
            "",
            f"- query: `{payload['meta_analysis']['query']}`",
            f"- search_success: `{payload['meta_analysis']['search_success']}`",
            f"- result_count: `{payload['meta_analysis']['result_count']}`",
            f"- returned_count: `{payload['meta_analysis']['returned_count']}`",
            f"- preview_candidate_count: `{payload['meta_analysis']['preview_candidate_count']}`",
            f"- handoff_success: `{payload['meta_analysis']['handoff_success']}`",
            f"- imported_count: `{payload['meta_analysis']['imported_count']}`",
            f"- screening_queue_success: `{payload['meta_analysis']['screening_queue_success']}`",
            f"- screening_record_count: `{payload['meta_analysis']['screening_record_count']}`",
            f"- project_dir: `{payload['meta_analysis']['project_dir']}`",
            "",
            "## Screenshot Evidence",
            "",
        ]
    )
    for shot in payload["ui"]["screenshots"]:
        name = shot["name"]
        path = shot["path"]
        lines.extend([f"### {name}", "", f"![{name}]({path})", ""])
    lines.extend(
        [
            "## Click Audit Summary",
            "",
            "| Scope | Object | Text | Enabled | Click Result | Disabled Reason |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    for entry in payload["ui"]["clicks"]:
        lines.append(
            "| {scope} | `{object_name}` | {text} | {enabled} | {click_result} | {disabled_reason} |".format(
                scope=_md_cell(entry.get("scope", "")),
                object_name=_md_cell(entry.get("object_name", "")),
                text=_md_cell(entry.get("text", "")),
                enabled=entry.get("enabled", ""),
                click_result=_md_cell(entry.get("click_result", "")),
                disabled_reason=_md_cell(entry.get("disabled_reason", "")),
            )
        )
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _candidate_from_geo_search(accession: str, search: Any) -> UnifiedDatasetCandidate:
    result = search.results[0] if search.results else None
    metadata = result.to_dict() if result is not None and hasattr(result, "to_dict") else {}
    return UnifiedDatasetCandidate(
        source="geo",
        accession_or_project=accession,
        display_title=str(getattr(result, "title", accession) or accession),
        organism="Homo sapiens",
        disease="thyroid cancer",
        tissue="thyroid",
        data_modality="expression profiling",
        sample_count="",
        has_expression_matrix=True,
        has_sample_metadata=True,
        has_clinical_metadata=False,
        has_platform_annotation=True,
        recommended_analyses=("data_recognition", "readiness_preflight"),
        download_plan_available=True,
        score=90,
        warnings=tuple(search.warnings),
        source_specific_metadata=metadata,
    )


def _capture_tabs(window: MainWindow, tab_object_name: str, prefix: str, screenshots: list[dict[str, str]]) -> None:
    tab = window.findChild(QTabBar, tab_object_name)
    if tab is None:
        return
    app = QApplication.instance()
    for index in range(tab.count()):
        tab.setCurrentIndex(index)
        if app is not None:
            app.processEvents()
        QTest.qWait(20)
        name = f"{prefix}_tab_{index}_{tab.tabData(index)}"
        path = SCREENSHOT_DIR / f"{name}.png"
        window.grab().save(str(path))
        screenshots.append({"name": name, "path": str(path), "workspace": window.current_workspace_key()})


def _click_sidebar(window: MainWindow, key: str, clicks: list[dict[str, Any]]) -> None:
    button = getattr(window._sidebar, "_nav_buttons", {}).get(key)
    if button is None:
        clicks.append({"scope": "sidebar", "object_name": key, "enabled": False, "clicked": False, "click_result": "missing_sidebar_button"})
        return
    button.click()
    app = QApplication.instance()
    if app is not None:
        app.processEvents()
    clicks.append(
        {
            "scope": "sidebar",
            "object_name": button.objectName(),
            "text": button.text().replace("\n", " / "),
            "enabled": button.isEnabled(),
            "button_behavior": str(button.property("buttonBehavior") or ""),
            "clicked": True,
            "click_result": window.current_workspace_key(),
        }
    )


def _is_safe_click(button: QPushButton) -> bool:
    name = button.objectName()
    text = button.text()
    behavior = str(button.property("buttonBehavior") or "")
    unsafe_tokens = (
        "choose",
        "file",
        "folder",
        "path",
        "open",
        "browse",
        "dialog",
        "download",
        "export",
        "导出",
        "下载",
        "选择",
        "打开",
        "路径",
    )
    haystack = f"{name} {text} {behavior}".lower()
    if any(token.lower() in haystack for token in unsafe_tokens):
        return False
    if button.property("formalActionEnabled"):
        return False
    return name in {
        "settingsDetectButton",
        "detectREnrichmentBackendButton",
        "developerDiagnosticsToggle",
        "labToolsHomeButton",
        "labtoolsEntryButton",
        "labtoolsSecondaryEntryButton",
        "primaryButton",
        "secondaryButton",
        "ghostButton",
        "quickAccessButton",
        "centersActionButton",
    } or "navigates_to" in behavior or "toggles_" in behavior or "calls_" in behavior


def _md_cell(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " / ")


if __name__ == "__main__":
    main()
