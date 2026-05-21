# Meta Seed Search Config Integration Audit

Date: 2026-05-20

## Scope

This stage connects the curated Meta seed helper to the active Meta project workspace as a draft-only search configuration step.

Implemented files:

- `app/meta_analysis/search_config_draft.py`
- `app/meta_analysis/workspace.py`
- `tests/meta_analysis/test_meta_seed_search_config_draft.py`
- `tests/meta_analysis/test_mainline_meta_contract.py`

Protected boundaries:

- Shared core was not modified.
- Bioinformatics vocabularies and Bioinformatics runtime were not modified.
- Legacy Meta runtime JSON files were not modified.
- No seed expansion was performed.
- No PubMed, Embase, Web of Science, CNKI, WanFang, VIP, or other online retrieval is executed.
- No Chinese database retrieval is supported in this stage.
- No Chinese PDF extraction is supported in this stage.
- No English PDF extraction UI is supported in this stage.
- No final extraction table is written.

## Draft Model

`MetaSeedSearchConfigDraft` stores:

- Original Chinese research question.
- Draft status and confirmation requirement.
- Search execution status.
- Detected PICO/PECO concepts.
- Detected research intent.
- PubMed query blocks and joined draft query.
- Query guard details for every detected seed concept.
- Warnings and unsupported feature markers.

The draft is saved to:

`search_strategy/meta_seed_search_config_draft.json`

Saving also records a pointer in `meta_project_config.json`, but keeps:

- `draft_status= draft_needs_user_confirmation`
- `search_execution_status= not_executed`
- `online_retrieval_executed= false`
- `formal_search_completed= false`

## Workspace Integration

The active Meta workspace now exposes a `Seed 检索草稿` step with page key:

`search_config_draft`

The page supports local Chinese question input and displays:

- Population
- Exposure/Intervention
- Outcome
- Intent
- PubMed query draft
- Draft-only status
- Query guard values

This is not a formal search step. It is a user-confirmation draft before any future retrieval workflow.

## Chinese Example Coverage

The integration tests cover:

- `糖尿病前期与甲状腺癌风险的关系`
- `二甲双胍治疗2型糖尿病的疗效`
- `放射性碘治疗甲状腺癌复发的影响`
- `肥胖与乳腺癌风险的Meta分析`

Expected behavior:

- Curated disease/exposure/intervention/outcome seeds are detected.
- English PubMed query draft is generated from curated MeSH/free-text mappings.
- Research intent is detected but does not become an unconditional topic query.
- Study design terms remain filter-only.

## Query Guard Behavior

Guard visibility is included for every detected seed:

- `effect_measure`: not included in PubMed topic expansion; remains PDF/extraction oriented.
- `research_intent`: not included in PubMed topic expansion; used for question classification.
- `study_design`: `filter_only=true`; not included in topic expansion.
- `outcome`: `query_expansion_allowed=conditional` and requires population/disease pairing.

Outcome expansion rule:

- With a disease/population pair, outcome terms can enter the draft query.
- Without a disease/population pair, outcome terms are shown in guard output but excluded from the draft query with a warning.

## Verification Plan

Validation completed:

```bash
git diff --check
# pass
python3 -m pytest tests/meta_analysis -q
# 8 passed
python3 -m pytest tests/shared/test_meta_seed_terms.py -q
# 9 passed
python3 -m pytest tests/shared/test_query_intelligence_service.py -q
# 21 passed
python3 -m app.main --smoke-test
# pass
```

## Decision

The integration is accepted as a draft-only local configuration layer. It is intentionally separate from formal Meta task creation and online retrieval. The next safe stage is user-confirmed search strategy editing, not automatic retrieval execution.
