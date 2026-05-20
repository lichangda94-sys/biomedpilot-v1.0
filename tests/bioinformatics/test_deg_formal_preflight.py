from __future__ import annotations

from app.bioinformatics.deg_ready.preflight import build_deg_formal_preflight


def test_deg_formal_preflight_blocks_tpm_count_model() -> None:
    preflight = build_deg_formal_preflight(
        {
            "source_input_package_id": "pkg",
            "deg_ready_package_id": "ready",
            "value_type": "TPM",
            "blockers": [],
            "warnings": [],
            "sample_alignment_status": {"status": "passed"},
            "gene_mapping_status": {"status": "passed"},
        },
        method_candidate="count_model",
    )

    assert preflight["status"] == "blocked"
    assert "tpm_fpkm_or_log_expression_not_allowed_for_count_model_deg" in preflight["blockers"]
    assert "p_value" in preflight["forbidden_outputs"]
