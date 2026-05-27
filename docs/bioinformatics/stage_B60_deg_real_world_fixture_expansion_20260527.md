# B60 DEG Real-World Fixture Expansion

## Audit

B57 had acceptance scenarios, but the fixture matrix lived mainly in tests. B60 promotes the matrix to reusable code so ReleaseBuild gates and future audits can run the same positive/negative scenarios.

## Implementation

- Added `build_deg_real_world_fixture_acceptance`.
- Fixture coverage:
  - local count positive
  - TCGA-like raw count positive
  - GEO microarray mapped positive
  - GEO microarray unmapped negative
  - TPM count-model negative
  - batch-confounded negative
  - sample mismatch negative
  - missing dependency negative
- The aggregate gate passes only when expected positives pass and expected negatives block.

## Boundary

The fixture gate does not create formal results. It only validates cross-project gate behavior and stable blockers.
