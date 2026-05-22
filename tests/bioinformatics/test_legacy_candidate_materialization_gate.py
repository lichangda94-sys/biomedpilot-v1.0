from pathlib import Path

from app.bioinformatics.acquisition_adapters import (
    adapt_geo_detection_manifest,
    build_legacy_candidate_materialization_plan,
    materialize_legacy_standardized_asset_candidates,
    validate_legacy_candidate_materialization_plan,
    write_legacy_acquisition_manifest,
    write_legacy_standardized_asset_candidates,
)


def _prepare_geo_candidate(tmp_path: Path, *, source_exists: bool = True) -> dict[str, object]:
    source = tmp_path / "inputs" / "matrix.tsv"
    if source_exists:
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_text("gene\ts1\ts2\nTP53\t1\t2\n", encoding="utf-8")
    manifest = adapt_geo_detection_manifest(
        accession="GSE_MAT",
        scan_root=tmp_path,
        detection_result={
            "accession_type": "GSE",
            "has_expression_payload": True,
            "matrix_level": "gene",
            "candidate_expression_files": [str(source)],
        },
    )
    write_legacy_acquisition_manifest(tmp_path, manifest)
    return write_legacy_standardized_asset_candidates(tmp_path)


def test_materialization_copies_selected_candidate_without_registering_analysis_inputs(tmp_path: Path) -> None:
    bundle = _prepare_geo_candidate(tmp_path)
    candidate_id = bundle["candidates"][0]["candidate_id"]

    result = materialize_legacy_standardized_asset_candidates(tmp_path, selected_candidate_ids=[candidate_id])

    assert result["status"] == "materialized_candidates_only"
    assert result["materialized_asset_count"] == 1
    asset = result["assets"][0]
    assert asset["asset_role"] == "expression_matrix"
    assert asset["analysis_ready"] is False
    assert asset["formal_analysis_ready"] is False
    assert asset["result_semantics"] == "not_a_result"
    assert asset["report_ready_eligible"] is False
    assert asset["materialization_mode"] == "copied_file"
    assert Path(asset["path"]).exists()
    assert "TP53" in Path(asset["path"]).read_text(encoding="utf-8")
    assert result["downstream_contract"]["writes_repository_manifest"] is False
    assert result["downstream_contract"]["writes_analysis_input_repository"] is False
    assert result["downstream_contract"]["writes_result_index"] is False
    assert not (tmp_path / "standardized_data/repositories/repository_manifest.json").exists()
    assert not (tmp_path / "standardized_data/repositories/analysis_input_repository").exists()
    assert not (tmp_path / "results/summaries/result_index.json").exists()


def test_materialization_plan_requires_candidate_validation_and_later_gates(tmp_path: Path) -> None:
    _prepare_geo_candidate(tmp_path)

    plan = build_legacy_candidate_materialization_plan(tmp_path)

    assert plan["status"] == "materialization_plan_only"
    assert plan["downstream_contract"]["requires_later_repository_manifest_merge"] is True
    assert plan["downstream_contract"]["requires_b8_resolver_after_merge"] is True
    assert plan["validation"]["status"] == "passed"
    item = plan["plan_items"][0]
    assert item["writes_repository_manifest"] is False
    assert item["writes_analysis_input_repository"] is False
    assert item["writes_result_index"] is False
    assert item["formal_analysis_ready"] is False
    assert item["result_semantics"] == "not_a_result"


def test_missing_source_materializes_sidecar_only_and_remains_not_formal(tmp_path: Path) -> None:
    bundle = _prepare_geo_candidate(tmp_path, source_exists=False)
    candidate_id = bundle["candidates"][0]["candidate_id"]

    result = materialize_legacy_standardized_asset_candidates(tmp_path, selected_candidate_ids=[candidate_id])

    assert result["status"] == "materialized_candidates_only"
    asset = result["assets"][0]
    assert asset["materialization_mode"] == "sidecar_only"
    assert asset["formal_analysis_ready"] is False
    assert "candidate_source_path_not_found_sidecar_only" in asset["warnings"]
    payload = Path(asset["path"]).read_text(encoding="utf-8")
    assert "biomedpilot.legacy_materialized_asset_sidecar.v1" in payload


def test_materialization_plan_validation_blocks_formal_promotion(tmp_path: Path) -> None:
    _prepare_geo_candidate(tmp_path)
    plan = build_legacy_candidate_materialization_plan(tmp_path)
    plan["downstream_contract"] = {
        **plan["downstream_contract"],
        "writes_repository_manifest": True,
        "writes_result_index": True,
        "ready_for_formal_analysis": True,
    }
    plan["plan_items"][0] = {
        **plan["plan_items"][0],
        "formal_analysis_ready": True,
        "result_semantics": "formal_computed_result",
        "writes_analysis_input_repository": True,
    }

    validation = validate_legacy_candidate_materialization_plan(plan)

    assert validation["status"] == "blocked"
    assert "materialization_must_not_write_repository_manifest" in validation["blockers"]
    assert "materialization_must_not_write_result_index" in validation["blockers"]
    assert "materialization_must_not_be_formal_ready" in validation["blockers"]
    assert "plan_item_0:writes_analysis_input_repository_forbidden" in validation["blockers"]
    assert "plan_item_0:formal_analysis_ready_forbidden" in validation["blockers"]
    assert "plan_item_0:formal_result_semantics_forbidden" in validation["blockers"]


def test_blocked_candidate_is_not_materialized_as_asset(tmp_path: Path) -> None:
    manifest = adapt_geo_detection_manifest(
        accession="GSE_BLOCKED",
        scan_root=tmp_path,
        detection_result={"has_expression_payload": False, "matrix_level": "unknown", "candidate_metadata_files": ["missing.soft"]},
    )
    write_legacy_acquisition_manifest(tmp_path, manifest)
    bundle = write_legacy_standardized_asset_candidates(tmp_path)
    candidate_id = bundle["candidates"][0]["candidate_id"]

    result = materialize_legacy_standardized_asset_candidates(tmp_path, selected_candidate_ids=[candidate_id])

    assert result["status"] == "blocked"
    assert result["materialized_asset_count"] == 0
    assert "plan_item_0:geo_legacy_detection_missing_expression_payload" in result["blockers"]
