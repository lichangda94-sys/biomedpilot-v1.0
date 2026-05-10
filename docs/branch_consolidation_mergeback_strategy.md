# Branch Consolidation Mergeback Strategy

Date: 2026-05-10

Scope: read-only strategy audit for merging long-lived development branches back to `stable/mainline`. No merge, cherry-pick, rebase, reset, branch deletion, or push was performed during this audit.

## 1. Current Heads

| Branch | HEAD | Latest commit |
| --- | --- | --- |
| `stable/mainline` | `36cbb66` | `docs(repo): add branch consolidation plan` |
| `dev/shared-vocabulary` | `be6a461` | `docs(repo): record shared vocabulary branch consolidation` |
| `dev/meta-analysis` | `e7360f5` | `docs(repo): finalize meta branch consolidation review` |
| `dev/bioinformatics` | `59369de` | `docs(repo): audit bioinformatics safe stage2 branch gaps` |

All three dev branches have `36cbb66` as their merge base with `stable/mainline`.

## 2. Branch Differences

### `dev/shared-vocabulary`

Ahead / behind:

```text
stable/mainline...dev/shared-vocabulary = 0 2
```

Branch-only commits:

```text
be6a461 docs(repo): record shared vocabulary branch consolidation
14d7f5a docs(shared): isolate medical vocabulary worktree
```

Changed files:

```text
M docs/branch_consolidation_plan.md
A docs/stage_v1_medical_vocabulary_worktree_isolation.md
```

Risk assessment:

- Only documentation changes.
- No `app/`, `tests/`, `app/shared/`, `app/meta_analysis/`, `app/bioinformatics/`, `app/main.py`, `app/shell/`, or packaging script changes.
- Low functional risk.
- Main merge risk: `docs/branch_consolidation_plan.md` conflicts with other dev branch consolidation logs.
- Recommended merge style: normal merge is acceptable; fast-forward is also possible if it is merged first. Squash is not necessary.
- Recommendation: merge back to `stable/mainline`.

### `dev/meta-analysis`

Ahead / behind:

```text
stable/mainline...dev/meta-analysis = 0 4
```

Branch-only commits:

```text
e7360f5 docs(repo): finalize meta branch consolidation review
e9e6d00 docs(repo): record meta search branch consolidation
4db1286 docs(repo): record meta workflow branch consolidation
df411c3 feat(meta): connect workflow ui later stages
```

Changed files:

```text
M app/meta_analysis/workspace.py
M docs/branch_consolidation_plan.md
A docs/meta_ui_06_18_implementation_plan.md
M tests/meta_analysis/test_meta_workspace_ui_navigation.py
```

Risk assessment:

- Contains a real Meta Analysis app change in `app/meta_analysis/workspace.py`.
- Contains Meta tests and Meta docs.
- No Bioinformatics, shared AI/query intelligence, medical vocabulary, app shell, main app, or packaging script changes.
- Low-to-medium functional risk because it modifies Meta workspace UI routing.
- Main merge risk: `docs/branch_consolidation_plan.md` conflicts with shared and bio consolidation logs.
- Recommended merge style: normal merge to preserve the feature commit and audit commits.
- Recommendation: merge back to `stable/mainline` after `dev/shared-vocabulary`.

### `dev/bioinformatics`

Ahead / behind:

```text
stable/mainline...dev/bioinformatics = 0 3
```

Branch-only commits:

```text
59369de docs(repo): audit bioinformatics safe stage2 branch gaps
1e02b15 docs(repo): audit bio search ui branch gaps
68210af docs(repo): record bio geo download branch consolidation
```

Changed files:

```text
A docs/bio_search_ui_main_gap_audit.md
A docs/bioinformatics_safe_stage2_gap_audit.md
M docs/branch_consolidation_plan.md
```

Risk assessment:

- Only documentation changes.
- No Bioinformatics app code changes are currently unique to this dev branch.
- No `app/shared/`, `app/meta_analysis/`, `app/bioinformatics/`, `app/main.py`, `app/shell/`, tests, or packaging script changes.
- Low functional risk.
- Main merge risk: `docs/branch_consolidation_plan.md` conflicts with shared and meta consolidation logs.
- Recommended merge style: normal merge is acceptable. Squash is not necessary.
- Recommendation: merge back to `stable/mainline` after Meta.

## 3. Conflict Preview

Read-only `git merge-tree` checks show text conflicts between every pair of dev branches in:

```text
docs/branch_consolidation_plan.md
```

The conflict is expected because each dev branch appended a separate `## 8. Consolidation Log` section from the same `stable/mainline` base:

- `dev/shared-vocabulary`: `Shared Vocabulary Round 1`
- `dev/meta-analysis`: `Meta Analysis Round 1`, `Meta Analysis Round 2`, `Meta Analysis Final Review`
- `dev/bioinformatics`: `Bioinformatics Round 1`, `Bioinformatics Round 2`, `Bioinformatics Round 3`

Conflict resolution principle:

- Keep exactly one `## 8. Consolidation Log` heading.
- Append all three branch logs under that heading.
- Recommended order inside the section:
  1. `Shared Vocabulary Round 1`
  2. `Meta Analysis Round 1`
  3. `Meta Analysis Round 2`
  4. `Meta Analysis Final Review`
  5. `Bioinformatics Round 1`
  6. `Bioinformatics Round 2`
  7. `Bioinformatics Round 3`
- Do not drop any branch-specific audit details.
- Do not resolve by taking only `ours` or only `theirs`.

No predicted cross-branch conflict was found in application code because only `dev/meta-analysis` has app/test changes.

## 4. Recommended Mergeback Order

Recommended order:

1. Merge `dev/shared-vocabulary` into `stable/mainline`.
2. Merge `dev/meta-analysis` into `stable/mainline`.
3. Merge `dev/bioinformatics` into `stable/mainline`.

Reasoning:

- `dev/shared-vocabulary` is documentation-only and has the smallest diff.
- `dev/meta-analysis` is the only branch with app/test changes; merging it before Bio keeps any functional validation focused.
- `dev/bioinformatics` is documentation-only and can be merged last after its audit reports are added.

Alternative:

- If the goal is a very compact stable history, the two documentation-only branches can be squash-merged, but normal merge is still preferred because these are long-lived branch consolidation records.
- Avoid cherry-picking individual docs unless a merge conflict becomes unexpectedly hard to resolve.

## 5. Validation Plan

After merging `dev/shared-vocabulary`:

```bash
python3 -m pytest tests/shared -q
python3 -m compileall -q app tests scripts
QT_QPA_PLATFORM=offscreen python3 -m app.main --smoke-test
```

After merging `dev/meta-analysis`:

```bash
python3 -m pytest tests/meta_analysis -q
python3 -m pytest tests/ui/test_meta_analysis_workflow_pages.py -q
python3 -m compileall -q app tests scripts
QT_QPA_PLATFORM=offscreen python3 -m app.main --smoke-test
```

After merging `dev/bioinformatics`:

```bash
python3 -m pytest tests/bioinformatics -q
python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q
python3 -m compileall -q app tests scripts
QT_QPA_PLATFORM=offscreen python3 -m app.main --smoke-test
```

Final `stable/mainline` validation:

```bash
python3 scripts/run_tests.py
QT_QPA_PLATFORM=offscreen python3 -m app.main --smoke-test
```

If a desktop app build is needed:

```bash
python3 scripts/package_app.py --output-dir /Users/changdali/Desktop --app-name BioMedPilot --smoke-test
```

## 6. Merge Conflict Handling Rules

- Stop on conflicts and inspect `git status --short`.
- Resolve only documented conflicts.
- For `docs/branch_consolidation_plan.md`, manually combine all consolidation log sections in chronological/module order.
- Do not modify business code while resolving documentation conflicts.
- If any unexpected conflict appears in `app/`, `tests/`, `scripts/`, or packaging files, stop and reassess before editing.
- After each merge and conflict resolution, run the branch-specific validation commands before moving to the next branch.

## 7. Desktop App Packaging Recommendation

After all three branches are merged and final validation passes, rebuild `/Users/changdali/Desktop/BioMedPilot.app` from `stable/mainline`.

Packaging is recommended because:

- `dev/meta-analysis` changes the Meta workspace routing.
- `stable/mainline` should become the confirmed desktop app packaging source.
- The old desktop app was previously tied to earlier branch state and should be refreshed after consolidation.

## 8. Old Branch Archive Recommendation

Do not delete old branches in this phase.

After mergeback and desktop package validation, create a separate archive document listing old branches by status:

- Archive candidates:
  - `codex/vocab-line-stabilization`
  - `codex/meta-workflow-ui`
  - `codex/meta-search-ui-main`
  - `codex/bio-geo-real-download-test`
  - `codex/bio-search-ui-main`
  - `codex/bioinformatics-safe-stage2`
- High-risk/manual-only:
  - `codex/ai-gateway-call-isolation-audit`
- Likely already merged or superseded:
  - branches already identified in `docs/branch_consolidation_plan.md`

Branches attached to worktrees must not be deleted directly. Audit and remove their worktrees intentionally first, then archive or delete branches in a separate maintenance task.

## 9. Overall Recommendation

Merge all three long-lived dev branches back to `stable/mainline` in this order:

```text
dev/shared-vocabulary -> dev/meta-analysis -> dev/bioinformatics
```

Expected risk:

- Functional risk: low to medium, driven only by the Meta workspace UI change.
- Conflict risk: medium, limited to `docs/branch_consolidation_plan.md`.
- Packaging risk: low, but final desktop rebuild should be done after validation.
