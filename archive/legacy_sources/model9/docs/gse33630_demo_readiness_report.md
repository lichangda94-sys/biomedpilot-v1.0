# GSE33630 Demo Readiness Report

This report summarizes the current controlled readiness status for `GSE33630`. It is a demo/readiness document only. It is not a formal DEG result and does not include p-values, FDR, enrichment, survival, production downloader changes, or `geo_workflow.py` changes.

## Dataset

- dataset id: `GSE33630`
- topic: papillary thyroid carcinoma readiness benchmark.
- comparison candidate: PTC vs normal/control.
- platform: `GPL570`.

## Current Harness Result

- preflight runnable: true.
- gap count: 0.
- feature count: 54675.
- sample count: 105.
- mapping success rate: 0.8373.
- PTC samples: 49.
- normal/control samples: 45.
- ATC samples excluded: 11.
- recommended action: `ready_for_manual_review`.

## Demonstration Value

GSE33630 is the first end-to-end readiness demonstration because it exercises the current real-dataset harness without requiring production downloads or formal analysis:

- GEO accession metadata readiness.
- Series Matrix metadata readiness.
- group detection for PTC, normal/control, and excluded ATC samples.
- expression matrix report.
- GPL570 probe-to-symbol mapping readiness.
- DEG-ready matrix readiness.
- structured real dataset readiness report.

## Boundaries

This demo is not formal DEG:

- no p-value.
- no FDR.
- no limma, DESeq2, or edgeR.
- no enrichment.
- no survival analysis.
- no production downloader changes.
- no `geo_workflow.py` changes.

The next useful display step is a read-only UI summary for `RealDatasetReadinessReport`. The next dataset coverage step is local-file testing for `GSE60542` or `GSE27155` after manual files are provided.
