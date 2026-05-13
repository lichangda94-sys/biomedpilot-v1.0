# Stage V7 Medical Vocabulary Coverage Quality Gates

## Goal

Stage V7 turns the reference checklist audit into a quality gate. The audit
continues to measure the stable mini vocabulary plus Chinese overrides, while
the optional sqlite index remains a runtime enhancement.

## Gates

| Gate | Threshold |
| --- | ---: |
| Common cancer checklist coverage | >= 0.95 |
| TCGA project checklist coverage | >= 0.90 |
| GTEx tissue weighted coverage | >= 0.95 |
| Meta retrieval term coverage | >= 0.90 |
| Missing reference items | 0 |
| P0 gaps | 0 |
| Audit cross-context pollution | 0 |

## Current Result

After Stage 2.5 and V6, all gates pass:

- Overall coverage: 1.000
- Weighted coverage: 1.000
- Missing items: 0
- P0/P1/P2 gaps: none
- Audit cross-context pollution: 0

## Boundaries

- Does not modify Bioinformatics business code.
- Does not modify Meta Analysis business code.
- Does not change retrieval execution logic.
- Does not make `medical_terms_index.sqlite` mandatory.
- Does not redefine coverage audit around the optional sqlite index.

## Validation

Run:

```bash
python3 scripts/audit_medical_vocabulary_coverage.py
python3 -m pytest tests/shared/test_medical_vocabulary_reference_audit.py
```
