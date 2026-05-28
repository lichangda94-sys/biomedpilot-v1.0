# B92 Enrichment Production Hardening Planning

## Scope

B92 plans the next hardening track for ORA and preranked GSEA after the B81-B90 controlled enrichment MVP and MainLine carry-over convergence.

This stage is planning only. It does not change B81-B88 public contracts, does not enable new formal GSEA modes, does not publish ReleaseBuild, and does not add clinical interpretation.

## Current Implemented Baseline

The current enrichment layer supports a controlled, gated internal-test MVP:

| Area | Current state |
| --- | --- |
| Resource gate | `enrichment_resources.py` validates selected GMT-like resources and registry metadata |
| Backend gate | `enrichment_backend.py` consumes external R enrichment detector output detect-first |
| ORA adapter | `enrichment_r_adapter.py` runs controlled ORA through `clusterProfiler::enricher` when gates pass |
| GSEA adapter | `enrichment_r_adapter.py` runs controlled preranked GSEA through `fgsea` when gates pass |
| Parameter confirmation | `enrichment_execution_gate.py` requires source/result/resource/backend/parameter confirmation |
| Result review | `enrichment_result_review.py` reviews and exports formal ORA/GSEA tables |
| Plot/report gate | `enrichment_plot_report.py` creates gated SVG artifacts and section-only report package |
| UI gate | Analysis Center shows ORA/GSEA actions, blockers, warnings and disabled reasons |
| Carry-over status | B90 carried B81-B88 into MainLine; ReleaseBuild receive remains separate |

Current result semantics remain:

- formal ORA/GSEA only from controlled gated execution;
- imported/testing/exploratory/preflight results cannot become formal enrichment results;
- section report packages are enrichment-only, not full integrated reports;
- biological interpretation remains statistical/research context only, not clinical advice.

## Gap Audit

The current layer is not yet production-grade enrichment analysis because the following areas are incomplete:

| Gap | Current limitation | Required hardening |
| --- | --- | --- |
| Resource versioning | Registry records basic source metadata but not a strict immutable resource lock | Add resource lock manifest with collection, version, checksum, license, species, namespace and acquisition mode |
| Multi-library policy | GO/KEGG/Reactome/MSigDB/custom are visible but not governed by a unified production policy | Define supported library matrix, required backend/resource capabilities and disabled reasons |
| Background universe | ORA can run with controlled input but background strategy is not production-hardened | Require explicit background manifest and block implicit/unreviewed universe |
| Gene identifier compatibility | Resource/input identifier compatibility is basic | Add namespace mapping policy and strict blocker for unsupported ID-space mismatch |
| Multiple testing explanation | p.adjust/qvalue are present but explanation and policy are not deeply audited | Add multiple-testing policy manifest and report limitations |
| Ranking metric provenance | GSEA uses controlled rank input, but ranking metric provenance can be deeper | Require ranking metric manifest tied to source DEG result and thresholds |
| Resource-level QC | GMT validation exists, but needs production thresholds and duplicated-term handling | Add min/max gene-set size, duplicate term policy, empty/oversized set blockers |
| Cross-resource consistency | No acceptance matrix across GO/KEGG/Reactome/MSigDB/custom | Add fixture matrix and stable blockers for missing resources/backends |
| UI guidance | UI shows gate status but not full production repair workflow | Add resource/version/background/ID-space repair guidance rows |
| Report package | Section package exists but lacks resource lock and background strategy snapshot | Add enrichment production audit attachments to section package |

## Production Hardening Track

### B93 Enrichment Resource Version Lock and Library Policy

Goal: make every selected enrichment resource reproducible.

Planned outputs:

- `enrichment_resource_lock.json`
- library policy matrix for GO / KEGG / Reactome / MSigDB / custom GMT
- immutable fields: resource id, collection, source, source version, species, gene namespace, checksum, license note, acquisition mode, created_at
- blockers for missing checksum, unknown source version, unsupported species, unaccepted license policy, and unselected resource

Boundaries:

- No automatic MSigDB download.
- No hidden online download during formal execution.
- No resource substitution after user confirmation.

### B94 Enrichment Background Universe and Identifier Compatibility Gate

Goal: formal ORA/GSEA must prove source result, selected genes, background universe and gene-set identifiers are compatible.

Planned outputs:

- background universe manifest
- input/resource namespace compatibility gate
- selected gene derivation manifest for ORA
- ranking metric manifest for GSEA
- blockers for missing background, ID-space mismatch, empty overlap, duplicated feature policy missing, and untraceable rank metric

Boundaries:

- Do not silently infer background from arbitrary visible table columns.
- Do not auto-map identifiers without an audited mapping manifest.

### B95 Enrichment Statistical Policy and Result Schema Hardening

Goal: harden ORA/GSEA parameter and result contracts.

Planned outputs:

- enrichment statistical policy manifest
- multiple testing policy snapshot
- min/max gene-set size policy
- result schema additions for resource lock, background universe, identifier compatibility, ranking metric, library policy and statistical policy
- blockers for missing adjusted p-value, missing method, invalid p-value range, invalid NES/ES, or missing pathway size

Boundaries:

- No automatic biological conclusion.
- No clinical interpretation.

### B96 Enrichment Production Audit Package

Goal: make formal enrichment outputs independently auditable.

Planned package contents:

- `manifests/resource_lock.json`
- `manifests/background_universe.json`
- `manifests/identifier_compatibility.json`
- `manifests/statistical_policy.json`
- `manifests/parameter_confirmation.json`
- `manifests/dependency_snapshot.json`
- `manifests/result_index_snapshot.json`
- `tables/enrichment_results.tsv`
- `plots/` only for registered formal enrichment plot artifacts
- `logs/`
- `README_limitations.md`

Boundaries:

- Package accepts only formal enrichment results.
- Section package remains enrichment-only unless a later integrated-report gate explicitly includes it.

### B97 Enrichment Cross-Library / Cross-Project Acceptance

Goal: validate stable behavior across supported resource and project types.

Acceptance fixtures:

- GO-like GMT positive fixture
- KEGG-like TERM2GENE positive fixture
- Reactome-like GMT positive fixture when backend/resource gates pass
- MSigDB-like imported GMT positive fixture when user-provided lock passes
- custom GMT with duplicated terms
- ID-space mismatch negative fixture
- missing background negative fixture
- missing backend negative fixture
- preflight/testing/imported source negative fixture

Required checks:

- source runtime consistency;
- packaged runtime consistency where detector payload is present;
- open-W smoke consistency;
- result index v2 completeness;
- no traceback for missing resource/backend cases.

### B98 Enrichment UI Production Preview

Goal: expose production readiness without implying full automatic interpretation.

UI additions:

- resource lock row
- background universe row
- identifier compatibility row
- statistical policy row
- library capability row
- production audit package row
- repair guidance for resource/version/background/ID-space blockers

Boundary wording:

- controlled ORA / controlled preranked GSEA only;
- not a clinical interpretation;
- not a full biological conclusion engine;
- disabled reasons must remain visible.

### B99 Enrichment Production-Readiness Closure Audit

Goal: close B92-B98 with a release-readiness style audit.

Report must include:

- capability matrix;
- resource/library support matrix;
- backend/runtime status;
- cross-project acceptance results;
- UI disabled reason checks;
- package/open-W/codesign status if code changed;
- blocker/major/minor;
- recommendation for ReleaseBuild receive.

Conclusion labels:

- `production-readiness_candidate_internal`
- `conditional_internal_candidate`
- `not_ready`

The report must not claim public-release readiness or clinical-grade interpretation.

## Public Contract Additions Planned

Future stages may add these payloads:

- `biomedpilot.enrichment_resource_lock.v1`
- `biomedpilot.enrichment_background_universe.v1`
- `biomedpilot.enrichment_identifier_compatibility_gate.v1`
- `biomedpilot.enrichment_statistical_policy.v1`
- `biomedpilot.enrichment_production_audit_package.v1`
- `biomedpilot.enrichment_production_readiness_gate.v1`

Existing B81-B88 payloads remain valid. New fields should be additive and backward-compatible unless a stage explicitly audits migration.

## Test Strategy

Each implementation stage should run:

```bash
git diff --check
python3 -m pytest tests/bioinformatics -q -k "enrichment or gsea or gene_set or analysis_ui"
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q -k "analysis_task or enrichment or gsea"
python3 -m app.main --smoke-test
```

B97/B99 should additionally run:

```bash
python3 -m pytest tests/bioinformatics -q
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q
python3 scripts/package_app.py --smoke-test
open -W -n dist/BioMedPilot.app --args --smoke-test
codesign --verify --deep --strict --verbose=2 dist/BioMedPilot.app
```

## Development Boundaries

The B92-B99 track must not:

- enable full automatic GSEA modes beyond controlled preranked GSEA;
- auto-download or auto-install R/Bioconductor packages;
- auto-download MSigDB without user-provided licensed resource;
- bypass formal DEG source-result gates;
- promote imported/testing/exploratory/preflight outputs to formal enrichment results;
- generate survival, clinical, treatment, diagnostic or prognostic conclusions;
- turn section-only enrichment output into a full integrated report without the integrated report gate.

## Final Recommendation

Proceed next to B93 Enrichment Resource Version Lock and Library Policy.

ReleaseBuild can continue B91 independently. Bioinformatics can develop B93-B99 as additive production hardening as long as B81-B88 public contracts remain stable until ReleaseBuild has completed its receive/closure gate.
