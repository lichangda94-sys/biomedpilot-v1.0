from __future__ import annotations

import json
from pathlib import Path

from app.bioinformatics.deg_engine import create_deg_production_audit_package, run_controlled_multifactor_limma_fixture
from app.bioinformatics.plots import create_formal_deg_plot_artifact
from app.bioinformatics.reports.formal_deg import create_formal_deg_report_ready_package, evaluate_formal_deg_report_ready_gate
from app.bioinformatics.results.registry import load_registry


def test_multifactor_deg_result_enters_plot_audit_and_section_report(tmp_path: Path) -> None:
    run = run_controlled_multifactor_limma_fixture(tmp_path, allow_legacy_sidecar_execution=True)
    assert run["status"] == "passed", run.get("blockers")

    plot = create_formal_deg_plot_artifact(tmp_path, result_id=run["result_id"], plot_type="volcano_plot")
    assert plot["status"] == "passed", plot.get("blockers")
    provenance = plot["plot_artifact"]["parameters_manifest"]["multifactor_design_provenance"]
    assert provenance["design_formula"] == "~ batch + group"
    assert provenance["contrast"]["coefficient"] == "groupcase"

    audit = create_deg_production_audit_package(tmp_path, result_id=run["result_id"])
    assert audit["status"] == "deg_production_audit_package_created"
    audit_provenance = json.loads((Path(audit["package_path"]) / "manifests" / "multifactor_design_provenance.json").read_text(encoding="utf-8"))
    assert audit_provenance["batch_variables"] == ["batch"]

    gate = evaluate_formal_deg_report_ready_gate(tmp_path, result_id=run["result_id"])
    assert gate["status"] == "eligible_for_formal_deg_report_ready"
    assert gate["provenance_required"]["multifactor_design"]["design_formula"] == "~ batch + group"

    package = create_formal_deg_report_ready_package(tmp_path, result_id=run["result_id"])
    assert package["status"] == "formal_deg_report_ready_package_created"
    report = (Path(package["package_path"]) / "formal_deg_report.md").read_text(encoding="utf-8")
    assert "design_formula: ~ batch + group" in report
    assert "clinical conclusions" in report

    entry = next(item for item in load_registry(tmp_path)["results"] if item["result_id"] == run["result_id"])
    assert entry["report_ready_eligible"] is True
    assert entry["report_artifacts"][0]["section_scope"] == "formal_deg_only"
