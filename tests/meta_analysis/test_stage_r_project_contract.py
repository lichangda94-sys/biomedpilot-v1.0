from __future__ import annotations

import json
import zipfile
from pathlib import Path

from app.meta_analysis.services.project_contract_service import MANIFEST_FILES, MetaProjectContractService
from app.meta_analysis.services.traceability_audit_service import TraceabilityAuditService
from tests.meta_analysis.e2e_project_builder import build_meta_analysis_e2e_project


def test_stage_m_project_generates_root_manifests_and_lineage(tmp_path: Path) -> None:
    project = build_meta_analysis_e2e_project(tmp_path)
    service = MetaProjectContractService(data_center=project["data_center"], task_center=project["task_center"])

    outputs = service.write_project_manifests(project["project_dir"])

    assert {path.name for path in outputs.values()} == set(MANIFEST_FILES)
    for filename in MANIFEST_FILES:
        assert (project["project_dir"] / filename).exists()
    lineage = json.loads((project["project_dir"] / "lineage_manifest.json").read_text(encoding="utf-8"))
    assert any(item["name"] == "analysis_result_to_dataset" for item in lineage["lineage"])
    assert any(item["name"] == "extraction_records_to_literature" for item in lineage["lineage"])


def test_missing_artifacts_warn_without_crashing(tmp_path: Path) -> None:
    project_dir = tmp_path / "empty-meta-project"
    project_dir.mkdir()
    service = MetaProjectContractService()

    service.write_project_manifests(project_dir)
    result = service.validate_project_contract(project_dir)

    assert result.valid
    assert any(warning.startswith("canonical_artifact_missing:analysis_result") for warning in result.warnings)


def test_traceability_service_saves_manifest_files_for_old_testing_project_shape(tmp_path: Path) -> None:
    project_dir = tmp_path / "old-testing-project"
    (project_dir / "analysis").mkdir(parents=True)
    (project_dir / "analysis" / "analysis_results.json").write_text(json.dumps({"results": []}), encoding="utf-8")
    service = TraceabilityAuditService()

    outputs = service.save_project_manifests(project_dir)

    assert outputs["project"].exists()
    audit = service.run_traceability_audit(project_dir)
    assert audit.passed
    assert "reproducibility_package_missing" in audit.warnings


def test_reproducibility_package_contains_root_manifests(tmp_path: Path) -> None:
    project = build_meta_analysis_e2e_project(tmp_path)

    with zipfile.ZipFile(project["paths"]["reproducibility_package"]) as archive:
        names = set(archive.namelist())

    assert set(MANIFEST_FILES) <= names
    assert "reports/report_manifest.json" in names

