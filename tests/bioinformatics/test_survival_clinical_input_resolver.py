from __future__ import annotations

import json
from pathlib import Path

from app.bioinformatics.survival_clinical import resolve_survival_clinical_inputs


def test_clinical_asset_present_and_exact_case_sample_mapping_passes(tmp_path: Path) -> None:
    clinical, sample, expression = _write_project_tables(tmp_path)
    _write_standardized_state(tmp_path, clinical=clinical, sample=sample, expression=expression)

    package = resolve_survival_clinical_inputs(tmp_path)

    assert package["status"] == "passed"
    assert package["clinical_asset"]["asset_id"] == "clinical"
    assert package["mapped_case_count"] == 2
    assert package["mapped_sample_count"] == 2
    assert package["available_time_fields"] == ["OS_time"]
    assert package["available_event_fields"] == ["OS_event"]
    assert "recognition_report.json" in package["provenance"]["forbidden_sources"]
    assert not (tmp_path / "results" / "summaries" / "result_index.json").exists()


def test_missing_clinical_asset_blocks_input_resolver(tmp_path: Path) -> None:
    expression = tmp_path / "expr.tsv"
    expression.write_text("gene\tS1\nTP53\t1\n", encoding="utf-8")
    _write_standardized_state(tmp_path, clinical=None, sample=None, expression=expression)

    package = resolve_survival_clinical_inputs(tmp_path)

    assert package["status"] == "blocked"
    assert "missing_clinical_asset" in package["blockers"]


def test_partial_and_no_overlap_mapping_are_reported(tmp_path: Path) -> None:
    clinical = tmp_path / "clinical.tsv"
    clinical.write_text("case_id\tOS_time\tOS_event\nC1\t10\t1\nC2\t20\t0\n", encoding="utf-8")
    sample = tmp_path / "sample.tsv"
    sample.write_text("sample_id\tcase_id\nS1\tC1\nS3\tC3\n", encoding="utf-8")
    expression = tmp_path / "expr.tsv"
    expression.write_text("gene\tS1\tS3\nTP53\t1\t2\n", encoding="utf-8")
    _write_standardized_state(tmp_path, clinical=clinical, sample=sample, expression=expression)

    partial = resolve_survival_clinical_inputs(tmp_path)
    assert partial["status"] == "passed_with_warnings"
    assert "partial_case_sample_mapping" in partial["warnings"]
    assert "clinical_only_cases_present" in partial["warnings"]

    sample.write_text("sample_id\tcase_id\nS4\tC4\n", encoding="utf-8")
    expression.write_text("gene\tS4\nTP53\t1\n", encoding="utf-8")
    blocked = resolve_survival_clinical_inputs(tmp_path)
    assert "no_overlap_between_clinical_and_expression" in blocked["blockers"]
    assert "case_sample_mapping_failed" in blocked["blockers"]


def test_duplicate_ids_and_tcga_barcode_normalization(tmp_path: Path) -> None:
    clinical = tmp_path / "clinical.tsv"
    clinical.write_text("case_id\tOS_time\tOS_event\nTCGA-AA-0001\t10\t1\nTCGA-AA-0001\t20\t0\n", encoding="utf-8")
    sample = tmp_path / "sample.tsv"
    sample.write_text("sample_id\tcase_id\nTCGA-AA-0001-01A\tTCGA-AA-0001-01A\n", encoding="utf-8")
    expression = tmp_path / "expr.tsv"
    expression.write_text("gene\tTCGA-AA-0001-01A\nTP53\t1\n", encoding="utf-8")
    _write_standardized_state(tmp_path, clinical=clinical, sample=sample, expression=expression)

    package = resolve_survival_clinical_inputs(tmp_path)

    assert "duplicate_case_id_unresolved" in package["blockers"]
    assert "tcga_barcode_truncated_to_case_id" in package["warnings"]
    assert package["mapped_case_count"] == 1


def _write_project_tables(root: Path) -> tuple[Path, Path, Path]:
    clinical = root / "clinical.tsv"
    clinical.write_text("case_id\tOS_time\tOS_event\tstage\nC1\t10\t1\tII\nC2\t20\t0\tIII\n", encoding="utf-8")
    sample = root / "sample.tsv"
    sample.write_text("sample_id\tcase_id\tgroup\nS1\tC1\tcase\nS2\tC2\tcontrol\n", encoding="utf-8")
    expression = root / "expr.tsv"
    expression.write_text("gene\tS1\tS2\nTP53\t1\t2\n", encoding="utf-8")
    return clinical, sample, expression


def _write_standardized_state(root: Path, *, clinical: Path | None, sample: Path | None, expression: Path) -> None:
    assets: list[dict[str, object]] = [
        _asset("expr", "normalized_expression_matrix", "expression_repository", expression),
    ]
    if clinical is not None:
        assets.append(_asset("clinical", "clinical_metadata", "clinical_repository", clinical))
    if sample is not None:
        assets.append(_asset("sample", "sample_metadata", "sample_metadata_repository", sample))
    payload = {"schema_version": "biomedpilot.repository_manifest.v1", "assets": assets, "source_state": {"source_state_hash": "dataset-1"}}
    registry = {"schema_version": "biomedpilot.standardized_assets_registry.v2", "assets": assets}
    repo_path = root / "standardized_data" / "repositories" / "repository_manifest.json"
    registry_path = root / "manifests" / "standardized_assets_registry.json"
    repo_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    repo_path.write_text(json.dumps(payload), encoding="utf-8")
    registry_path.write_text(json.dumps(registry), encoding="utf-8")


def _asset(asset_id: str, asset_type: str, repository: str, path: Path) -> dict[str, object]:
    return {"asset_id": asset_id, "asset_type": asset_type, "repository": repository, "path": str(path), "file_path": str(path), "validation_status": "passed"}
