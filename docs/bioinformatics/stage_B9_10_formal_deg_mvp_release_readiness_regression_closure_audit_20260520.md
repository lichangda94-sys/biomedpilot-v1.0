# Bioinformatics B9.10 Formal DEG MVP Release-Readiness / Regression Closure Audit

Date: 2026-05-20

## Scope

This audit closes the B9 formal DEG MVP line and checks whether the current implementation is ready for MainLine carry-over / ReleaseBuild carry-over.

This is a release-readiness and regression closure audit. It does not add new analysis capability.

## Current Commit Range

Audited B9 capability commits:

| Stage | Commit | Capability |
| --- | --- | --- |
| B9.1 | `a6aa926` / `d7e8fb8` | Formal DEG dependency policy, parameter gate, result schema gate, UI execution controls |
| B9.2 | `bab8355` | Audited two-group controlled formal DEG MVP |
| B9.3 | `86195e1` | Runtime dependency packaging validation |
| B9.3b | `9760831` | Controlled scipy/statsmodels runtime validation |
| B9.4 | `0073ba3` | User parameter confirmation flow |
| B9.5 | `e983ba6` | Formal DEG result review and interpretation guard |
| B9.6 | `17786b5` | Formal DEG plot artifact activation |
| B9.7 | `ce8c2c1` | Formal DEG report-ready gate |
| B9.8 | `7a53f9b` | Report-ready package UX / review audit hardening |
| B9.9 | `a7c8d73` | Formal DEG end-to-end user acceptance audit |

## B9.1-B9.9 Current Capability Summary

| Area | Status | Evidence |
| --- | --- | --- |
| Dependency policy | Passed | numpy/pandas/scipy/statsmodels are detected first; missing scipy/statsmodels blocks formal DEG; no auto-install action |
| Parameter gate | Passed | comparison, groups, samples, method, thresholds, value type policy, pseudocount, FDR policy, dependency snapshot required before formal DEG |
| Result schema gate | Passed | formal DEG result must register result index v2 with input package, task run, parameters, dependency, output artifacts, validation, warnings/blockers |
| Controlled formal DEG execution | Passed | two-group controlled DEG generates numeric `p_value` and `adjusted_p_value`; no fake fallback statistics |
| User confirmation | Passed | confirmation manifest includes output plan and dependency snapshot; formal run is blocked without matching confirmation |
| Result review | Passed | review table is limited to `formal_computed_result` DEG; imported/testing/exploratory/preflight are excluded |
| Plot artifact | Passed | formal DEG plot artifact can only come from formal DEG result source and inherits result semantics |
| Report-ready gate | Passed | package requires formal DEG result index, confirmation, dependency, table validation, plot artifact or explicit table-only mode |
| Package UX | Passed | package includes stable directories, inventory, gate snapshot, provenance, warnings, limitations, output path, and non-overwrite policy |
| E2E acceptance audit | Passed | confirmation -> run -> review -> plot -> report-ready -> package path is covered by a read-only audit helper |

## Formal DEG MVP Supported Scope

Supported:

- two-group controlled DEG only
- Python backend using scipy/statsmodels for controlled Welch t-test or Mann-Whitney path
- standardized repository / analysis input resolver source only
- user-confirmed comparison and parameters
- formal result index v2 registration
- formal DEG result review
- formal DEG plot artifact metadata/spec registration
- formal DEG report-ready package for formal DEG section only
- explicit no-plot table-only report mode

## Explicitly Unsupported Scope

Not supported in this MVP:

- formal GSEA
- survival analysis
- KM plot, Cox model, log-rank p-value, hazard ratio
- clinical association statistics
- clinical conclusions or treatment recommendations
- DESeq2
- edgeR
- limma
- R backend execution
- multi-factor design
- batch-corrected complex design
- imported/testing/exploratory/preflight outputs upgraded into formal results

## Runtime And Packaging Acceptance

| Check | Result |
| --- | --- |
| `git diff --check` | Passed |
| Focused formal DEG/UI regression | `29 passed, 348 deselected` |
| Results browser / analysis task / report UI regression | `13 passed, 96 deselected` |
| Full bioinformatics tests | `377 passed` |
| Full UI tests | `176 passed` |
| Source smoke | Passed, `git_head=a7c8d73` |
| Controlled runtime check | Passed, arm64, `formal_computed_result`, numeric p-value/FDR present |
| Controlled runtime boundary | `plot_artifacts=[]`, `report_artifacts=[]`, `report_ready_eligible=False` during formal DEG run itself |
| Package smoke | Passed, packaged-local-python launcher, `git_head=a7c8d73` |
| `open -W -n dist/BioMedPilot.app --args --smoke-test` | Passed |
| `codesign --verify --deep --strict --verbose=2 dist/BioMedPilot.app` | Passed |

Controlled runtime dependency versions observed:

- numpy `2.4.6`
- pandas `3.0.3`
- scipy `1.17.1`
- statsmodels `0.14.6`
- architecture `arm64`

## Contract Acceptance

| Contract | Status | Notes |
| --- | --- | --- |
| Resolver source boundary | Passed | Formal DEG still flows from standardized repository / registry / analysis input resolver contracts |
| Formal DEG execution gate | Passed | UI formal DEG action depends on resolver, DEG-ready, dependency, parameter, confirmation, result schema gates |
| Result index v2 | Passed | Formal DEG entries include semantics, input package, parameters, dependency, artifacts, validation, logs |
| Plot artifact | Passed | Formal plot artifacts inherit formal DEG semantics and are registered under result index `plot_artifacts` |
| Report-ready package | Passed | Package includes report markdown, DEG table, plot artifact manifest, confirmation, dependency, result index snapshot, logs, warnings, limitations, provenance |
| E2E audit | Passed | Read-only audit validates traceability and failure blockers |

## UI Acceptance

| UI Concern | Status |
| --- | --- |
| User can understand each step state | Passed |
| Formal DEG button enabled/disabled reason clear | Passed |
| Parameter confirmation traces to result/report | Passed |
| Review table is distinct from report-ready export | Passed |
| Plot artifact generation is source-result driven | Passed |
| Table-only report mode wording is explicit | Passed |
| Export path is visible | Passed |
| Export path is stable and non-overwriting | Passed |
| Failure messages expose blockers | Passed |
| UI does not imply GSEA/survival/clinical conclusions are available | Passed |

## Untracked File Audit

Untracked files observed and intentionally excluded from B9.10 commit:

- `docs/bioinformatics/Bioinformatics_handoff_report_20260513.md`
- `project_storage/bioinformatics/`

These are not part of the formal DEG MVP release-readiness audit and must not be staged for this commit.

## Blockers / Major / Minor

Blockers:

- None found.

Major:

- None found.

Minor:

- Package is still local-python launcher based, not a standalone frozen runtime. This is accepted for the current BioMedPilot packaging mode but should be called out during ReleaseBuild planning.
- Formal DEG MVP excludes R-based methods and multi-factor design by policy; UI/report copy must continue to state this boundary.

## Release-Readiness Conclusion

Final conclusion: **small-issue pass**.

The B9 formal DEG MVP is ready for carry-over as a bounded feature, provided the release notes preserve the exact MVP scope:

- formal DEG = two-group controlled DEG only
- scipy/statsmodels dependency required
- report-ready = formal DEG section only
- no GSEA / survival / clinical statistics / DESeq2 / edgeR / limma / multi-factor design

## Carry-Over Recommendation

MainLine carry-over: **Recommended with scope lock**.

ReleaseBuild carry-over: **Recommended as a controlled MVP**, with these release conditions:

- keep LaunchServices `open -W` and codesign checks in the release gate
- keep controlled runtime dependency validation in the release gate
- keep B9.9 E2E acceptance audit in regression suite
- do not market or label this as broad DEG, GSEA, survival, or clinical analysis
- keep unrelated `project_storage/` and handoff documents out of release commits

Next suggested stage: MainLine carry-over / ReleaseBuild carry-over planning for the bounded Formal DEG MVP.
