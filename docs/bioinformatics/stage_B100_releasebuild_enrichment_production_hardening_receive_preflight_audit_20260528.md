# B100 ReleaseBuild Enrichment Production Hardening Receive Preflight Audit

## Scope

This audit checks whether ReleaseBuild can receive the Bioinformatics B92-B99 enrichment production hardening track after Bioinformatics commit `8365ef4`.

This stage does not publish ReleaseBuild, does not overwrite the desktop entrypoint, and does not directly copy the Bioinformatics source tree into ReleaseBuild.

## Current ReleaseBuild State

- Worktree: `/Users/changdali/Developer/biomedpilot v1.0/ReleaseBuild`
- Branch: `dev/release-internal-test`
- Starting HEAD: `e02d58e`
- Existing uncommitted changes were present before this audit:
  - `app/bioinformatics/analysis_ui/state.py`
  - `app/bioinformatics/deg_engine/__init__.py`
  - `tests/bioinformatics/test_analysis_ui_state.py`
  - `app/bioinformatics/deg_engine/input_adaptation.py`
  - `tests/bioinformatics/test_deg_input_adaptation_gate.py`
- Existing untracked files were preserved:
  - `docs/release/ReleaseBuild_handoff_report_20260513.md`
  - `project_storage/external_engines/`

The dirty DEG input-adaptation files overlap `analysis_ui/state.py`, so ReleaseBuild should not receive B98 UI changes by whole-file replacement or broad cherry-pick.

## Bioinformatics Baseline

- Bioinformatics source worktree: `/Users/changdali/Developer/biomedpilot v1.0/Bioinformatics`
- Baseline commit: `8365ef4`
- B92-B99 conclusion: `production-readiness_candidate_internal`
- Scope: controlled ORA and controlled preranked GSEA internal candidate only.

## Difference Summary

Bioinformatics B92-B99 added standalone modules:

- `app/bioinformatics/enrichment_backend.py`
- `app/bioinformatics/enrichment_resources.py`
- `app/bioinformatics/enrichment_input_contract.py`
- `app/bioinformatics/enrichment_result_schema.py`
- `app/bioinformatics/enrichment_audit_package.py`
- `app/bioinformatics/enrichment_acceptance.py`
- `app/bioinformatics/enrichment_execution_gate.py`
- `app/bioinformatics/enrichment_r_adapter.py`
- `app/bioinformatics/enrichment_plot_report.py`
- `app/bioinformatics/enrichment_result_review.py`

ReleaseBuild currently has a different enrichment architecture:

- `app/bioinformatics/enrichment/` package for ORA;
- `app/bioinformatics/gsea/` package for preranked GSEA;
- existing ORA/GSEA plot, report-ready, and full-integrated report wiring;
- external R enrichment backend detection in `app/shared/local_engines/external_dependency_registry.py`;
- ORA/GSEA UI action rows already use ReleaseBuild-specific action ids and result schemas.

Directly copying B92-B99 source files would introduce a second enrichment contract stack with different result table schemas. That is not a safe ReleaseBuild receive strategy.

## Runtime / External Engine Status

Current ReleaseBuild external enrichment detector result:

- Rscript: passed, `/usr/local/bin/Rscript`, R 4.4.2, arm64.
- `clusterProfiler`: passed, 4.14.6.
- `fgsea`: passed, 1.32.4.
- `DOSE`: passed, 4.0.1.
- `enrichplot`: passed, 1.26.6.
- `ggplot2`: passed, 3.5.2.
- `AnnotationDbi`: passed, 1.68.0.
- `org.Hs.eg.db`: passed, 3.20.0.
- `ReactomePA`: passed, 1.50.0.
- `msigdbr`: passed, 26.1.0.

The external validation fixture also passed:

- ORA fixture columns: passed.
- GSEA fixture columns: passed.
- No enrichment backend blockers.

The policy remains detect-first:

- no R package auto-install;
- no Bioconductor or MSigDB download from BioMedPilot;
- no bundling external R packages into the app.

## Safe Receive Surface

Can be received after scoped convergence:

- resource lock/version policy, but implemented on top of ReleaseBuild `gene_set_resources.py` and `enrichment/gene_set_gate.py`;
- background universe and identifier compatibility, but adapted to ReleaseBuild ORA/GSEA result schemas;
- statistical policy and result schema hardening, but preserving ReleaseBuild table formats and existing report package contracts;
- production audit package, but generated from ReleaseBuild ORA/GSEA result index and task-log paths;
- Analysis Center production preview, but merged into ReleaseBuild `action_rules.py` and `state.py` without overwriting the existing DEG input-adaptation dirty work or full integrated report gates.

Should not be received by direct copy:

- Bioinformatics `analysis_ui/state.py` or `action_rules.py`;
- Bioinformatics standalone enrichment result schema without a ReleaseBuild schema adapter;
- any source tree replacement under `app/bioinformatics/`;
- any generated `project_storage` outputs.

## Blocker / Major / Minor

Blockers:

- Direct carry-over is blocked by architecture divergence and dirty overlapping UI files.

Major:

- ReleaseBuild ORA/GSEA schema differs from Bioinformatics B92-B99 R-style schema. A schema convergence adapter is required before result schema/audit package gates can be accepted.
- Existing dirty DEG input-adaptation changes in `analysis_ui/state.py` must be preserved and either committed separately or carefully partial-staged during future scoped receive.

Minor:

- `gene_set_resources.py` lacks the B93 resource `file_size` and `checksum` registry fields and should be patched in scoped convergence.
- The existing external R enrichment detector is already stronger than Bioinformatics B92 detector in this worktree, but it is not yet connected to ReleaseBuild ORA/GSEA UI production preview.

## Test Evidence

Preflight tests on the current ReleaseBuild worktree:

```bash
git diff --check
python3 -m pytest tests/bioinformatics -q -k "enrichment or gsea or gene_set or analysis_ui"
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q -k "analysis_task or enrichment or gsea"
```

Results:

- `git diff --check`: passed.
- focused bioinformatics: 113 passed, 658 deselected.
- focused UI workflow: 9 passed, 111 deselected.
- `python3 -m app.main --smoke-test`: passed, `git_head=e02d58e`.
- `python3 scripts/package_app.py --smoke-test`: passed, `git_head=e02d58e`.
- `open -W -n dist/BioMedPilot.app --args --smoke-test`: passed.
- `codesign --verify --deep --strict --verbose=2 dist/BioMedPilot.app`: passed.

## Recommendation

Recommendation: do not direct-copy B92-B99 into ReleaseBuild.

Proceed with a scoped convergence stage:

1. Preserve current ReleaseBuild dirty DEG input-adaptation work.
2. Patch `gene_set_resources.py` for resource checksum/file size.
3. Add ReleaseBuild-native enrichment resource lock / background / identifier / statistical policy gates.
4. Adapt result schema gates to ReleaseBuild ORA/GSEA table formats.
5. Add production audit package from ReleaseBuild result index paths.
6. Add Analysis Center production preview rows and disabled reasons using existing ReleaseBuild action ids.
7. Re-run full bioinformatics/UI/source/package/open-W/codesign gates.

## Conclusion

Conclusion label: `conditional_internal_candidate`.

ReleaseBuild is ready for scoped enrichment production-hardening convergence, but not ready for direct B92-B99 carry-over by source tree replacement or broad cherry-pick.
