from __future__ import annotations

import json
import subprocess
from pathlib import Path

from app.bioinformatics.reports import integrated
from app.bioinformatics.reports.integrated import (
    build_full_integrated_report_package_plan,
    create_full_integrated_docx_rendered_export,
    create_full_integrated_docx_rendered_export_skeleton,
    create_full_integrated_report_package,
    evaluate_full_integrated_docx_preflight_gate,
    evaluate_full_integrated_report_renderer_gate,
)
from app.bioinformatics.reports.renderer_runtime_policy import build_full_integrated_renderer_runtime_packaging_policy
from app.bioinformatics.reports.survival_clinical import create_cox_report_ready_package, create_km_logrank_report_ready_package
from app.bioinformatics.results.registry import save_registry
from tests.bioinformatics.test_survival_clinical_report_ready_gate import _cox_entry, _km_entry


def test_integrated_report_package_is_blocked_while_gate_blocked(tmp_path: Path) -> None:
    _write_entries(tmp_path)

    package = create_full_integrated_report_package(tmp_path)

    assert package["status"] == "blocked"
    assert package["package_path"] == ""
    assert package["user_visible_package_path"] == ""
    assert package["package_plan"]["can_create_package"] is False
    assert "survival_clinical_report_ready_not_implemented" not in package["blockers"]
    assert "full_integrated_prerequisite_survival_clinical_section_package_not_passed:survival_km_logrank" in package["blockers"]
    assert not (tmp_path / "report_package" / "integrated").exists()


def test_integrated_report_package_plan_lists_stable_layout(tmp_path: Path) -> None:
    plan = build_full_integrated_report_package_plan(tmp_path, gate={"status": "blocked", "blockers": ["survival_clinical_report_ready_not_implemented"]})

    assert plan["section_scope"] == "full_integrated_report"
    assert "prerequisite_summary" in plan
    assert "sections" in plan["required_directories"]
    assert "integrated_report.md" in plan["required_files"]
    assert "manifests/full_integrated_gate_snapshot.json" in plan["required_files"]
    assert plan["renderer_status"] == "passed"
    assert plan["renderer_id"] == "builtin_markdown"
    assert "preflight_only" in plan["artifact_policy"]["forbidden_sources"]


def test_integrated_report_package_blocks_non_markdown_format_even_when_gate_is_stubbed_passed(tmp_path: Path, monkeypatch) -> None:
    _write_entries(tmp_path)
    monkeypatch.setattr(integrated, "evaluate_full_integrated_report_gate", lambda *args, **kwargs: _passed_gate())

    package = create_full_integrated_report_package(tmp_path, export_format="pdf")

    assert package["status"] == "blocked"
    assert "full_integrated_pdf_renderer_not_enabled_in_b23_4" in package["blockers"]
    assert package["renderer_gate"]["export_format"] == "pdf"
    assert package["package_plan"]["can_create_package"] is False
    assert not (tmp_path / "report_package" / "integrated").exists()


def test_integrated_report_package_plan_surfaces_renderer_gate_for_docx(tmp_path: Path) -> None:
    gate = {"status": "eligible_for_full_integrated_report", "blockers": []}
    renderer = evaluate_full_integrated_report_renderer_gate("docx")

    plan = build_full_integrated_report_package_plan(tmp_path, gate=gate, export_format="docx", renderer_gate=renderer)

    assert plan["export_format"] == "docx"
    assert plan["renderer_id"] == "pandoc_docx"
    assert plan["renderer_status"] == "blocked"
    assert plan["renderer_preflight_policy"]["activation_status"] == "disabled_until_docx_renderer_activation_stage"
    assert "non-empty integrated_report.md" in plan["renderer_preflight_policy"]["checks"]
    assert "full_integrated_docx_renderer_not_enabled_in_b23_4" in plan["disabled_reasons"]
    assert plan["can_create_package"] is False


def test_renderer_runtime_packaging_policy_keeps_releasebuild_external_only(tmp_path: Path) -> None:
    policy = build_full_integrated_renderer_runtime_packaging_policy()
    docx_gate = evaluate_full_integrated_report_renderer_gate("docx")
    pdf_gate = evaluate_full_integrated_report_renderer_gate("pdf")
    plan = build_full_integrated_report_package_plan(tmp_path)

    assert policy["releasebuild_policy"]["bundles_external_renderers"] is False
    assert policy["releasebuild_policy"]["network_downloads"] is False
    assert policy["docx"]["runtime_provider"] == "user_system_pandoc_on_search_path"
    assert policy["pdf"]["selected_engine"] == "pandoc_xelatex_when_pdf_activation_is_explicitly_approved"
    assert policy["pdf"]["wkhtmltopdf_policy"] == "detect_only_not_formal_full_integrated_report_backend"
    assert plan["renderer_runtime_packaging_policy"]["policy_id"] == "b24_3_system_path_no_bundled_renderers"
    assert docx_gate["runtime_packaging_policy"]["policy_id"] == policy["policy_id"]
    assert docx_gate["checks"]["external_renderers_bundled"] is False
    assert pdf_gate["required_dependencies"] == ["pandoc", "xelatex"]
    assert "xelatex" in pdf_gate["detected_dependencies"]
    assert "wkhtmltopdf" in pdf_gate["detected_dependencies"]


def test_integrated_report_package_skeleton_writes_timestamped_auditable_layout_when_gate_passes(tmp_path: Path, monkeypatch) -> None:
    _write_entries(tmp_path)
    gate = _passed_gate()
    monkeypatch.setattr(integrated, "evaluate_full_integrated_report_gate", lambda *args, **kwargs: gate)

    first = create_full_integrated_report_package(tmp_path)
    second = create_full_integrated_report_package(tmp_path)

    assert first["status"] == "full_integrated_report_package_created"
    assert second["status"] == "full_integrated_report_package_created"
    assert first["package_path"] != second["package_path"]
    package_path = Path(first["package_path"])
    assert (package_path / "integrated_report.md").is_file()
    assert (package_path / "README_limitations.md").is_file()
    assert (package_path / "integrated_report_package_manifest.json").is_file()
    assert (package_path / "manifests" / "full_integrated_gate_snapshot.json").is_file()
    assert (package_path / "manifests" / "result_index_snapshot.json").is_file()
    assert (package_path / "manifests" / "section_manifest.json").is_file()
    assert (package_path / "manifests" / "dependency_snapshot.json").is_file()
    assert (package_path / "manifests" / "warnings_limitations.json").is_file()
    assert (package_path / "manifests" / "package_inventory.json").is_file()
    assert (package_path / "sections" / "formal_deg.md").is_file()
    assert (package_path / "sections" / "ora.md").is_file()
    assert (package_path / "sections" / "gsea.md").is_file()
    assert (package_path / "sections" / "survival_km.md").is_file()
    assert (package_path / "sections" / "cox.md").is_file()
    assert "treatment recommendation" in (package_path / "README_limitations.md").read_text(encoding="utf-8")
    assert first["package_inventory"]["required_files"]["integrated_report_package_manifest.json"] is True


def test_integrated_report_markdown_export_activates_when_all_section_prerequisites_pass(tmp_path: Path, monkeypatch) -> None:
    save_registry(
        tmp_path,
        [
            _section_entry(tmp_path, "deg-formal", "deg", "deg_result_table"),
            _section_entry(tmp_path, "ora-formal", "ora_enrichment", "ora_result_table"),
            _section_entry(tmp_path, "gsea-formal", "gsea_preranked", "gsea_result_table"),
            _km_entry(tmp_path),
            _cox_entry(tmp_path),
        ],
    )
    km_package = create_km_logrank_report_ready_package(tmp_path, result_id="km-ready")
    cox_package = create_cox_report_ready_package(tmp_path, result_id="cox-ready")
    assert km_package["status"] == "survival_km_logrank_only_report_ready_package_created"
    assert cox_package["status"] == "cox_univariate_only_report_ready_package_created"
    monkeypatch.setattr(integrated, "evaluate_formal_deg_report_ready_gate", lambda _root, result_id=None: _eligible_section_gate("eligible_for_formal_deg_report_ready", result_id or "deg-formal"))
    monkeypatch.setattr(integrated, "evaluate_ora_report_ready_gate", lambda _root, result_id=None, **_kwargs: _eligible_section_gate("eligible_for_ora_report_ready", result_id or "ora-formal"))
    monkeypatch.setattr(integrated, "evaluate_gsea_report_ready_gate", lambda _root, result_id=None, **_kwargs: _eligible_section_gate("eligible_for_gsea_report_ready", result_id or "gsea-formal"))

    gate = integrated.evaluate_full_integrated_report_gate(tmp_path)

    assert gate["status"] == "eligible_for_full_integrated_report"
    assert gate["enabled_export_formats"] == ["markdown"]
    assert gate["disabled_export_formats"] == ["pdf", "docx"]
    assert gate["export_activation_status"] == "eligible_for_markdown_export"
    assert "full_integrated_report_export_not_enabled_in_b23_1" not in gate["blockers"]
    assert "full_integrated_report_export_waiting_for_section_prerequisites" not in gate["blockers"]
    assert gate["checks"]["all_required_section_ids_requested"] is True
    assert gate["checks"]["survival_clinical_report_ready_available"] is True
    sections = {row["section_id"]: row for row in gate["prerequisite_rows"]}
    assert sections["survival_km_logrank"]["section_only_package_sufficient"] is True
    assert sections["cox"]["section_only_package_sufficient"] is True

    package = create_full_integrated_report_package(tmp_path)

    assert package["status"] == "full_integrated_report_package_created"
    assert package["export_format"] == "markdown"
    package_path = Path(package["package_path"])
    assert (package_path / "integrated_report.md").is_file()
    assert (package_path / "sections" / "formal_deg.md").is_file()
    assert (package_path / "sections" / "survival_km.md").is_file()
    assert (package_path / "sections" / "cox.md").is_file()
    assert package["renderer_gate"]["renderer_id"] == "builtin_markdown"
    assert "clinical diagnosis" in (package_path / "README_limitations.md").read_text(encoding="utf-8")


def test_docx_preflight_validates_markdown_package_but_keeps_activation_blocked(tmp_path: Path, monkeypatch) -> None:
    _write_entries(tmp_path)
    monkeypatch.setattr(integrated, "evaluate_full_integrated_report_gate", lambda *args, **kwargs: _passed_gate())
    package = create_full_integrated_report_package(tmp_path)

    gate = evaluate_full_integrated_docx_preflight_gate(package["package_path"], renderer_gate=_docx_renderer_gate_without_activation_blocker())

    assert gate["status"] == "blocked"
    assert gate["preflight_status"] == "passed_pending_activation"
    assert gate["checks"]["source_package_full_integrated_markdown"] is True
    assert gate["checks"]["source_markdown_nonempty"] is True
    assert gate["checks"]["pandoc_detected"] is True
    assert gate["checks"]["no_conversion_invoked"] is True
    assert gate["artifact_manifest_preview"]["artifact_type"] == "full_integrated_report_rendered_export"
    assert gate["artifact_manifest_preview"]["validation_status"] == "not_created_preflight_only"
    assert "full_integrated_docx_export_activation_required_b24_2" in gate["blockers"]
    assert not (Path(package["package_path"]) / "exports" / "integrated_report.docx").exists()


def test_docx_preflight_blocks_missing_local_markdown_references(tmp_path: Path, monkeypatch) -> None:
    _write_entries(tmp_path)
    monkeypatch.setattr(integrated, "evaluate_full_integrated_report_gate", lambda *args, **kwargs: _passed_gate())
    package = create_full_integrated_report_package(tmp_path)
    package_path = Path(package["package_path"])
    markdown = package_path / "integrated_report.md"
    markdown.write_text(markdown.read_text(encoding="utf-8") + "\n\n![missing](plots/missing.svg)\n", encoding="utf-8")

    gate = evaluate_full_integrated_docx_preflight_gate(package_path, renderer_gate=_docx_renderer_gate_without_activation_blocker())

    assert gate["preflight_status"] == "blocked"
    assert "docx_markdown_local_reference_missing:plots/missing.svg" in gate["blockers"]


def test_docx_rendered_export_skeleton_writes_blocked_attempt_without_docx(tmp_path: Path, monkeypatch) -> None:
    _write_entries(tmp_path)
    monkeypatch.setattr(integrated, "evaluate_full_integrated_report_gate", lambda *args, **kwargs: _passed_gate())
    package = create_full_integrated_report_package(tmp_path)

    skeleton = create_full_integrated_docx_rendered_export_skeleton(package["package_path"], renderer_gate=_docx_renderer_gate_without_activation_blocker())

    package_path = Path(package["package_path"])
    manifest_path = package_path / "manifests" / "rendered_exports.json"
    log_path = Path(skeleton["conversion_log_path"])
    package_manifest = json.loads((package_path / "integrated_report_package_manifest.json").read_text(encoding="utf-8"))
    rendered = json.loads(manifest_path.read_text(encoding="utf-8"))
    log_payload = json.loads(log_path.read_text(encoding="utf-8"))

    assert skeleton["status"] == "blocked"
    assert manifest_path.is_file()
    assert log_path.is_file()
    assert rendered["exports"] == []
    assert rendered["attempts"][0]["validation_status"] == "blocked"
    assert rendered["policy"]["rendered_exports_are_package_artifacts_not_analysis_results"] is True
    assert "full_integrated_docx_conversion_not_enabled_b24_4" in rendered["attempts"][0]["blockers"]
    assert log_payload["conversion_invoked"] is False
    assert log_payload["markdown_package_preserved"] is True
    assert package_manifest["rendered_exports_manifest"] == "manifests/rendered_exports.json"
    assert package_manifest["rendered_exports_summary"]["exports_count"] == 0
    assert not (package_path / "exports").exists()


def test_docx_rendered_export_skeleton_keeps_existing_successful_exports(tmp_path: Path, monkeypatch) -> None:
    _write_entries(tmp_path)
    monkeypatch.setattr(integrated, "evaluate_full_integrated_report_gate", lambda *args, **kwargs: _passed_gate())
    package = create_full_integrated_report_package(tmp_path)
    package_path = Path(package["package_path"])
    existing = {
        "schema_version": "biomedpilot.full_integrated_rendered_exports.v1",
        "package_scope": "full_integrated_report",
        "source_package_id": package_path.name,
        "source_package_path": str(package_path),
        "exports": [{"artifact_id": "docx_previous", "validation_status": "passed"}],
        "attempts": [],
    }
    (package_path / "manifests" / "rendered_exports.json").write_text(json.dumps(existing, indent=2) + "\n", encoding="utf-8")

    create_full_integrated_docx_rendered_export_skeleton(package["package_path"], renderer_gate=_docx_renderer_gate_without_activation_blocker())

    rendered = json.loads((package_path / "manifests" / "rendered_exports.json").read_text(encoding="utf-8"))
    assert rendered["exports"] == existing["exports"]
    assert len(rendered["attempts"]) == 1
    assert rendered["latest_attempt_status"] == "blocked"


def test_docx_rendered_export_blocks_when_pandoc_missing_without_docx(tmp_path: Path, monkeypatch) -> None:
    _write_entries(tmp_path)
    monkeypatch.setattr(integrated, "evaluate_full_integrated_report_gate", lambda *args, **kwargs: _passed_gate())
    package = create_full_integrated_report_package(tmp_path)

    result = create_full_integrated_docx_rendered_export(
        package["package_path"],
        command_finder=lambda _command: None,
        runner=_runner_should_not_convert,
    )

    package_path = Path(package["package_path"])
    rendered = json.loads((package_path / "manifests" / "rendered_exports.json").read_text(encoding="utf-8"))
    log_payload = json.loads(Path(result["conversion_log_path"]).read_text(encoding="utf-8"))

    assert result["status"] == "blocked"
    assert "renderer_dependency_missing:pandoc" in result["blockers"]
    assert result["output_path"] == ""
    assert rendered["exports"] == []
    assert rendered["attempts"][0]["validation_status"] == "blocked"
    assert log_payload["conversion_invoked"] is False
    assert not list((package_path / "exports").glob("*.docx"))


def test_docx_rendered_export_creates_docx_and_registers_package_export_when_pandoc_available(tmp_path: Path, monkeypatch) -> None:
    _write_entries(tmp_path)
    monkeypatch.setattr(integrated, "evaluate_full_integrated_report_gate", lambda *args, **kwargs: _passed_gate())
    package = create_full_integrated_report_package(tmp_path)

    result = create_full_integrated_docx_rendered_export(
        package["package_path"],
        command_finder=lambda command: f"/usr/local/bin/{command}",
        runner=_pandoc_runner_writes_docx,
    )

    package_path = Path(package["package_path"])
    rendered = json.loads((package_path / "manifests" / "rendered_exports.json").read_text(encoding="utf-8"))
    log_payload = json.loads(Path(result["conversion_log_path"]).read_text(encoding="utf-8"))
    package_manifest = json.loads((package_path / "integrated_report_package_manifest.json").read_text(encoding="utf-8"))
    output = Path(result["output_path"])

    assert result["status"] == "full_integrated_docx_rendered_export_created"
    assert output.is_file()
    assert output.read_bytes()
    assert rendered["exports"][0]["artifact_type"] == "full_integrated_report_rendered_export"
    assert rendered["exports"][0]["validation_status"] == "passed"
    assert rendered["attempts"][0]["validation_status"] == "passed"
    assert rendered["policy"]["rendered_exports_are_package_artifacts_not_analysis_results"] is True
    assert log_payload["conversion_invoked"] is True
    assert log_payload["exit_code"] == 0
    assert package_manifest["rendered_exports_summary"]["exports_count"] == 1
    assert package_manifest["rendered_exports_summary"]["docx_conversion_enabled"] is True


def test_docx_rendered_export_failure_rolls_back_temp_and_preserves_markdown(tmp_path: Path, monkeypatch) -> None:
    _write_entries(tmp_path)
    monkeypatch.setattr(integrated, "evaluate_full_integrated_report_gate", lambda *args, **kwargs: _passed_gate())
    package = create_full_integrated_report_package(tmp_path)
    package_path = Path(package["package_path"])

    result = create_full_integrated_docx_rendered_export(
        package_path,
        command_finder=lambda command: f"/usr/local/bin/{command}",
        runner=_pandoc_runner_fails,
    )

    rendered = json.loads((package_path / "manifests" / "rendered_exports.json").read_text(encoding="utf-8"))
    log_payload = json.loads(Path(result["conversion_log_path"]).read_text(encoding="utf-8"))

    assert result["status"] == "failed"
    assert "docx_pandoc_conversion_failed" in result["blockers"]
    assert rendered["exports"] == []
    assert rendered["attempts"][0]["validation_status"] == "failed"
    assert log_payload["conversion_invoked"] is True
    assert log_payload["exit_code"] == 2
    assert (package_path / "integrated_report.md").is_file()
    assert not list((package_path / "exports" / ".tmp").glob("*.docx"))
    assert not list((package_path / "exports").glob("*.docx"))


def _write_entries(root: Path) -> None:
    entries = []
    for result_id, task_type, artifact_type in (
        ("deg-formal", "deg", "deg_result_table"),
        ("ora-formal", "ora_enrichment", "ora_result_table"),
        ("gsea-formal", "gsea_preranked", "gsea_result_table"),
        ("km-formal", "survival_km_logrank", "km_curve_table"),
        ("cox-formal", "cox_univariate", "cox_result_table"),
    ):
        table = _write_table(root, result_id, artifact_type)
        log = _write_log(root, result_id)
        plot = _write_plot(root, result_id)
        entries.append(
            {
                "result_id": result_id,
                "task_run_id": f"run-{result_id}",
                "task_type": task_type,
                "result_semantics": "formal_computed_result",
                "input_package_id": f"input-{result_id}",
                "source_dataset_id": "dataset",
                "source_repository_manifest": "manifest",
                "parameters_manifest": {"task_type": task_type},
                "engine_name": "engine",
                "engine_version": "1",
                "dependency_snapshot": {"status": "passed", "packages": {}},
                "output_artifacts": [{"artifact_type": artifact_type, "path": str(table)}],
                "plot_artifacts": [{"plot_id": f"plot-{result_id}", "plot_type": "km_curve", "image_artifacts": [{"path": str(plot), "format": "svg"}]}],
                "report_artifacts": [],
                "validation_status": "passed",
                "warnings": [],
                "blockers": [],
                "log_artifacts": [{"artifact_type": "task_run_log", "path": str(log)}],
                "failure_reason": "",
                "created_at": "2026-05-22T00:00:00+00:00",
                "updated_at": "2026-05-22T00:00:00+00:00",
                "schema_version": "biomedpilot.result_index_entry.v1",
                "report_ready_eligible": False,
                "migration_status": "native_v2",
            }
        )
    save_registry(root, entries)


def _section_entry(root: Path, result_id: str, task_type: str, artifact_type: str) -> dict:
    table = _write_table(root, result_id, artifact_type)
    log = _write_log(root, result_id)
    plot = _write_plot(root, result_id)
    return {
        "result_id": result_id,
        "task_run_id": f"run-{result_id}",
        "task_type": task_type,
        "result_semantics": "formal_computed_result",
        "input_package_id": f"input-{result_id}",
        "source_dataset_id": "dataset",
        "source_repository_manifest": "manifest",
        "parameters_manifest": {"task_type": task_type},
        "engine_name": "engine",
        "engine_version": "1",
        "dependency_snapshot": {"status": "passed", "packages": {}},
        "output_artifacts": [{"artifact_type": artifact_type, "path": str(table)}],
        "plot_artifacts": [{"plot_id": f"plot-{result_id}", "plot_type": "section_plot", "image_artifacts": [{"path": str(plot), "format": "svg"}]}],
        "report_artifacts": [],
        "validation_status": "passed",
        "warnings": [],
        "blockers": [],
        "log_artifacts": [{"artifact_type": "task_run_log", "path": str(log)}],
        "failure_reason": "",
        "created_at": "2026-05-22T00:00:00+00:00",
        "updated_at": "2026-05-22T00:00:00+00:00",
        "schema_version": "biomedpilot.result_index_entry.v1",
        "report_ready_eligible": False,
        "migration_status": "native_v2",
    }


def _eligible_section_gate(status: str, result_id: str) -> dict:
    return {
        "schema_version": "biomedpilot.test_section_report_gate.v1",
        "status": status,
        "selected_result_id": result_id,
        "blockers": [],
        "warnings": [],
    }


def _docx_renderer_gate_without_activation_blocker() -> dict:
    return {
        "schema_version": "biomedpilot.full_integrated_report_renderer_gate.v1",
        "status": "blocked",
        "export_format": "docx",
        "renderer_id": "pandoc_docx",
        "required_dependencies": ["pandoc"],
        "detected_dependencies": {
            "pandoc": {
                "command": "pandoc",
                "available": True,
                "path": "/usr/local/bin/pandoc",
                "version": "pandoc 3.2",
                "missing_reason": "",
                "packaging_impact": "external_binary_required_for_docx_and_pdf_activation_not_bundled",
            }
        },
        "checks": {"dependencies_detected": True, "implementation_enabled": False, "detect_first_no_install_action": True},
        "blockers": [],
        "warnings": [],
    }


def _runner_should_not_convert(*args, **kwargs):
    return subprocess.CompletedProcess(args[0], 99, stdout="", stderr="unexpected conversion")


def _pandoc_runner_writes_docx(args, **kwargs):
    if "--version" in args or "-version" in args:
        return subprocess.CompletedProcess(args, 0, stdout="pandoc 3.2\n", stderr="")
    output = Path(args[args.index("-o") + 1])
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(b"docx fixture")
    return subprocess.CompletedProcess(args, 0, stdout="pandoc ok\n", stderr="")


def _pandoc_runner_fails(args, **kwargs):
    if "--version" in args or "-version" in args:
        return subprocess.CompletedProcess(args, 0, stdout="pandoc 3.2\n", stderr="")
    return subprocess.CompletedProcess(args, 2, stdout="", stderr="pandoc failed\n")


def _passed_gate() -> dict:
    rows = [
        {"section_id": "formal_deg", "result_id": "deg-formal", "task_type": "deg", "result_semantics": "formal_computed_result", "validation_status": "passed", "plot_artifact_status": "real_artifact_registered", "section_report_ready_status": "passed"},
        {"section_id": "ora_enrichment", "result_id": "ora-formal", "task_type": "ora_enrichment", "result_semantics": "formal_computed_result", "validation_status": "passed", "plot_artifact_status": "real_artifact_registered", "section_report_ready_status": "passed"},
        {"section_id": "gsea_preranked", "result_id": "gsea-formal", "task_type": "gsea_preranked", "result_semantics": "formal_computed_result", "validation_status": "passed", "plot_artifact_status": "real_artifact_registered", "section_report_ready_status": "passed"},
        {"section_id": "survival_km_logrank", "result_id": "km-formal", "task_type": "survival_km_logrank", "result_semantics": "formal_computed_result", "validation_status": "passed", "plot_artifact_status": "real_artifact_registered", "section_report_ready_status": "passed"},
        {"section_id": "cox", "result_id": "cox-formal", "task_type": "cox_univariate", "result_semantics": "formal_computed_result", "validation_status": "passed", "plot_artifact_status": "real_artifact_registered", "section_report_ready_status": "passed"},
    ]
    return {
        "schema_version": "biomedpilot.full_integrated_report_gate.v1",
        "status": "eligible_for_full_integrated_report",
        "section_scope": "full_integrated_report",
        "section_rows": rows,
        "blockers": [],
        "warnings": [],
        "limitations_required": ["Statistical research report only."],
    }


def _write_table(root: Path, result_id: str, artifact_type: str) -> Path:
    path = root / "results" / "tables" / f"{result_id}.tsv"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"{artifact_type}\nvalue\n", encoding="utf-8")
    return path


def _write_log(root: Path, result_id: str) -> Path:
    path = root / "analysis" / f"{result_id}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('{"status": "succeeded"}\n', encoding="utf-8")
    return path


def _write_plot(root: Path, result_id: str) -> Path:
    path = root / "results" / "plots" / f"{result_id}.svg"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("<svg></svg>\n", encoding="utf-8")
    return path
