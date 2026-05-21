# Medical Terms Source Of Truth Index

Date: 2026-05-20

## Current Source Of Truth

- GEO current audit: `data/medical_terms/bioinformatics/audits/geo_core_terms_coverage_audit.json`
- GTEx current audit: `data/medical_terms/bioinformatics/audits/gtex_terms_coverage_audit.json`
- Meta seed current list: `data/medical_terms/meta_analysis/meta_seed_terms.json`
- Scope mirror: `data/medical_terms/meta_analysis/meta_migrated_from_shared_terms.json`
- Legacy compatibility: `data/medical_terms/meta_analysis/legacy_meta_compatibility_map.json`
- Shared cleanup decision: `data/medical_terms/review_reports/shared_core_cleanup_decision.json`
- Final handoff: `docs/medical_terms/medical_terms_phase_final_handoff_20260520.md`

## Document Status Policy

Old documents are not deleted in this phase. This index marks known pre-fix or historical documents so future work should not treat them as current operational state.

## Historical / Superseded Documents

- `docs/medical_terms/bioinformatics_vocabulary_coverage_audit_summary.md`: `superseded_or_historical`; superseded_by=`medical_terms_phase_final_handoff_20260520.md`; May describe pre-fix Bioinformatics state; use machine-readable audit JSON files for current status.
- `docs/medical_terms/geo_core_terms_coverage_audit.md`: `superseded_or_historical`; superseded_by=`medical_terms_phase_final_handoff_20260520.md`; May describe pre-fix Bioinformatics state; use machine-readable audit JSON files for current status.
- `docs/medical_terms/gtex_terms_coverage_audit.md`: `superseded_or_historical`; superseded_by=`medical_terms_phase_final_handoff_20260520.md`; May describe pre-fix Bioinformatics state; use machine-readable audit JSON files for current status.
- `docs/medical_terms/manual_review_required_report.md`: `historical_review_artifact`; superseded_by=`shared_core_cleanup_decision_20260520.md`; Historical manual review artifact; not current runtime source of truth.
- `docs/medical_terms/medical_terms_phase_final_handoff_20260520.md`: `current_handoff`; superseded_by=`None`; Top-level handoff summary.
- `docs/medical_terms/meta_seed_expansion_batch2_audit_20260519.md`: `current_audit_summary`; superseded_by=`None`; Current curated Meta seed audit summary; machine-readable seed JSON remains source of truth.
- `docs/medical_terms/meta_seed_mvp_audit_20260518.md`: `current_audit_summary`; superseded_by=`None`; Current curated Meta seed audit summary; machine-readable seed JSON remains source of truth.
- `docs/medical_terms/shared_core_pollution_manual_review_required.md`: `historical_review_artifact`; superseded_by=`shared_core_cleanup_decision_20260520.md`; Historical manual review artifact; not current runtime source of truth.
