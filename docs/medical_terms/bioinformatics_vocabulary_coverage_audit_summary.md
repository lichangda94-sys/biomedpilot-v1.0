# Bioinformatics Vocabulary Coverage Audit Summary

Generated: 2026-05-18

## Conclusions

- TCGA: {'total': 33, 'complete': 33, 'partial': 0, 'missing': 0, 'needs_review': 0}
- GTEx: {'total': 23, 'complete': 18, 'partial': 0, 'missing': 0, 'needs_review': 5}
- GEO core: {'total': 54, 'complete': 26, 'partial': 0, 'missing': 28, 'needs_review': 0}

GEO is reported as core coverage only; this stage does not claim long-tail GEO vocabulary completeness.

## Missing Items

| source | term | reason |
| --- | --- | --- |
| GEO | Homo sapiens | Keep as GEO core future candidate; do not claim full GEO coverage. |
| GEO | Mus musculus | Keep as GEO core future candidate; do not claim full GEO coverage. |
| GEO | mouse | Keep as GEO core future candidate; do not claim full GEO coverage. |
| GEO | Rattus norvegicus | Keep as GEO core future candidate; do not claim full GEO coverage. |
| GEO | adjacent normal | Keep as GEO core future candidate; do not claim full GEO coverage. |
| GEO | untreated | Keep as GEO core future candidate; do not claim full GEO coverage. |
| GEO | vehicle | Keep as GEO core future candidate; do not claim full GEO coverage. |
| GEO | sham | Keep as GEO core future candidate; do not claim full GEO coverage. |
| GEO | resistant | Keep as GEO core future candidate; do not claim full GEO coverage. |
| GEO | wild type | Keep as GEO core future candidate; do not claim full GEO coverage. |
| GEO | mutant | Keep as GEO core future candidate; do not claim full GEO coverage. |
| GEO | knockdown | Keep as GEO core future candidate; do not claim full GEO coverage. |
| GEO | overexpression | Keep as GEO core future candidate; do not claim full GEO coverage. |
| GEO | count matrix | Keep as GEO core future candidate; do not claim full GEO coverage. |
| GEO | raw counts | Keep as GEO core future candidate; do not claim full GEO coverage. |
| GEO | TPM | Keep as GEO core future candidate; do not claim full GEO coverage. |
| GEO | FPKM | Keep as GEO core future candidate; do not claim full GEO coverage. |
| GEO | RPKM | Keep as GEO core future candidate; do not claim full GEO coverage. |
| GEO | CPM | Keep as GEO core future candidate; do not claim full GEO coverage. |
| GEO | gene symbol | Keep as GEO core future candidate; do not claim full GEO coverage. |
| GEO | Ensembl ID | Keep as GEO core future candidate; do not claim full GEO coverage. |
| GEO | probe ID | Keep as GEO core future candidate; do not claim full GEO coverage. |
| GEO | series matrix | Keep as GEO core future candidate; do not claim full GEO coverage. |
| GEO | sample metadata | Keep as GEO core future candidate; do not claim full GEO coverage. |
| GEO | platform annotation | Keep as GEO core future candidate; do not claim full GEO coverage. |
| GEO | dataset | Keep as GEO core future candidate; do not claim full GEO coverage. |
| GEO | sample | Keep as GEO core future candidate; do not claim full GEO coverage. |
| GEO | series | Keep as GEO core future candidate; do not claim full GEO coverage. |

## Needs Manual Review

| source | term | reason |
| --- | --- | --- |
| GTEx | Skin | Broad body term requires context-aware matching. |
| GTEx | Heart | Broad body term requires context-aware matching. |
| GTEx | Muscle | Broad body term requires context-aware matching. |
| GTEx | Artery | Broad body term requires context-aware matching. |
| GTEx | Nerve | Broad body term requires context-aware matching. |

## Suggested Later Patch

Add reviewed missing GEO species, sample-state, and data-format terms to Bioinformatics-specific vocabulary files before any runtime exposure.

## Why Nothing Was Auto-Merged

This stage is an audit stage. It does not automatically promote Bioinformatics terms into shared core or Meta runtime.
