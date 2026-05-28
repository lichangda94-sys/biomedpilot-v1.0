# B99 Enrichment Production-Readiness Closure Audit

## Scope

B99 closes the B92-B98 enrichment production hardening track for controlled ORA and controlled preranked GSEA. This is an internal production-readiness audit, not a public-release or clinical-grade claim.

The audited range includes:

- B92 production hardening plan;
- B93 resource version lock and library policy;
- B94 background universe and identifier compatibility;
- B95 statistical policy and result schema;
- B96 production audit package;
- B97 cross-library / cross-project acceptance;
- B98 Analysis Center production preview.

## Capability Matrix

| Area | Current status | Boundary |
| --- | --- | --- |
| Controlled ORA | Implemented behind formal DEG source, resource, backend, parameter, result schema gates | Statistical enrichment only |
| Controlled preranked GSEA | Implemented behind formal DEG source, resource, backend, parameter, result schema gates | Preranked controlled mode only |
| Resource lock | Implemented | No silent download, no auto-install |
| Background universe | Implemented from formal DEG result table | No imported/testing/preflight source |
| Identifier compatibility | Implemented | Mismatched source/resource gene ID blocks |
| Statistical policy | Implemented with FDR policy validation | No biological or clinical conclusion engine |
| Result schema gate | Implemented for formal ORA/GSEA result index v2 records | Blocks imported/testing/exploratory/preflight |
| Production audit package | Implemented for formal enrichment result only | Not report-ready and not full integrated report |
| Cross-library acceptance | Implemented | Fixture acceptance, not public resource certification |
| Analysis UI preview | Implemented | Preview/review-only for production audit readiness |

## Resource / Library Support Matrix

| Library family | Supported controlled path | Resource policy | Current notes |
| --- | --- | --- | --- |
| GO BP/CC/MF | ORA, preranked GSEA | Local registry/resource lock | Requires version, checksum, species, gene ID type |
| KEGG | ORA, preranked GSEA | Local registry/resource lock and usage-rights note | Entrez ID compatibility required when resource uses Entrez |
| Reactome | ORA, preranked GSEA | Local registry/resource lock; Reactome source/version required | Current detector can import `ReactomePA` |
| MSigDB Hallmark | ORA, preranked GSEA | User-provided licensed GMT only | Current detector can import `msigdbr`; license still user-governed |
| Custom GMT | ORA, preranked GSEA | User-provided GMT only | User responsible for source and usage rights |

## Backend / Runtime Status

Current local detector result on 2026-05-28:

- Rscript: passed, `/usr/local/bin/Rscript`, R 4.4.2, arm64.
- `clusterProfiler`: available, 4.14.6.
- `fgsea`: available, 1.32.4.
- `ReactomePA`: available, 1.50.0.
- `msigdbr`: available, 26.1.0.
- `pathview`: missing, but not required for current controlled ORA/preranked GSEA gates.

The runtime policy remains detect-first:

- no R package auto-install;
- no Bioconductor or MSigDB download from UI;
- no bundling of R/Bioconductor packages into the app;
- missing selected backend capability produces blockers instead of traceback.

## Cross-Project Acceptance

B97 acceptance gate status: passed.

Acceptance scenarios: 12/12 passed.

Covered scenarios:

- GO BP ORA positive;
- KEGG Entrez ORA positive;
- Reactome ORA positive;
- MSigDB Hallmark preranked GSEA positive;
- Custom GMT ORA positive;
- identifier mismatch negative;
- missing background negative;
- missing backend negative;
- preflight source negative;
- imported source negative;
- ORA result schema positive;
- GSEA result schema positive.

## UI Disabled Reason Checks

B98 Analysis Center now exposes production preview rows for:

- enrichment resource lock;
- enrichment library capability;
- enrichment background universe;
- enrichment identifier compatibility;
- enrichment statistical policy;
- enrichment result schema;
- enrichment production audit package;
- enrichment cross-library acceptance.

The new `enrichment_production_audit_preview` action is review-only:

- `button_behavior=enabled_review_only_no_package_write` when ready;
- `blocked_enrichment_production_gate` with explicit blockers when not ready;
- no package write during UI state build;
- no report-ready upgrade.

Formal full GSEA remains disabled. Controlled ORA/GSEA actions remain separately gated by source result, resource, backend, parameter confirmation, and result schema.

## Package / Open-W / Codesign Status

Validated on the B98/B99 candidate line before this audit commit:

- `python3 -m pytest tests/bioinformatics -q`: 536 passed, 1 scipy precision warning in a legacy GEO DEG test.
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q`: 177 passed.
- `python3 -m app.main --smoke-test`: passed.
- `python3 scripts/package_app.py --smoke-test`: passed.
- `open -W -n dist/BioMedPilot.app --args --smoke-test`: passed.
- `codesign --verify --deep --strict --verbose=2 dist/BioMedPilot.app`: passed.

B99 is documentation-only. No source runtime or package behavior is changed by this audit document.

## Blocker / Major / Minor

Blockers:

- None for internal controlled ORA/preranked GSEA production-readiness candidate status.

Major:

- This is not public-release-ready enrichment. Resource licensing, user-provided MSigDB usage, and project-specific biological review remain outside the automated gate.
- `pathview` is not installed. This does not block current controlled ORA/preranked GSEA, but it blocks any future pathview-specific pathway diagram feature until explicitly gated.

Minor:

- The B98 UI preview is readiness/review only; actual audit package export remains a separate explicit operation.
- Cross-library acceptance uses controlled fixtures and contract checks, not broad public database certification.

## ReleaseBuild Receive Recommendation

Recommendation: proceed to scoped ReleaseBuild receive after this B99 audit commit.

Carry-over should include only the B92-B99 enrichment production hardening surface and preserve existing ReleaseBuild entrypoint, packaging, and release notes policy. ReleaseBuild should rerun:

```bash
git diff --check
python3 -m pytest tests/bioinformatics -q -k "enrichment or gsea or gene_set or analysis_ui"
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q -k "analysis_task or enrichment or gsea"
python3 -m pytest tests/bioinformatics -q
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q
python3 -m app.main --smoke-test
python3 scripts/package_app.py --smoke-test
open -W -n dist/BioMedPilot.app --args --smoke-test
codesign --verify --deep --strict --verbose=2 dist/BioMedPilot.app
```

## Final Conclusion

Conclusion label: `production-readiness_candidate_internal`.

The enrichment layer can be treated as an internal controlled ORA / controlled preranked GSEA production-readiness candidate. It must not be described as clinical-grade, public-release-ready, or a full automatic biological interpretation engine.
