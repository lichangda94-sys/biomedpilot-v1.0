# B77 Real edgeR Multi-factor Fixture Execution

## Audit

limma and DESeq2 multi-factor fixtures were registered through result index v2, but edgeR still needed an equivalent controlled raw-count path before UI execution gates could truthfully show all three R backends.

## Implementation

- Extended the external Rscript dependency detector to support edgeR.
- Added a controlled raw-count edgeR fixture using design `~ batch + group` and coefficient `groupcase`.
- Wrote DEG result table, task-run log, dependency snapshot, parameter manifest, and result index v2 entry.
- Kept `plot_artifacts=[]`, `report_artifacts=[]`, and `report_ready_eligible=False`.

## Boundary

edgeR multi-factor execution is controlled-fixture only and raw-count only. TPM/FPKM/log-expression inputs are blocked before Rscript execution. B77 does not add formal UI execution, plots, report-ready export, GSEA, survival, or clinical interpretation.
