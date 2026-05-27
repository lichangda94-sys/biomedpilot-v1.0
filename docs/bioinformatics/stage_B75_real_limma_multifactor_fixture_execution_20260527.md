# B75 Real limma Multi-factor Fixture Execution

## Audit

B73/B74 defined multi-factor DEG provenance and confirmation contracts, but there was no real Rscript execution path proving that a controlled limma design can produce a formal DEG result table and result index v2 entry.

## Implementation

- Added a detect-first external Rscript/limma dependency snapshot.
- Added a controlled multi-factor limma fixture runner using `~ batch + group` and contrast `groupcase`.
- The runner writes:
  - DEG result table with p-value and adjusted p-value columns
  - task-run log
  - dependency snapshot in the result entry
  - B73/B74 parameter manifest provenance
  - result index v2 entry with `result_semantics=formal_computed_result`

## Boundary

B75 only activates a controlled limma fixture execution adapter. It does not expose a user-facing formal multi-factor DEG button, does not generate plots or reports, and does not output clinical interpretation.
