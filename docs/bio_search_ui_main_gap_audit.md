# Bio Search UI Main Gap Audit

Date: 2026-05-10

Scope: read-only audit of `codex/bio-search-ui-main` against `dev/bioinformatics`. No code was merged, cherry-picked, copied, or edited during this review.

## 1. Branch Information

| Field | Value |
| --- | --- |
| Base branch | `dev/bioinformatics` |
| Reviewed branch | `codex/bio-search-ui-main` |
| Base HEAD at review | `68210af docs(repo): record bio geo download branch consolidation` |
| Ahead / behind | `73 30` for `git rev-list --left-right --count dev/bioinformatics...codex/bio-search-ui-main` |
| Branch-only commit count | 30 |
| Overall risk | High for direct merge; acceptable as historical reference |

Interpretation: `dev/bioinformatics` has 73 commits not present in `codex/bio-search-ui-main`, while the reviewed branch has 30 branch-only commits. The reviewed branch is an older large UI/search line and should not be merged as a whole.

## 2. Branch-Only Commits

| Commit | Message | Initial classification |
| --- | --- | --- |
| `26a33be` | `fix(bio): simplify GEO Chinese summary panel` | AI summary / UI / obsolete |
| `083a543` | `fix(bio): harden GEO group recognition audit` | recognition / tests / covered |
| `92b5296` | `fix(bio): enable safe deletion of historical GEO cache` | UI / cache / covered |
| `c9c4db2` | `test(bio): add controlled GEO recognition audit` | tests / audit / covered |
| `cbfbd79` | `feat(bio): confirm GEO comparison groups` | recognition / comparison / covered |
| `1a7c197` | `feat(bio): refine GEO metadata profile evidence` | GEO metadata profile / covered |
| `37a2351` | `feat(bio): add GEO page sample structure profiles` | metadata profile / UI / covered |
| `be7790b` | `feat(bio): harden GEO group recognition and analysis runners` | recognition / runners / covered |
| `4dfa894` | `feat(bio): add sample group preview` | group preview / covered |
| `b2e2cba` | `feat(bio): refine data readiness navigation UI` | readiness UI / covered |
| `c4aaedb` | `feat(bio): refine data import cache and selected recognition UI` | UI / cache / covered |
| `bf14b5a` | `feat(bio): connect dataset download manifests and GEO analysis` | download / recognition / covered |
| `97216b2` | `feat(bio): harden GEO asset recognition and DEG runner` | download / recognition / runner / covered |
| `f70a944` | `fix(bio): simplify GEO topic match wording` | UI wording / reference only |
| `c52e52d` | `fix(bio): clarify GEO asset downloads and comparison setup` | UI wording / reference only |
| `bcaec6e` | `feat(bio): refine dataset import search UI` | UI / covered |
| `c3ea8cc` | `feat(bio): add shared GEO detail and download list` | UI / download list / covered |
| `c2d2277` | `feat(bio): simplify TCGA and GTEx topic recommendations` | search UI / covered |
| `47f4795` | `feat(bio): split Chinese dataset search by source` | Chinese search UI / covered |
| `30e469c` | `feat(bio): refine Chinese dataset search UI` | Chinese search UI / covered |
| `020e173` | `fix(bio): harden GEO summary translation` | AI summary / high risk old direct Ollama |
| `5530acd` | `feat(bio): download GEO supplemental assets` | download / covered |
| `654a12c` | `feat(bio): discover GEO assets after metadata download` | download / covered |
| `083f5ec` | `feat(bio): download GEO candidates and run recognition` | download / recognition / covered |
| `94b2dfe` | `feat(bio): add dataset download service bridge` | download / covered |
| `6e1d169` | `feat(bio): harden GEO series matrix and tabular role recognition` | recognition / covered |
| `80c6ad0` | `feat(bio): support multi-role GEO SOFT recognition` | recognition / covered |
| `b1de2f5` | `fix(bio): recognize local xlsx count matrices` | recognition / covered |
| `aef04fa` | `feat(bio): register GEO search results as data sources` | search / data center / covered |
| `6051681` | `feat(bio): improve disease-aware dataset search` | GEO search / covered |

## 3. File Difference Table

| Path | Change | Module | Equivalent in current `dev/bioinformatics` | Recommendation |
| --- | --- | --- | --- | --- |
| `app/bioinformatics/comparison_config.py` | A | Bio comparison config | Present in current branch | Ignore |
| `app/bioinformatics/download/__init__.py` | A | Bio download | Present in current branch | Ignore |
| `app/bioinformatics/download/dataset_download_service.py` | A | GEO/TCGA/GTEx download | Current version is newer and larger, including manifest assets and invalid GSE handling | Ignore |
| `app/bioinformatics/download/geo_page_profile_service.py` | A | GEO detail profile | Present in current branch | Ignore |
| `app/bioinformatics/download/geo_text_summary_service.py` | A | GEO AI summary | Current version routes through AI Gateway; reviewed branch uses direct `/api/generate` | Do not integrate |
| `app/bioinformatics/group_preview.py` | A | group preview | Present in current branch | Ignore |
| `app/bioinformatics/pages/geo_download_page.py` | M | UI page | Current UI uses newer workflow integration | Ignore |
| `app/bioinformatics/project_readiness.py` | M | readiness | Current readiness flow is newer | Ignore |
| `app/bioinformatics/project_recognition.py` | M | recognition | Current recognition includes Series Matrix, supplementary, group preview, and newer hardening | Ignore |
| `app/bioinformatics/project_standardization.py` | M | standardization | Current implementation is newer | Ignore |
| `app/bioinformatics/retrieval/bio_query_adapter.py` | M | query adapter | Current implementation preserves Bio/Meta boundary and removes PubMed candidates | Ignore |
| `app/bioinformatics/search_center/geo_adapter.py` | M | GEO search | Current search center is newer | Ignore |
| `app/bioinformatics/search_center/gtex_adapter.py` | M | GTEx search | Current search center is newer | Ignore |
| `app/bioinformatics/search_center/query_understanding.py` | M | Chinese query understanding | Current version passes AI Gateway `bio_generate_dataset_query_draft` context | Do not replace |
| `app/bioinformatics/search_center/tcga_gdc_adapter.py` | M | TCGA search | Current adapter has later hardening | Ignore |
| `app/bioinformatics/services/correlation_runner.py` | A | runner | Present in current branch | Ignore |
| `app/bioinformatics/services/enrichment_runner.py` | A | runner | Present in current branch | Ignore |
| `app/bioinformatics/services/geo_differential_expression_runner.py` | A | runner | Current runner is newer and supports explicit group assignments | Ignore |
| `app/bioinformatics/services/geo_metadata_profile_service.py` | A | GEO metadata profile | Present in current branch with supplementary prioritization and candidate comparison evidence | Ignore |
| `app/bioinformatics/workflow_pages.py` | M | desktop Bio UI | Current version includes AI Gateway local AI loop, editable query drafts, cache actions, GSE search, and recognition workflow | Reference only |
| `app/bioinformatics/workspace.py` | M | Bio workspace | Current workspace is newer | Ignore |
| `app/shared/feature_availability.py` | M | shared | Cross-module change from Bio branch | Need manual confirmation only if ever considered |
| `app/shared/query_intelligence/local_model_bridge.py` | M | shared query intelligence | Current shared query intelligence routes local model calls through AI Gateway | Do not integrate |
| `app/shared/query_intelligence/query_intelligence_models.py` | M | shared query intelligence | Current model config is newer and gateway-aware | Do not integrate |
| `docs/stage_bio_*.md` | A | docs | Mostly historical stage notes | Reference only |
| `logs/validation/geo_random_recognition_audit.jsonl` | A | generated validation log | Generated artifact | Do not integrate |
| `scripts/bio_geo_random_recognition_audit.py` | A | audit script | Present in current branch | Ignore |
| `tests/bioinformatics/*` | A/M | Bio tests | Current suite covers these areas with newer expectations | Ignore |
| `tests/shared/test_query_intelligence_service.py` | M | shared tests | Cross-module test change from old local model assumptions | Do not integrate |
| `tests/ui/test_bioinformatics_workflow_pages.py` | M | Bio UI tests | Current test is newer and aligned with AI Gateway loop | Reference only |

## 4. Functional Gap Table

| Function point | Reviewed branch implementation | Current `dev/bioinformatics` implementation | Covered? | Suggested follow-up | Risk |
| --- | --- | --- | --- | --- | --- |
| Data import and search page refactor | `app/bioinformatics/workflow_pages.py` | Current `workflow_pages.py` has newer GSE, Chinese query, dataset list, notes, cache, recognition flow | Yes | None | Low |
| Chinese research question search entry | `workflow_pages.py`, `search_center/query_understanding.py` | Current Bio UI and search center use explicit `bio_generate_dataset_query_draft` Gateway context | Yes | None | Low |
| Independent Chinese search UI | `workflow_pages.py` | Current UI separates Chinese research draft/search behavior and keeps user-confirmed drafts editable | Yes | None | Low |
| GSE accession search | `workflow_pages.py`, `geo_adapter.py` | Current GSE search panel and registration flow | Yes | None | Low |
| invalid / not found GSE state | `dataset_download_service.py`, UI tests | Current download service validates GSE accession and UI handles status text | Yes | None | Low |
| GEO metadata profile | `geo_metadata_profile_service.py` | Current `geo_metadata_profile_service.py` includes sample-level profile, supplementary preview, candidate comparison evidence | Yes | None | Low |
| sample-level metadata grouping | `geo_metadata_profile_service.py`, `group_preview.py` | Current group preview and metadata profile include candidate assignments and invalid label filters | Yes | None | Low |
| candidate comparison evidence chain | `comparison_config.py`, metadata profile | Current comparison config, candidate comparisons, and confirmation actions exist | Yes | None | Low |
| Chinese summary simplification | `geo_text_summary_service.py` | Current summary service uses AI Gateway and safe fallback | Yes | Do not use old direct Ollama code | High if copied |
| User notes | `workflow_pages.py` | Current detail panel has `datasetUserNoteEdit`; notes are stored separately and excluded from AI prompts | Yes | None | Low |
| Historical cache add/delete | `workflow_pages.py` | Current UI has historical cache card and selected deletion actions | Yes | None | Low |
| Pending dataset list | `workflow_pages.py` | Current dataset list panel supports pending assets and batch actions | Yes | None | Low |
| Recognition checkbox and batch recognition | `workflow_pages.py` | Current dataset list supports selected entries and continue-to-recognition selection | Yes | None | Low |
| Readiness page simplification | `project_readiness.py`, `workflow_pages.py` | Current readiness navigation is newer | Yes | None | Low |
| group preview | `group_preview.py` | Current `group_preview.py` is present and tested | Yes | None | Low |
| supplementary prioritization | `dataset_download_service.py`, `geo_metadata_profile_service.py` | Current implementation detects expression candidates and prioritizes supplementary assets | Yes | None | Low |
| random GEO recognition audit | `scripts/bio_geo_random_recognition_audit.py` | Current script and tests are present | Yes | None | Low |
| DEG runner | `geo_differential_expression_runner.py` | Current runner is newer, including Series Matrix support and explicit group assignments | Yes | None | Low |
| enrichment runner | `enrichment_runner.py` | Current runner is present and tested | Yes | None | Low |
| correlation runner | `correlation_runner.py` | Current runner is present and tested | Yes | None | Low |

## 5. Content Not Recommended For Integration

- Old direct Ollama implementation in `app/bioinformatics/download/geo_text_summary_service.py`.
  - The reviewed branch calls `/api/tags` and `/api/generate` directly.
  - Current `dev/bioinformatics` routes GEO text summary through `app/shared/ai_gateway/`.
- Old shared query intelligence local model defaults and tests.
  - The reviewed branch changes `app/shared/query_intelligence/` and `tests/shared/`.
  - Current shared query intelligence has already been migrated to AI Gateway and should not be overwritten.
- Generated validation log `logs/validation/geo_random_recognition_audit.jsonl`.
  - Keep generated logs out of consolidation unless explicitly approved.
- Large old `workflow_pages.py` UI chunks.
  - Current Bio UI is newer and includes desktop local AI loop, editable drafts, notes, cache actions, download manifests, and recognition handoff.
- Any PubMed / Meta search content found in legacy files or historical branch content.
  - Bioinformatics must not gain PubMed / Embase / WOS / CNKI search behavior.
- Duplicate implementations of search center, metadata profile, group preview, or runners.
  - Current implementations are more recent and already tested.

## 6. Potentially Useful Reference Items

No production code should be copied directly from `codex/bio-search-ui-main`.

The only potentially useful material is historical reference:

- UI wording around GEO topic match simplification and asset download clarification.
- Stage documentation under `docs/stage_bio_*.md` if a future human reviewer wants context.
- Some UI tests may be useful as examples, but current tests should remain the source of truth.

## 7. Boundary Check

High-risk paths present in the branch diff:

- `app/shared/query_intelligence/local_model_bridge.py`
- `app/shared/query_intelligence/query_intelligence_models.py`
- `tests/shared/test_query_intelligence_service.py`

High-risk active behavior present in the reviewed branch:

- `app/bioinformatics/download/geo_text_summary_service.py` contains direct Ollama `/api/generate` and `/api/tags` calls.

No branch diff paths were found under:

- `app/meta_analysis/`
- `app/shell/`
- `app/main.py`
- packaging scripts
- `app/shared/ai_gateway/`

However, keyword searches against the branch history and legacy tree show PubMed / Meta / Ollama strings in legacy or unrelated files. Those are not valid integration candidates for Bioinformatics.

## 8. Overall Conclusion

Conclusion: **少量 UI 文案或测试可参考**.

`codex/bio-search-ui-main` should not be merged or cherry-picked as a branch. Current `dev/bioinformatics` already covers the substantive functionality in newer form. The reviewed branch also contains outdated local model behavior that bypasses AI Gateway and cross-module shared query changes, so direct integration would be unsafe. Future work, if any, should be limited to manually reviewing UI copy or test-case ideas.
