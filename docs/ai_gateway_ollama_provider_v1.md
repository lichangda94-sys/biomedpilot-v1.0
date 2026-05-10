# AI Gateway OllamaProvider v1

## Purpose

`OllamaProvider` is the first real provider implementation inside `app/shared/ai_gateway/`. It is a local-only provider for future BioMedPilot AI features that need a unified gateway boundary before calling an Ollama model.

This stage only adds the provider. It does not migrate existing shared query intelligence calls or Bioinformatics GEO summary calls, and it does not change Bioinformatics or Meta Analysis workflows.

## Default State

The AI Gateway default provider remains `disabled`.

Ollama is also disabled by default. Setting `default_provider` to `ollama` is not enough; the provider is registered only when `provider_configs.ollama.enabled` is `true`.

Safe default behavior:

- no external model
- no external API key
- no raw prompt audit logging
- no raw response audit logging
- no sensitive-content upload when the gateway request is marked sensitive
- safe fallback responses for provider errors

## Configuration

Example `config/ai_gateway_config.json`:

```json
{
  "allow_network": true,
  "default_provider": "ollama",
  "provider_configs": {
    "ollama": {
      "enabled": true,
      "base_url": "http://localhost:11434",
      "default_model": "medgemma:4b",
      "timeout_seconds": 20
    }
  }
}
```

Supported provider fields:

- `enabled`: boolean, default `false`
- `base_url`: local Ollama endpoint, default `http://localhost:11434`
- `default_model`: model used when a request does not specify one, default `medgemma:4b`
- `timeout_seconds`: HTTP timeout, default `20`

Because the provider uses local loopback HTTP, Gateway calls also require `allow_network=true`. External model access remains disabled unless a future provider explicitly needs it.

## Health Check

`OllamaProvider.detect_ollama_status()` calls `/api/tags` and returns:

- `disabled` when provider config is disabled
- `available` when the local endpoint responds with a 2xx status
- `unavailable` for connection errors, timeout, or non-2xx status
- `error` for unexpected implementation-level exceptions

All health-check failures are caught.

## Generate Behavior

`generate()` calls the local Ollama `/api/generate` endpoint with:

- configured model
- request prompt
- `stream=false`
- configured timeout

It handles connection failure, timeout, non-2xx status, empty HTTP response, invalid HTTP response JSON, missing generated content, and optional structured parsing when `output_format=json`.

JSON output parsing failure does not crash the app. The provider returns the generated content with a warning in response metadata.

## Privacy Boundary

The provider returns model output to the caller, but the AI Gateway audit logger stores only summaries by default:

- prompt length and hash
- response length and hash
- provider name
- model name
- status
- fallback flag
- warnings

It does not store full prompts or full responses unless the explicit gateway audit flags are enabled. BioMedPilot defaults keep those flags off.

Sensitive input must be marked on `AIGatewayRequest.contains_sensitive_content`. The gateway privacy policy blocks those requests unless `allow_sensitive_upload=true`.

## Relationship To Existing Calls

Existing direct Ollama-capable paths remain unchanged in this stage:

- `app/shared/query_intelligence/local_model_bridge.py`
- `app/bioinformatics/download/geo_text_summary_service.py`
- `app/bioinformatics/workflow_pages.py`
- legacy Bioinformatics GEO tool files

They are intentionally not migrated in AI-2B. The migration audit test now allows `app/shared/ai_gateway/providers/ollama_provider.py` as the only formal AI Gateway Ollama call point while still blocking direct Meta Analysis calls and unreviewed new direct callers.

## Next Migration Stage

Recommended next stage:

1. Add task-specific prompt wrappers for `bio_query_help`, `bio_geo_metadata_summary`, and `meta_query_help`.
2. Route shared query intelligence through `AIGateway.generate()` while preserving existing default-off behavior.
3. Remove raw model output from shared query-intelligence audit payloads.
4. Wrap Bioinformatics GEO metadata summarization behind Gateway requests.
5. Keep legacy GEO tool code isolated until it is removed or fully retired.
6. Add tests proving no active non-Gateway code calls Ollama directly after each migration step.
