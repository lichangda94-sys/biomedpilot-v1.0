# Meta AI-assisted Extraction Queue v1

Stage M14 adds a testing-level AI-assisted extraction suggestion queue.

## Active Service

- Service: `app/meta_analysis/services/ai_assisted_extraction_queue_service.py`
- Generic suggestion service: `app/meta_analysis/services/ai_suggestion_service.py`
- Manual extraction draft target: `app/meta_analysis/services/manual_extraction_effect_row_service.py`
- Page state: `ai_extraction_suggestion_queue_state_from_project()` in `app/meta_analysis/pages/ai_suggestions_page.py`

## Artifacts

- Generic AI queue: `ai/ai_suggestions.json`
- Extraction suggestion queue: `extraction/extraction_ai_suggestion_queue.json`
- Extraction suggestion validation: `extraction/extraction_ai_suggestion_validation.json`
- Extraction suggestion application log: `extraction/extraction_ai_suggestion_applications.json`

## Workflow

1. Generate a suggestion from abstract, parsed PDF text, or manual text.
2. Store the suggestion with `pending` status.
3. Attach schema validation diagnostics, disease-guard metadata, rationale, and confidence.
4. Reviewer accepts, rejects, or edits the suggestion.
5. Only accepted suggestions can be applied.
6. Applying an accepted suggestion creates a Manual Data Extraction UI v1 draft effect row.

## Governance

- Suggestion creation records `suggestion_created`.
- Reviewer accept/reject/edit records user governance events through the generic AI suggestion queue.
- Applying an accepted extraction suggestion records a user confirmation event with `source_suggestion_id`.

## Safety Boundaries

- AI/PDF parsing output is suggestion only.
- Pending, rejected, or edited suggestions cannot write extraction drafts.
- Accepted suggestions are applied only as manual extraction draft effect rows.
- No analysis-ready dataset is created.
- No statistical analysis is run.
- No PRISMA counts are updated.
- Final extracted values still require human review and later analysis-plan governance.

## Current Limitations

- The extraction suggestion generator is heuristic/testing-level.
- It does not perform production PDF table extraction.
- It does not infer final study data.
- It supports first-pass binary, continuous, survival, and diagnostic 2x2 field suggestions.
- Disease guard metadata is a safety signal, not a final clinical validation.
