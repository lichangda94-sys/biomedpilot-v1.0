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
- No exact `localhost:11434` references were found; active HTTP callers use `http://127.0.0.1:11434`.
- Existing real Ollama paths are split between subprocess-based shared query intelligence and HTTP-based Bioinformatics GEO metadata summarization.

## Existing Call Inventory

| Area | File | Function / class | Current status | Invocation |
| --- | --- | --- | --- | --- |
| shared | `app/shared/query_intelligence/local_model_bridge.py` | `detect_local_model_status()`, `describe_local_model_components()`, `detect_ollama_status()` | active status detection | `shutil.which("ollama")` only |
| shared | `app/shared/query_intelligence/local_model_bridge.py` | `call_ollama_json()` | active direct model call when explicitly enabled | `subprocess.run(["ollama", "run", model], input=prompt, ...)` |
| shared | `app/shared/query_intelligence/local_model_bridge.py` | `generate_search_translation_candidates()` | active wrapper around `call_ollama_json()` | builds prompt and requires JSON |
| shared | `app/shared/query_intelligence/query_intelligence_service.py` | `analyze_medical_question()` | active status reporting only | detects Ollama availability, no model call |
| shared | `app/shared/query_intelligence/query_intelligence_service.py` | `build_search_translation_draft()` | active conditional caller | calls shared local model bridge only when `use_local_model=True` and `LocalModelConfig.enabled=True` |
| shared | `app/shared/query_intelligence/query_intelligence_models.py` | `LocalModelConfig`, `LocalModelCallResult`, `LocalModelSearchTranslation` | active config/result models | defaults to disabled Ollama config |
| Bioinformatics | `app/bioinformatics/download/geo_text_summary_service.py` | `GeoTextSummaryService` | active optional UI service | HTTP GET `/api/tags`, POST `/api/generate` against `http://127.0.0.1:11434` |
| Bioinformatics | `app/bioinformatics/workflow_pages.py` | `BioinformaticsDataSourceWidget`, `BioinformaticsChineseDatasetSearchWidget`, local AI settings status | active UI wiring | instantiates `GeoTextSummaryService(timeout=20)` and checks `shutil.which("ollama")` |
| Bioinformatics | `app/bioinformatics/search_center/query_understanding.py` | `QueryUnderstandingLayer.understand()` | active conditional path | forwards `use_local_model` to shared query intelligence; default is `False` |
| Bioinformatics | `app/bioinformatics/search_center/router.py` | `BioinformaticsSourceRouter.search()` | active conditional path | forwards `use_local_model`; default is `False` |
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
  - covers Ollama unavailable fallback, default not-called behavior, successful mocked JSON, invalid JSON fallback, disease guard filtering, and bio/meta context filtering.
  - monkeypatches `shutil.which` and `subprocess.run`; it does not require a real Ollama process.
- `tests/bioinformatics/test_dataset_download_service.py`
  - covers `GeoTextSummaryService` with injected generators, model availability aliases, missing model fallback, empty brief fallback, and local-model-unavailable fallback.
  - uses dependency injection; it does not require real HTTP calls.
- UI tests assert local model status text, but do not call Ollama.

## Current Behavior

### Shared query intelligence

Shared query intelligence defaults to safe local rules:

- `LocalModelConfig.enabled=False`
- `build_search_translation_draft(..., use_local_model=False)` by default
- `allow_network` is accepted by `build_search_translation_draft()` and recorded in audit, but it is not the switch that gates the local model call.

An Ollama subprocess call only occurs when both are true:

- caller passes `use_local_model=True`
- caller passes or resolves `LocalModelConfig(enabled=True)`

The subprocess path uses `ollama run <model>` with prompt on stdin. It does not use `base_url`, `/api/generate`, or `/api/chat`.

### Bioinformatics GEO metadata summarization

`GeoTextSummaryService` is active in Bioinformatics UI code and is the only active HTTP Ollama caller. It:

- checks model availability with `/api/tags`
- requires both `translategemma` and `medgemma:4b`
- translates GEO title/summary/overall design
- builds one Chinese brief
- uses `stream=False`, `keep_alive=0`, and low temperature
- returns fallback summaries instead of raising to UI callers through `summarize()`

### Meta Analysis

Meta Analysis currently has no direct Ollama call. It consumes shared query intelligence with `use_local_model=False` in the observed production paths. Shared context filtering removes GEO candidates for Meta Analysis and excludes TCGA/GTEx audit candidates.

## Safety Assessment

### Direct AI Gateway bypass

Yes. All existing Ollama-capable paths bypass `app/shared/ai_gateway/` because they predate Stage AI-1:

- shared query intelligence calls `ollama run` directly when enabled
- Bioinformatics GEO metadata summarization calls the local HTTP endpoint directly
- legacy GEO tool calls the local HTTP endpoint directly

This is expected for AI-2A but should not continue after an Ollama provider is introduced.

### Raw prompt storage

No active path intentionally persists raw prompts. Prompts are built in memory and sent to the subprocess or local HTTP endpoint.

### Raw response storage

Partially unsafe:

- shared query intelligence stores model raw output in `LocalModelCallResult.raw_output`, `LocalModelSearchTranslation.raw_output`, and `SearchTranslationDraft.audit["local_model"]["raw_output"]`.
- Bioinformatics `GeoTextSummaryService` does not include raw model responses in `GeoStudyTextSummary.to_dict()`.
- legacy `GeoTextProcessor` returns parsed text and raises exceptions, but does not define a redacted audit boundary.

The shared raw-output audit field should be removed, redacted, or moved behind an explicit `store_raw_responses` policy before routing through AI Gateway.

### Sensitive upload control

No existing Ollama caller has a sensitive-content gate equivalent to `AIGatewayRequest.contains_sensitive_content` plus `AIGatewayConfig.allow_sensitive_upload`.

Current prompts may include:

- user research questions
- GEO titles, abstracts/summaries, and overall design text
- translated or generated metadata

Because the current endpoint is local Ollama, this is lower risk than external upload, but it is still ungoverned and should be wrapped by AI Gateway policy before expansion.

### Network / local endpoint control

Mixed:

- shared query intelligence uses `ollama run`, so no HTTP base URL is configured.
- Bioinformatics GEO metadata summarization uses `http://127.0.0.1:11434`.
- `allow_network=False` is passed in several query-intelligence calls but is not a hard gate for the subprocess local model path.
- no single config controls provider mode, base URL, model names, timeout, enabled flag, and raw storage policy.

### Module boundary

Mostly safe in final outputs, with one audit caveat:

- Bioinformatics final `SearchTranslationDraft` clears `pubmed_query_candidates`.
- Meta Analysis final `SearchTranslationDraft` clears `geo_query_candidates` and excludes TCGA/GTEx/GEO context fields.
- `app/shared/search_context.py` adds an additional context filter for Bioinformatics and Meta Analysis.
- The shared local-model prompt asks for both PubMed and GEO candidates regardless of `target_context`, then filters later. If raw model output remains in audit, out-of-context candidates may still be visible in `audit["local_model"]["raw_output"]`.

### Fallback behavior

Shared subprocess path:

- Ollama command missing: returns unavailable / registry fallback.
- model missing or subprocess nonzero: returns `called_failed_fallback_registry`.
- timeout: returns `called_failed_fallback_registry`.
- invalid JSON: returns `invalid_model_output_fallback_registry`.
- JSON root not object: returns `invalid_model_output_fallback_registry`.
- schema mismatch: returns `invalid_model_output_fallback_registry`.
- empty stdout: treated as invalid JSON and falls back.

Bioinformatics HTTP summary path:

- Ollama unavailable or `/api/tags` fails: returns `local_model_unavailable` with conservative fallback.
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
- `detect_ollama_status()` and command detection from `local_model_bridge.py`.
- subprocess error mapping from `call_ollama_json()`.
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

1. Add a Gateway `OllamaProvider` behind disabled-by-default config.
2. Keep AI Gateway default provider as `disabled`; do not change Stage AI-1 default behavior.
3. Define task-specific request types before enabling any call:
   - `bio_query_help`
   - `bio_geo_metadata_summary`
   - `meta_query_help`
   - future tasks only after explicit allowlist review
4. Use AI Gateway module policy as the first boundary:
   - Bioinformatics calls only `bio_` tasks.
   - Meta Analysis calls only `meta_` tasks.
5. Move shared local model calls behind Gateway request metadata:
   - no raw prompt/response logging by default
   - record prompt/response hash and lengths only
   - map current statuses into `AIGatewayResponse.status`
6. Decide provider transport:
   - prefer `ollama run` for local-only no-HTTP mode, or
   - support local loopback HTTP only with explicit provider config and audit labeling
7. Wrap `GeoTextSummaryService` with a Gateway adapter instead of calling `/api/generate` directly.
8. Keep legacy files untouched until their callers are confirmed unused; if retained, mark them as legacy/direct and exclude from new UI paths.
9. Add migration tests that prove no active `app/` code calls `ollama run` or `/api/generate` except the provider implementation and legacy excluded paths.

## Risks

- Two Ollama systems could coexist if `OllamaProvider` is added without migrating `local_model_bridge.py` and `GeoTextSummaryService`.
- Shared query intelligence currently can preserve raw model responses in audit payloads.
- Existing `allow_network` arguments can look like policy enforcement but do not govern the subprocess path.
- Local HTTP endpoint usage may be mistaken for "no network"; it still sends full prompts to a service over HTTP.
- Bioinformatics and Meta Analysis final outputs are filtered, but raw local-model output can contain cross-module candidates before filtering.
- UI-level optional GEO summarization can send GEO metadata to Ollama without an AI Gateway sensitive-content decision.
- Legacy code raises exceptions rather than using the new normalized `AIGatewayResponse` contract.

## Recommended Next Stage

Stage AI-2B should implement a disabled-by-default `OllamaProvider` inside `app/shared/ai_gateway/providers/` without changing callers.

Recommended design:

- Provider name: `ollama`
- Default status: unavailable unless config explicitly enables it.
- Transport: start with subprocess `ollama run` to avoid introducing a local HTTP base URL into the first provider, or add local HTTP as an explicit config field with audit labeling.
- Config fields:
  - `enabled`
  - `transport`
  - `base_url`
  - `model`
  - `timeout_seconds`
  - `require_json`
  - `temperature`
  - `keep_alive`
- Safety:
  - no external model
  - no API key
  - no raw prompt/response storage by default
  - explicit sensitive-content blocking via Gateway privacy policy
  - task-specific prompt templates, not one shared all-context prompt
- Tests:
  - default disabled behavior remains unchanged
  - command missing fallback
  - model failure fallback
  - timeout fallback
  - invalid JSON fallback
  - empty response fallback
  - audit log redaction
  - Bioinformatics cannot call `meta_` tasks
  - Meta Analysis cannot call `bio_` tasks
