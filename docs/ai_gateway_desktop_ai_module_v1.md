# Desktop Local AI Module v1

## Current Support

- Local Ollama can be used only through `app/shared/ai_gateway/`.
- The desktop Bioinformatics settings page provides a minimal local AI status panel: mode, local address, default model, enable/disable, and connection test.
- Bioinformatics GEO dataset details can request a Chinese translation and one-sentence refinement draft with `task_type=bio_translate_dataset_detail`.
- Bioinformatics Chinese research topics can generate an editable dataset query draft with `task_type=bio_generate_dataset_query_draft`.
- Confirming a query draft records a lightweight draft status only. It does not run GEO, TCGA/GDC, or GTEx search.

## Current Non-Support

- No real external API provider is implemented.
- No OpenAI, DeepSeek, Gemini, Claude, or other external service is called.
- No token relay, payment, public registration, or commercial token distribution exists.
- No sensitive content is uploaded by default.
- AI output is not written into final analysis results.
- User confirmation does not automatically execute database retrieval.

## Privacy Boundary

Default AI Gateway config remains safe:

- `allow_network=false`
- `allow_external_model=false`
- `allow_sensitive_upload=false`
- `store_raw_prompts=false`
- `store_raw_responses=false`
- `default_provider=disabled`

Audit logs store request/response summaries, hashes, provider, model, status, fallback flag, and warnings. Full prompts and full responses are not stored by default.

## Desktop Config

The local AI settings panel reads and writes `config/ai_gateway_config.json`. Enabling local AI sets:

- `default_provider=ollama`
- `allow_network=true`
- `provider_configs.ollama.enabled=true`
- local Ollama base URL
- default model name

Disabling local AI restores a disabled provider and `allow_network=false`. The UI does not provide an API key field.

## Bioinformatics Boundaries

Bioinformatics uses only `bio_` task types. The local query draft can include GEO query text, TCGA project hints, and GTEx tissue hints. It must not generate PubMed, Embase, Web of Science, or CNKI search strings.

GEO dataset translation/refinement prompts contain dataset title, summary, and overall design only. User notes do not enter model input.

## External API Placeholder

External API support is reserved for a later design stage. A future provider must be gated by AI Gateway privacy policy, explicit configuration, and non-raw audit logging before any desktop UI entry is added.
