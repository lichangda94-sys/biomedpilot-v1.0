from __future__ import annotations

from app.bioinformatics.enrichment_acceptance import build_enrichment_cross_library_acceptance_gate


def test_enrichment_cross_library_acceptance_gate_covers_positive_and_negative_scenarios() -> None:
    gate = build_enrichment_cross_library_acceptance_gate()

    assert gate["schema_version"] == "biomedpilot.enrichment_cross_library_acceptance.v1"
    assert gate["status"] == "passed"
    assert gate["scenario_count"] == 12
    assert gate["passed_scenario_count"] == 12
    matrix = gate["acceptance_matrix"]
    assert matrix["go_bp"] == "passed"
    assert matrix["kegg"] == "passed"
    assert matrix["reactome"] == "passed"
    assert matrix["msigdb_hallmark"] == "passed"
    assert matrix["custom_gmt"] == "passed"
    assert matrix["id_mismatch_negative"] == "passed"
    assert matrix["missing_background_negative"] == "passed"
    assert matrix["missing_backend_negative"] == "passed"
    assert matrix["non_formal_source_negative"] is True
    assert gate["semantic_boundary"] == "acceptance_gate_only_not_enrichment_execution_or_interpretation"


def test_enrichment_cross_library_acceptance_records_stable_negative_blockers() -> None:
    gate = build_enrichment_cross_library_acceptance_gate()
    rows = {row["scenario_id"]: row for row in gate["scenario_rows"]}

    assert rows["id_space_mismatch_negative"]["expected_blocker"] == "source_resource_gene_id_type_mismatch:symbol!=entrez"
    assert "source_resource_gene_id_type_mismatch:symbol!=entrez" in rows["id_space_mismatch_negative"]["observed_blockers"]
    assert rows["missing_background_negative"]["expected_blocker"] == "background_universe_empty"
    assert "background_universe_empty" in rows["missing_background_negative"]["observed_blockers"]
    assert rows["missing_backend_negative"]["expected_blocker"] == "external_enrichment_backend_detection_missing"
    assert "external_enrichment_backend_detection_missing" in rows["missing_backend_negative"]["observed_blockers"]
    assert rows["preflight_source_negative"]["expected_blocker"] == "enrichment_source_result_not_formal:preflight_only"
    assert rows["imported_source_negative"]["expected_blocker"] == "enrichment_source_result_not_formal:imported_external_result"
