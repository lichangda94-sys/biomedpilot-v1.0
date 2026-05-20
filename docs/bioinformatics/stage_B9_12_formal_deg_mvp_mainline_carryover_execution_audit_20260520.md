# B9.12 Formal DEG MVP MainLine Carry-Over Execution Audit

Date: 2026-05-20

Source worktree: `/Users/changdali/Developer/biomedpilot v1.0/Bioinformatics`

Source branch / HEAD: `dev/bioinformatics` / `4d00514`

Target worktree: `/Users/changdali/Developer/biomedpilot v1.0/MainLine`

Target branch / HEAD: `stable/mainline` / `21e1a0f`

## 1. Scope

This stage attempted the B9.11-defined MainLine carry-over for the bounded Formal DEG MVP.

Goal:

- Carry over the B8/B9 Formal DEG MVP into MainLine without weakening B8/B9 gates.
- Preserve MainLine-owned UI, launcher, packaging, and project governance changes.
- Validate MainLine with Bioinformatics tests and focused UI tests.

Non-goals:

- No ReleaseBuild packaging carry-over.
- No GSEA activation.
- No survival/KM/Cox/log-rank/HR activation.
- No clinical conclusions or treatment recommendations.
- No DESeq2/edgeR/limma/R backend/multi-factor design activation.
- No imported/testing/exploratory/preflight upgrade into `formal_computed_result`.

## 2. Pre-Intake State

Bioinformatics source worktree:

- branch: `dev/bioinformatics`
- HEAD: `4d00514 docs(bio): add formal DEG carry-over planning`
- known unrelated untracked items:
  - `docs/bioinformatics/Bioinformatics_handoff_report_20260513.md`
  - `project_storage/bioinformatics/`

MainLine target worktree:

- branch: `stable/mainline`
- HEAD before attempt: `21e1a0f docs(mainline): carry B5.15 integration handoff audit`
- worktree status before attempt: clean
- worktree status after abort: clean

## 3. Divergence Audit

Merge-base:

```text
59369dedc2066acb8e2f827a7b606ec015ab630c
```

Branch divergence:

```text
stable/mainline...dev/bioinformatics = 91 / 67
```

Bioinformatics source adds or modifies a broad module surface:

- `app/bioinformatics/`
- `tests/bioinformatics/`
- `tests/ui/test_bioinformatics_workflow_pages.py`
- `config/bioinformatics/package_requirements.yaml`
- `docs/bioinformatics/`
- `app/main.py`
- `pyproject.toml`
- `requirements.txt`

MainLine also has Bioinformatics-related changes after the merge-base, including:

- recognition detail and next-step guidance
- standardized asset selection
- group comparison design
- analysis task run records
- result/report manifest linking
- shared UI style convergence for Bioinformatics pages
- desktop launcher and packaging governance changes

## 4. Merge Attempt

Command attempted in MainLine:

```bash
git merge --no-commit --no-ff dev/bioinformatics
```

Initial conflict list:

- `CODEX.md`
- `app/bioinformatics/analysis_task_runs.py`
- `app/bioinformatics/deg_task_plan.py`
- `app/bioinformatics/project_readiness.py`
- `app/bioinformatics/project_recognition.py`
- `app/bioinformatics/project_standardization.py`
- `app/bioinformatics/reports/project_report_builder.py`
- `app/bioinformatics/results/project_results.py`
- `app/bioinformatics/workflow_pages.py`
- `app/bioinformatics/workspace.py`
- `app/main.py`
- `docs/architecture.md`
- `scripts/package_app.py`
- `tests/bioinformatics/test_deg_task_plan.py`
- `tests/bioinformatics/test_workflow_adapters.py`
- `tests/test_package_app.py`
- `tests/ui/test_bioinformatics_workflow_pages.py`

Conflict strategy attempted:

- Keep MainLine for global governance and packaging files:
  - `CODEX.md`
  - `docs/architecture.md`
  - `scripts/package_app.py`
  - `tests/test_package_app.py`
- Merge `app/main.py` to preserve MainLine `-psn_*` filtering and add B9 formal DEG runtime-check flags.
- Prefer B9 branch for Formal DEG contract/UI/runtime files.
- Add compatibility shims for MainLine task-run and imported DEG result browser APIs where feasible.

## 5. Validation Attempt Results

Whitespace / conflict markers:

```bash
git diff --check
rg -n "<<<<<<<|=======|>>>>>>>" .
```

Result:

- whitespace check passed
- no conflict markers after manual resolution

Focused Formal DEG / Analysis UI regression:

```bash
python3 -m pytest tests/bioinformatics -q -k "formal_deg_e2e or formal_deg_report or formal_deg_plot or formal_controlled_deg or parameter_confirmation or analysis_ui"
```

Result after compatibility fixes:

```text
29 passed, 385 deselected
```

Focused UI regression:

```bash
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q -k "analysis_task or deg_config or results_browser or report or settings"
```

Result:

```text
16 passed, 93 deselected
```

Full Bioinformatics regression:

```bash
python3 -m pytest tests/bioinformatics -q
```

Result:

```text
24 failed, 390 passed
```

After trying the opposite recognition/standardization resolution, result:

```text
17 failed, 397 passed
```

## 6. Blocker Analysis

Blocker: **MainLine recognition / standardization contracts and B9 recognition / standardization contracts have diverged and cannot be safely reconciled by a small carry-over fix.**

Observed split:

- MainLine has integrated RNA-seq table recognition, standardized asset selection, group comparison design, and result/report manifest expectations.
- B9 branch has newer B6-B9 GEO/TCGA/GTEx, analysis input resolver, DEG-ready, result semantics, and formal DEG gate expectations.
- Choosing the B9 branch versions breaks MainLine integrated table / asset selection / group comparison / legacy imported DEG browser regressions.
- Choosing the MainLine versions breaks B6-B9 recognition fields and standardization outputs required by the B8/B9 contract line.

Examples of MainLine regressions when B9 recognition/standardization is preferred:

- integrated RNA-seq result table lacks `semantic_type=rna_seq_integrated_result_table`
- count matrix assets are not emitted as `count_matrix`
- imported DEG tables are not recognized as `differential_result_table`
- gene annotation and sample metadata classifications regress
- standardized asset selection lacks count/normalized/DEG/gene annotation groups
- group comparison design cannot see count matrix sample IDs
- analysis task-run dry-run creation cannot find default count matrix

Examples of B9 regressions when MainLine recognition/standardization is preferred:

- B6-B9 GEO SOFT / Series Matrix fields are missing
- TCGA expression and clinical metadata recognition falls back to generic types
- GTEx expression and sample metadata recognition falls back to generic types
- standardization confirmation candidates for GEO/B6-B9 are incomplete
- B8/B9 stale report and resolver-adjacent fields are incomplete

This is not a single-file conflict. It is a contract convergence problem across:

- `project_recognition.py`
- `project_standardization.py`
- `standardized_asset_selection.py`
- `group_comparison_design.py`
- `project_readiness.py`
- `analysis_inputs/*`
- `workflow_pages.py`
- result/report manifest helpers

## 7. MainLine Preservation

Because the attempted carry-over failed full Bioinformatics regression, the merge was aborted:

```bash
git merge --abort
```

Post-abort MainLine state:

- branch: `stable/mainline`
- HEAD: `21e1a0f`
- worktree: clean
- no B9.12 carry-over commit was created in MainLine

## 8. Formal DEG Boundary Check

The failed carry-over attempt did not activate any unsupported analysis capability.

Still preserved in the source branch:

- formal DEG remains two-group controlled DEG only
- no formal GSEA
- no survival statistics
- no KM/Cox/log-rank/HR
- no clinical conclusions
- no DESeq2/edgeR/limma/R backend
- no multi-factor design
- formal plot/report actions remain gate-controlled
- imported/testing/exploratory/preflight results do not become `formal_computed_result`

No unsupported capability was committed to MainLine.

## 9. Blocker / Major / Minor

Blockers:

- Recognition / standardization contract divergence blocks safe MainLine carry-over.
- Full Bioinformatics regression does not pass under either straightforward conflict strategy.

Major:

- `workflow_pages.py` conflicts with MainLine shared UI convergence and B9 Analysis Center rebuild.
- `app/main.py` needs a careful merge to preserve both LaunchServices `-psn_*` filtering and formal DEG runtime-check CLI.
- `results/project_results.py` needs a no-side-effect load path while retaining MainLine imported DEG browser compatibility.

Minor:

- B9 docs can be carried over cleanly, but docs alone are not sufficient for MainLine acceptance.
- `pyproject.toml` and `requirements.txt` dependency deltas should be reviewed only after recognition/standardization convergence passes source tests.

## 10. Final Conclusion

Final conclusion: **not passed**.

B9.12 should not create a MainLine carry-over commit yet.

The Formal DEG MVP remains release-ready inside the Bioinformatics worktree, but MainLine intake is blocked until the recognition / standardization contract convergence is done explicitly and tested.

## 11. Recommendation

Do not proceed directly to ReleaseBuild carry-over.

Recommended next stage: **B9.12a MainLine Recognition / Standardization Contract Convergence**.

Suggested B9.12a scope:

1. Merge MainLine integrated RNA-seq recognition expectations with B6-B9 GEO/TCGA/GTEx recognition expectations.
2. Preserve B8 resolver-compatible standardized repository and analysis input package outputs.
3. Preserve MainLine standardized asset selection and group comparison design behavior.
4. Keep `load_result_index()` side-effect free for Analysis Center state builder.
5. Keep imported DEG browser compatibility without upgrading imported results to formal DEG.
6. Run:
   - `python3 -m pytest tests/bioinformatics/test_recognition_compatibility_matrix.py -q`
   - `python3 -m pytest tests/bioinformatics/test_standardized_asset_registry.py tests/bioinformatics/test_standardized_asset_selection.py -q`
   - `python3 -m pytest tests/bioinformatics/test_group_comparison_design.py tests/bioinformatics/test_analysis_task_runs.py tests/bioinformatics/test_result_report_manifest.py -q`
   - `python3 -m pytest tests/bioinformatics -q -k "analysis_input or resolver or deg_ready or formal_deg or analysis_ui"`
7. Only after B9.12a passes, retry B9.12 MainLine carry-over.
