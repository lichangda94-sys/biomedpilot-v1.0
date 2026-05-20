# Meta Search Draft Review Gate

Date: 2026-05-20

## Scope

This stage adds a user confirmation gate on top of the Meta seed search config draft.

Changed files:

- `app/meta_analysis/search_config_draft.py`
- `app/meta_analysis/workspace.py`
- `tests/meta_analysis/test_meta_seed_search_config_draft.py`
- `tests/meta_analysis/test_mainline_meta_contract.py`

Protected boundaries:

- No seed expansion.
- No shared core changes.
- No Bioinformatics changes.
- No legacy Meta runtime JSON changes.
- No online PubMed, Embase, Web of Science, or Chinese database retrieval.
- No PDF extraction UI.

## Review States

The search config draft now supports:

- `draft_only`: auto-generated draft exists but has not been confirmed.
- `needs_edit`: user has edited notes, selected terms, included blocks, or query text.
- `user_confirmed`: user explicitly confirmed the reviewed plan.
- `rejected`: user rejected the draft; it cannot enter downstream workflow.

## Saved Artifacts

Draft review payload:

`search_strategy/meta_seed_search_config_draft.json`

Confirmed plan payload:

`search_strategy/confirmed_search_plan.json`

The draft review payload preserves:

- `auto_generated_draft`
- `user_edited_plan`
- `confirmed_search_plan` when explicitly confirmed, otherwise `null`
- `search_execution_status=not_executed`
- `formal_search_completed=false`

The project config stores only draft/plan pointers and review state. Confirmation does not execute retrieval.

## UI Behavior

The active Meta workspace `search_config_draft` page now supports:

- Chinese research question input.
- Generated PICO/PECO block display.
- Generated PubMed query draft display.
- Editable PubMed query draft field.
- User notes field for selected terms / included blocks.
- Save draft.
- Confirm as search plan.
- Reject draft.
- Visible query guard and warnings.

## Guard Rules

The review gate preserves the existing seed guards:

- `effect_measure`: remains extraction/statistics oriented and does not enter PubMed topic expansion.
- `research_intent`: remains classification-only and does not enter PubMed topic expansion.
- `study_design`: remains `filter_only=true`.
- `outcome`: remains conditional and requires disease/population pairing.

Manual guard overrides are allowed to be recorded as reviewer edits, but they generate override warnings and are not automatically considered safe.

## Test Coverage

Added or updated tests cover:

- Four Chinese question examples still generate drafts.
- Unconfirmed drafts cannot become confirmed plans.
- Confirmed plans preserve both auto draft and user edits.
- Rejected drafts do not enter downstream flow.
- Guard override records a warning.
- Workspace page can generate and confirm a draft without executing retrieval.

## Verification

Validation completed:

```bash
git diff --check
# pass
python3 -m pytest tests/meta_analysis -q
# 13 passed
python3 -m pytest tests/shared/test_meta_seed_terms.py -q
# 9 passed
python3 -m pytest tests/shared/test_query_intelligence_service.py -q
# 21 passed
python3 -m app.main --smoke-test
# pass
```

## Decision

The Meta seed search configuration flow now has a hard review gate. Only `user_confirmed` plans produce `confirmed_search_plan.json`; draft-only, edited-but-unconfirmed, and rejected records remain non-executable and cannot be treated as formal search completion.
