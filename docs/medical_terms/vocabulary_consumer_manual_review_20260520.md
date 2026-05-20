# Vocabulary Consumer Manual Review

Date: 2026-05-20

## Scope

This report manually reviews the 15 paths previously marked `manual_review_required` in `vocabulary_consumer_adoption_audit.json`.

No business code was refactored. No loader behavior was changed. No vocabulary runtime files were modified.

## Summary

- Reviewed paths: `15`
- `approved_script_internal`: `13`
- `needs_scope_loader_migration`: `2`
- `safe_test_fixture`: `0`
- `manual_fix_required`: `0`
- Business runtime bypass found: `false`

## Decisions

| path | matched file | final classification | business runtime path | reason |
| --- | --- | --- | --- | --- |
| `scripts/audit_bioinformatics_vocabulary_coverage.py:21` | `mini_medical_terms_index.json` | `needs_scope_loader_migration` | `false` | This historical Bioinformatics coverage audit reads shared mini/zh files directly; if reused, it should migrate to Bioinformatics scoped audit JSON or load_terms(scope='bioinformatics') to avoid pre-fix source-of-truth drift. |
| `scripts/audit_bioinformatics_vocabulary_coverage.py:22` | `zh_term_overrides.json` | `needs_scope_loader_migration` | `false` | This historical Bioinformatics coverage audit reads shared mini/zh files directly; if reused, it should migrate to Bioinformatics scoped audit JSON or load_terms(scope='bioinformatics') to avoid pre-fix source-of-truth drift. |
| `scripts/audit_medical_terms_scope_isolation.py:16` | `mini_medical_terms_index.json` | `approved_script_internal` | `false` | This script writes a static scope-isolation policy artifact; the references are declared allowed source names, not runtime vocabulary consumption. |
| `scripts/audit_medical_terms_scope_isolation.py:16` | `zh_term_overrides.json` | `approved_script_internal` | `false` | This script writes a static scope-isolation policy artifact; the references are declared allowed source names, not runtime vocabulary consumption. |
| `scripts/audit_medical_terms_scope_isolation.py:20` | `mini_medical_terms_index.json` | `approved_script_internal` | `false` | This script writes a static scope-isolation policy artifact; the references are declared allowed source names, not runtime vocabulary consumption. |
| `scripts/audit_medical_terms_scope_isolation.py:20` | `zh_term_overrides.json` | `approved_script_internal` | `false` | This script writes a static scope-isolation policy artifact; the references are declared allowed source names, not runtime vocabulary consumption. |
| `scripts/audit_medical_vocabulary_coverage.py:14` | `mini_medical_terms_index.json` | `approved_script_internal` | `false` | This is an offline coverage/reference audit over curated shared source files. Direct file reads are acceptable as audit inputs and do not affect runtime scope isolation. |
| `scripts/audit_medical_vocabulary_coverage.py:15` | `zh_term_overrides.json` | `approved_script_internal` | `false` | This is an offline coverage/reference audit over curated shared source files. Direct file reads are acceptable as audit inputs and do not affect runtime scope isolation. |
| `scripts/inventory_shared_core_pollution.py:10` | `mini_medical_terms_index.json` | `approved_script_internal` | `false` | This inventory must inspect raw shared-core and Meta mirror files directly; using scope loader would hide the file-layer pollution being audited. |
| `scripts/inventory_shared_core_pollution.py:11` | `meta_seed_terms.json` | `approved_script_internal` | `false` | This inventory must inspect raw shared-core and Meta mirror files directly; using scope loader would hide the file-layer pollution being audited. |
| `scripts/inventory_shared_core_pollution.py:164` | `mini_medical_terms_index.json` | `approved_script_internal` | `false` | This inventory must inspect raw shared-core and Meta mirror files directly; using scope loader would hide the file-layer pollution being audited. |
| `scripts/inventory_shared_core_pollution.py:190` | `meta_migrated_from_shared_terms.json` | `approved_script_internal` | `false` | This inventory must inspect raw shared-core and Meta mirror files directly; using scope loader would hide the file-layer pollution being audited. |
| `scripts/update_medical_term_index.py:19` | `mini_medical_terms_index.json` | `approved_script_internal` | `false` | This is an optional index builder/source metadata updater. The mini index path is an explicit build input, not business runtime lookup. |
| `scripts/update_medical_term_index.py:639` | `mini_medical_terms_index.json` | `approved_script_internal` | `false` | This is an optional index builder/source metadata updater. The mini index path is an explicit build input, not business runtime lookup. |
| `scripts/update_medical_term_index.py:639` | `zh_term_overrides.json` | `approved_script_internal` | `false` | This is an optional index builder/source metadata updater. The mini index path is an explicit build input, not business runtime lookup. |

## Follow-Up

`script_audit_bioinformatics_vocabulary_coverage_scope_migration` is recommended as a separate low/medium priority maintenance patch. It should retire or update `scripts/audit_bioinformatics_vocabulary_coverage.py` so it cannot regenerate pre-scoped Bioinformatics status from `mini_medical_terms_index.json` and `zh_term_overrides.json`.

No immediate business fix is required because no runtime business path was found bypassing the scope-aware loader.
