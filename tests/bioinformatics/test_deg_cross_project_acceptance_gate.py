from __future__ import annotations

from pathlib import Path

from app.bioinformatics.deg_engine import build_deg_cross_project_acceptance_gate, build_deg_real_world_fixture_acceptance, evaluate_deg_cross_project_scenario


def test_cross_project_acceptance_passes_local_and_tcga_like_counts(tmp_path: Path) -> None:
    local = evaluate_deg_cross_project_scenario(_package(tmp_path / "local", value_type="count"), scenario_id="local_count", dependency_snapshot=_dependency())
    tcga = evaluate_deg_cross_project_scenario(_package(tmp_path / "tcga", value_type="raw_count"), scenario_id="tcga_like_count", dependency_snapshot=_dependency())

    gate = build_deg_cross_project_acceptance_gate([local, tcga])

    assert local["status"] == "passed"
    assert tcga["status"] == "passed"
    assert gate["status"] == "passed"
    assert gate["passed_scenarios"] == ["local_count", "tcga_like_count"]


def test_cross_project_acceptance_blocks_geo_probe_without_mapping(tmp_path: Path) -> None:
    scenario = evaluate_deg_cross_project_scenario(
        _package(tmp_path, value_type="TPM", gene_id_type="ID_REF", feature_validation="blocked"),
        scenario_id="geo_microarray_unmapped",
        dependency_snapshot=_dependency(),
    )

    assert scenario["status"] == "blocked"
    assert "geo_probe_or_id_ref_requires_platform_mapping" in scenario["blockers"]


def test_cross_project_acceptance_blocks_tpm_for_count_model(tmp_path: Path) -> None:
    scenario = evaluate_deg_cross_project_scenario(
        _package(tmp_path, value_type="TPM"),
        scenario_id="tpm_count_model_negative",
        dependency_snapshot=_dependency(),
        requested_method_family="deseq2",
    )

    assert "tpm_fpkm_or_log_expression_not_allowed_for_count_model_deg" in scenario["blockers"]


def test_cross_project_acceptance_blocks_batch_confounding_sample_mismatch_and_dependency(tmp_path: Path) -> None:
    confounded = evaluate_deg_cross_project_scenario(
        _package(tmp_path / "confounded", value_type="count"),
        scenario_id="batch_confounded_negative",
        dependency_snapshot=_dependency(),
        design_manifest={"batch_assignments": {"batch": {"S1": "B1", "S2": "B1", "S3": "B2", "S4": "B2"}}},
    )
    mismatch = evaluate_deg_cross_project_scenario(
        _package(tmp_path / "mismatch", value_type="count", sample_rows="sample_id\tgroup\nX1\tcase\nX2\tcontrol\n"),
        scenario_id="sample_mismatch_negative",
        dependency_snapshot=_dependency(),
    )
    missing_dependency = evaluate_deg_cross_project_scenario(
        _package(tmp_path / "dependency", value_type="count"),
        scenario_id="missing_dependency_negative",
        dependency_snapshot={"status": "blocked", "blockers": ["missing_python_package:scipy"]},
    )

    assert "group_covariate_fully_confounded:batch" in confounded["blockers"]
    assert "expression_and_metadata_samples_do_not_overlap" in mismatch["blockers"]
    assert "missing_python_package:scipy" in missing_dependency["blockers"]


def test_real_world_fixture_acceptance_has_expected_positive_and_negative_scenarios(tmp_path: Path) -> None:
    gate = build_deg_real_world_fixture_acceptance(tmp_path, dependency_snapshot=_dependency())

    assert gate["status"] == "passed"
    assert gate["positive_scenarios_passed"] is True
    assert gate["negative_scenarios_blocked"] is True
    assert set(gate["expected_positive_scenarios"]).issubset(set(gate["passed_scenarios"]))
    assert set(gate["expected_negative_scenarios"]).issubset(set(gate["blocked_scenarios"]))


def _package(
    root: Path,
    *,
    value_type: str,
    gene_id_type: str = "symbol",
    feature_validation: str = "passed",
    sample_rows: str = "sample_id\tgroup\nS1\tcase\nS2\tcase\nS3\tcontrol\nS4\tcontrol\n",
) -> dict[str, object]:
    root.mkdir(parents=True, exist_ok=True)
    matrix = root / "matrix.tsv"
    matrix.write_text("gene\tS1\tS2\tS3\tS4\nTP53\t100\t120\t20\t25\nBRCA1\t80\t90\t30\t35\n", encoding="utf-8")
    sample = root / "sample.tsv"
    sample.write_text(sample_rows, encoding="utf-8")
    return {
        "input_package_id": f"pkg-{root.name}",
        "package_type": "deg_recompute",
        "value_type": value_type,
        "gene_id_type": gene_id_type,
        "expression_asset": {"asset_id": "expr", "path": str(matrix), "asset_type": "raw_count_matrix"},
        "sample_metadata_asset": {"asset_id": "sample", "path": str(sample), "asset_type": "sample_metadata"},
        "group_design_asset": {"asset_id": "group", "asset_type": "group_design"},
        "feature_annotation_asset": {"asset_id": "feature", "validation_status": feature_validation, "asset_type": "feature_annotation"},
        "blockers": [],
        "warnings": [],
    }


def _dependency() -> dict[str, object]:
    return {
        "status": "passed",
        "blockers": [],
        "packages": {
            "numpy": {"available": True},
            "pandas": {"available": True},
            "scipy": {"available": True},
            "statsmodels": {"available": True},
        },
        "r_backend": {"packages": {"limma": {"available": True}, "DESeq2": {"available": True}, "edgeR": {"available": True}}},
    }
