# AI Gateway Ollama Existing Call Audit

Stage: AI-2A
Baseline commit: `75c3f0a feat(shared): add internal ai gateway foundation`
Scope: audit only. No provider implementation, no workflow refactor, no behavior change.

## Search Coverage

The audit searched the repository for:

- `ollama`
- `qwen`
- `local_model`
- `LocalModel`
- `detect_ollama`
- `localhost:11434`
- `/api/generate`
- `/api/chat`
- `use_local_model`
- `allow_network`
- `prompt`

Findings:

- No `qwen` references were found.
- No `/api/chat` references were found.
- Before AI-2B, no exact `localhost:11434` references were found; the AI Gateway `OllamaProvider` now uses `http://localhost:11434` as its disabled-by-default base URL.
- AI-2C migrated shared query intelligence off the direct `ollama run` subprocess path and into AI Gateway.
- Stage Desktop Local AI Loop migrated Bioinformatics GEO metadata summarization and local AI settings status off direct Ollama checks. Remaining direct Ollama paths are the formal AI Gateway `OllamaProvider` plus legacy/archive GEO tool files that are not active new integration points.
- `app/shared/ai_gateway/providers/ollama_provider.py` is now the reviewed AI Gateway Ollama call point. It remains disabled unless explicitly enabled in AI Gateway provider config.
- `app/meta_analysis/` currently has no direct Ollama call; Meta Analysis only consumes shared query-intelligence drafts with local model disabled in active paths.

## Existing Call Inventory

| Area | File | Function / class | Current status | Invocation |
| --- | --- | --- | --- | --- |
| shared | `app/shared/query_intelligence/local_model_bridge.py` | `detect_local_model_status()`, `describe_local_model_components()`, `detect_ollama_status()` | gateway-managed status reporting | no direct command or HTTP call |
| shared | `app/shared/query_intelligence/local_model_bridge.py` | `call_ai_gateway_json()` | active Gateway caller when explicitly enabled and module/task are provided | `AIGateway.generate()` |
| shared | `app/shared/query_intelligence/local_model_bridge.py` | `generate_search_translation_candidates()` | active wrapper around AI Gateway response parsing | builds prompt and requires JSON |
| shared AI Gateway | `app/shared/ai_gateway/providers/ollama_provider.py` | `OllamaProvider.detect_ollama_status()`, `OllamaProvider.generate()` | formal Gateway provider, disabled by default | HTTP GET `/api/tags`, POST `/api/generate` against `http://localhost:11434` only when enabled |
| shared | `app/shared/query_intelligence/query_intelligence_service.py` | `analyze_medical_question()` | active status reporting only | detects Ollama availability, no model call |
| shared | `app/shared/query_intelligence/query_intelligence_service.py` | `build_search_translation_draft()` | active conditional caller | calls shared local model bridge only when `use_local_model=True` and `LocalModelConfig.enabled=True` |
| shared | `app/shared/query_intelligence/query_intelligence_models.py` | `LocalModelConfig`, `LocalModelCallResult`, `LocalModelSearchTranslation` | active config/result models | defaults to disabled Ollama config |
| Bioinformatics | `app/bioinformatics/download/geo_text_summary_service.py` | `GeoTextSummaryService` | active optional UI service | calls `AIGateway.generate()` with `module=bioinformatics`, `task_type=bio_translate_dataset_detail` |
| Bioinformatics | `app/bioinformatics/workflow_pages.py` | `BioinformaticsDataSourceWidget`, `BioinformaticsChineseDatasetSearchWidget`, local AI settings status | active UI wiring | instantiates `GeoTextSummaryService(timeout=20)` and tests local status through AI Gateway provider helpers |
| Bioinformatics | `app/bioinformatics/search_center/query_understanding.py` | `QueryUnderstandingLayer.understand()` | active conditional path | forwards explicit Gateway module/task context to shared query intelligence; default local model is off |
| Bioinformatics | `app/bioinformatics/search_center/router.py` | `BioinformaticsSourceRouter.search()` | active conditional path | forwards explicit Gateway context; default local model is off |
| Bioinformatics | `app/bioinformatics/retrieval/bio_query_adapter.py` | `build_bioinformatics_query_strategy()` | active default-off path | calls shared query intelligence with `use_local_model=False` |
| Meta Analysis | `app/meta_analysis/search/strategy_builder.py` | `_shared_meta_translation()` | active default-off path | calls shared query intelligence with `use_local_model=False` |
| Meta Analysis | `app/meta_analysis/services/pico_workspace_service.py` | `PICOProtocolWorkspaceService.generate_draft()` | active default-off path | calls shared query intelligence with `use_local_model=False` |
| Meta Analysis | `app/meta_analysis/services/ai_assisted_extraction_queue_service.py` | `_disease_guard()` | active default-off path | calls shared query intelligence without enabling local model |
| legacy | `app/bioinformatics/legacy/geo_tool/geo_text_processor.py` | `GeoTextProcessor`, `OllamaAPIError` | legacy runtime source | HTTP GET `/api/tags`, POST `/api/generate` via `requests` |
| legacy | `app/bioinformatics/legacy/geo_tool/bootstrap_geo_tool.sh` | shell bootstrap | legacy setup helper | `command -v ollama`, `ollama list` |
| archive | `archive/legacy_sources/bioinformatics_project/geo_tool/geo_text_processor.py` | `GeoTextProcessor`, `OllamaAPIError` | archived copy | HTTP GET `/api/tags`, POST `/api/generate` via `requests` |
| archive | `archive/legacy_sources/bioinformatics_project/geo_tool/bootstrap_geo_tool.sh` | shell bootstrap | archived helper | `command -v ollama`, `ollama list` |

Tests covering existing behavior:

- `tests/shared/test_query_intelligence_service.py`
  - covers Gateway fallback, default not-called behavior, successful mocked Gateway JSON, invalid JSON fallback, disease guard filtering, and bio/meta context filtering.
  - uses mocked AI Gateway providers; it does not require a real Ollama process.
- `tests/bioinformatics/test_dataset_download_service.py`
  - covers `GeoTextSummaryService` with injected generators, mocked AI Gateway, model availability aliases, missing model fallback, empty brief fallback, and local-model-unavailable fallback.
  - uses dependency injection; it does not require real HTTP calls.
- UI tests assert local model status text, but do not call Ollama.
- `tests/shared/test_ai_gateway_ollama_migration_audit.py`
  - records the complete current direct-call inventory.
  - asserts active direct Ollama calls remain limited to AI Gateway `OllamaProvider`.
  - asserts Meta Analysis contains no direct Ollama calls and AI Gateway contains no direct call outside the reviewed provider.

## Active Isolation Guard

With AI-2C, active direct Ollama-capable code must remain limited to:

- `app/shared/ai_gateway/providers/ollama_provider.py`
- `app/bioinformatics/download/geo_text_summary_service.py`
- `app/bioinformatics/workflow_pages.py`

Legacy direct-call files are documented but should not be used as new integration points:

- `app/bioinformatics/legacy/geo_tool/geo_text_processor.py`
- `app/bioinformatics/legacy/geo_tool/bootstrap_geo_tool.sh`

The migration guard test intentionally fails if:

- Meta Analysis adds a direct Ollama call.
- AI Gateway adds a direct Ollama call outside `app/shared/ai_gateway/providers/ollama_provider.py`.
- new active `app/` code calls `/api/generate`, `/api/tags`, `ollama run`, or checks `shutil.which("ollama")` without updating the audit and migration plan.

## Current Behavior

### Shared query intelligence

Shared query intelligence defaults to safe local rules:

- `LocalModelConfig.enabled=False`
- `build_search_translation_draft(..., use_local_model=False)` by default
- `allow_network` is accepted by `build_search_translation_draft()` and recorded in audit, but it is not the switch that gates the local model call.

An AI Gateway local-model call only occurs when all are true:

- caller passes `use_local_model=True`
- caller passes or resolves `LocalModelConfig(enabled=True)`
- caller explicitly provides AI Gateway `module` and `task_type`

The shared path no longer invokes `ollama run`, `/api/generate`, or `/api/chat` directly. It sends an `AIGatewayRequest` and relies on Gateway module/privacy/provider policy.

### Bioinformatics GEO metadata summarization

`GeoTextSummaryService` is active in Bioinformatics UI code and no longer owns HTTP Ollama calls. It:

- checks local provider availability through the Gateway provider status helper when local AI is enabled
- preserves the existing translate/brief model configuration
- translates GEO title/summary/overall design
- builds one Chinese brief
- sends requests through `AIGateway.generate()`
- returns fallback summaries instead of raising to UI callers through `summarize()`

### Meta Analysis

Meta Analysis currently has no direct Ollama call. It consumes shared query intelligence with `use_local_model=False` in the observed production paths. Shared context filtering removes GEO candidates for Meta Analysis and excludes TCGA/GTEx audit candidates.

## Safety Assessment

### Direct AI Gateway bypass

Partially. AI-2C removes the shared query-intelligence bypass, but Bioinformatics GEO metadata summarization and legacy GEO code still predate Gateway:

- Bioinformatics GEO metadata summarization calls the local HTTP endpoint directly
- legacy GEO tool calls the local HTTP endpoint directly

### Raw prompt storage

No active shared query-intelligence path intentionally persists raw prompts. Prompts are built in memory and sent through AI Gateway when explicitly enabled.

### Raw response storage

Improved in AI-2C:

- shared query intelligence no longer writes raw model output into `SearchTranslationDraft.audit["local_model"]`.
- shared query intelligence now records local-model status, provider, fallback flag, output length, output hash, and warnings.
- Bioinformatics `GeoTextSummaryService` does not include raw model responses in `GeoStudyTextSummary.to_dict()`.
- legacy `GeoTextProcessor` returns parsed text and raises exceptions, but does not define a redacted audit boundary.

### Sensitive upload control

Shared query intelligence now goes through AI Gateway policy when local model use is explicitly enabled. Bioinformatics GEO metadata summarization and legacy GEO code still do not have an AI Gateway sensitive-content gate.

Current prompts may include:

- user research questions
- GEO titles, abstracts/summaries, and overall design text
- translated or generated metadata

Because the current endpoint is local Ollama, this is lower risk than external upload, but it is still ungoverned and should be wrapped by AI Gateway policy before expansion.

### Network / local endpoint control

Current active code is Gateway-routed:

- shared query intelligence uses AI Gateway and no longer owns a direct Ollama command or HTTP endpoint.
- Bioinformatics GEO metadata summarization uses AI Gateway and no longer calls local HTTP endpoints directly.
- `allow_network=False` is still recorded by shared query intelligence for draft provenance, while AI Gateway privacy policy governs provider calls.
- Desktop settings write the shared AI Gateway config for provider mode, base URL, model name, timeout, enabled flag, and raw storage policy.

### Module boundary

Mostly safe in final outputs, with one audit caveat:

- Bioinformatics final `SearchTranslationDraft` clears `pubmed_query_candidates`.
- Meta Analysis final `SearchTranslationDraft` clears `geo_query_candidates` and excludes TCGA/GTEx/GEO context fields.
- `app/shared/search_context.py` adds an additional context filter for Bioinformatics and Meta Analysis.
- The shared local-model prompt asks for both PubMed and GEO candidates regardless of `target_context`, then filters later. AI-2C removes raw output from audit so out-of-context raw model candidates are not retained there.

### Fallback behavior

Shared AI Gateway path:

- missing Gateway module/task type: returns registry fallback without calling a provider.
- disabled config: returns `disabled_by_config`.
- provider unavailable, model missing, timeout, or provider error: returns `called_failed_fallback_registry`.
- invalid JSON: returns `invalid_model_output_fallback_registry`.
- JSON root not object: returns `invalid_model_output_fallback_registry`.
- schema mismatch: returns `invalid_model_output_fallback_registry`.
- empty content: Gateway provider fallback, then shared registry fallback.

Bioinformatics Gateway summary path:

- Ollama disabled or unavailable: returns `local_model_unavailable` with conservative fallback.
- model missing: returns `local_model_unavailable` with conservative fallback.
- `/api/generate` HTTP/JSON/timeout failure: `summarize()` catches and returns `failed` with conservative fallback.
- translation JSON parse failure: returns `failed` with fallback.
- brief JSON parse failure: tries to clean text; if empty, falls back.
- empty response: raises inside `_generate()`, then `summarize()` returns fallback.

Legacy HTTP path:

- raises `OllamaAPIError` on HTTP failure, empty response, invalid JSON, or non-object JSON.
- legacy UI catches some errors and emits UI error messages.
- no central fallback contract.

## Reuse Candidates

Good candidates for `OllamaProvider`:

- `LocalModelConfig` defaults: `enabled`, `medical_model`, `translator_model`, `timeout_seconds`, `require_json`, fallback semantics.
- AI-2C Gateway response mapping from `local_model_bridge.py`.
- JSON-object validation and schema checks from `local_model_bridge.py`.
- `/api/tags` model availability logic from `GeoTextSummaryService`.
- `/api/generate` request shape from `GeoTextSummaryService`:
  - `stream=False`
  - `keep_alive=0`
  - low temperature
- fallback summary strategy and quality warnings from `GeoTextSummaryService`.
- disease guard and context filters from shared query intelligence and `app/shared/search_context.py`.

Pieces that should not be reused unchanged:

- `SearchTranslationDraft.audit["local_model"]["raw_output"]`
- prompt templates that request both PubMed and GEO outputs for every module without task-specific scoping
- direct HTTP calls from Bioinformatics UI services once Gateway routing exists
- legacy `requests` implementation as an active provider dependency

## Migration Plan

Completed:

1. Added a Gateway `OllamaProvider` behind disabled-by-default config.
2. Kept AI Gateway default provider as `disabled`.
3. Routed shared query intelligence local-model calls through `AIGateway.generate()`.
4. Removed shared query-intelligence raw model output from audit payloads.
5. Updated direct-call isolation tests so shared query intelligence is no longer an active direct Ollama caller.

Remaining:

1. Define task-specific request wrappers before enabling production callers:
   - `bio_query_help`
   - `bio_geo_metadata_summary`
   - `meta_query_help`
   - future tasks only after explicit allowlist review
2. Use AI Gateway module policy as the first boundary:
   - Bioinformatics calls only `bio_` tasks.
   - Meta Analysis calls only `meta_` tasks.
3. Keep `GeoTextSummaryService` on the Gateway path and prevent any new direct endpoint call outside `OllamaProvider`.
4. Keep legacy files untouched until their callers are confirmed unused; if retained, mark them as legacy/direct and exclude from new UI paths.
5. Add migration tests after each step proving no active `app/` code calls Ollama directly except reviewed provider or legacy-excluded paths.

## Risks

- Legacy/archive GEO tool files still contain direct local Ollama calls, but they are not active new integration points and remain excluded by isolation tests.
- Existing shared `allow_network` arguments are provenance metadata; AI Gateway policy is the enforcement point for provider calls.
- Local HTTP endpoint usage may be mistaken for "no network"; it still sends full prompts to a service over HTTP.
- Bioinformatics and Meta Analysis final outputs are filtered, but shared prompt templates can still request both PubMed and GEO candidate fields before filtering.
- UI-level optional GEO summarization can send GEO metadata to Ollama without an AI Gateway sensitive-content decision.
- Legacy code raises exceptions rather than using the new normalized `AIGatewayResponse` contract.

## Recommended Next Stage

Stage AI-2D should migrate Bioinformatics GEO metadata summarization to AI Gateway without changing default-off behavior.

Recommended scope:

- Keep default provider disabled.
- Preserve existing GEO summary UI fallback behavior.
- Route Bioinformatics GEO summary calls through `AIGateway.generate()` with a `bio_` task type.
- Keep Meta Analysis free of GEO/TCGA/GTEx imports.
- Continue to avoid raw prompt/response audit storage.
