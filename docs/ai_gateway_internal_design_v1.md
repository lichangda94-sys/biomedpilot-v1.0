# BioMedPilot Internal AI Gateway v1

## Purpose

`app/shared/ai_gateway/` is an internal AI call boundary for future Bioinformatics and Meta Analysis assistance features. It is not a public token relay, registration system, paid API product, or commercial token distribution layer.

Version 1 implements only the safety foundation:

- typed request, response, provider status, and config models
- a default `DisabledProvider` that never calls any model
- module task prefix isolation
- privacy policy checks
- safe config loading from `config/ai_gateway_config.json`
- JSONL audit logging with summaries only by default
- tests for the default blocked/fallback behavior

## Module Boundary

Bioinformatics and Meta Analysis may share the gateway implementation, but their task namespaces are isolated.

- `module="bioinformatics"` may only call `bio_` task types.
- `module="meta_analysis"` may only call `meta_` task types.
- Unknown modules are blocked unless they are explicitly added to `allowed_task_prefixes` in config.
- The built-in Bioinformatics and Meta Analysis prefixes are strict and should not be relaxed by feature code.

The gateway does not modify the existing Bioinformatics or Meta Analysis workflows. Version 1 does not add PubMed to Bioinformatics, does not add GEO/TCGA/GTEx to Meta Analysis, and does not perform downloads, statistical analysis, or PRISMA workflow advancement.

## Default Privacy Policy

The default configuration is intentionally closed:

```json
{
  "allow_network": false,
  "allow_external_model": false,
  "allow_sensitive_upload": false,
  "store_raw_prompts": false,
  "store_raw_responses": false,
  "default_provider": "disabled"
}
```

With these defaults:

- no network access is permitted
- external model access is not permitted
- sensitive content upload is not permitted
- full prompts are not written to logs
- full responses are not written to logs
- the disabled provider returns a fallback message instead of model output

## Audit Logging

Audit events are written to:

`logs/ai_gateway/ai_gateway_audit.jsonl`

Each event records request id, module, task type, provider name, status, fallback flag, privacy flags, prompt length/hash, response length/hash, and context keys. Full prompt, full context, and full response bodies are excluded unless the corresponding storage flags are explicitly enabled in config.

Audit logging is best effort. Logger errors are swallowed so logging failures cannot crash the desktop app.

## Provider Flow

`AIGateway.generate(request)` performs:

1. request validation
2. module policy check
3. request privacy policy check
4. provider selection
5. provider privacy policy check
6. provider call
7. response normalization
8. audit log write

Any exception returns a safe error or fallback response and still attempts to write an audit event.

## Future Extension Plan

Future local or external providers should implement `AIProvider` and be registered through `AIProviderRegistry`.

Planned provider categories:

- `OllamaProvider`: local-only provider, no external upload, gated by local availability and per-task allowlists.
- `OpenAICompatibleProvider`: optional external provider for OpenAI-compatible endpoints, gated by `allow_network=true` and `allow_external_model=true`.

Provider configuration should be read from config files or environment-managed secrets. API keys must never be hardcoded in source, docs, tests, or default config.

Before enabling any real provider, add provider-specific tests for privacy blocking, timeout handling, redacted logging, task-prefix isolation, and safe fallback on provider errors.
