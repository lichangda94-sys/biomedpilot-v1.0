# Integration Shared ImageJ/Fiji Detection Foundation - 2026-05-14

## Stage

ImageJ/Fiji detection foundation.

## Worktree

- Worktree: `/Users/changdali/Developer/biomedpilot v1.0/Integration`
- Branch: `dev/integration`
- Scope: shared local-engine infrastructure only.

## What Changed

Added `app/shared/local_engines/` as the shared foundation for local tool status and ImageJ/Fiji detection:

- Stable `EngineStatus` serialization with statuses:
  - `not_configured`
  - `configured_unverified`
  - `available`
  - `failed`
  - `unsupported_version`
- Local-only config storage through `LocalEngineConfigStore`.
- ImageJ/Fiji detector with common macOS path probing, explicit configured path support, executable validation, version parsing, and a minimal non-destructive macro smoke test.
- ImageJ/Fiji bridge wrapper for configure/check/clear flows.
- Install guide and setup prompt text for future contextual UI prompts.

## Boundaries

This stage does not add any real image-analysis workflow.

Explicitly not implemented:

- WB/gel grayscale analysis.
- Agarose gel analysis.
- Cell counting.
- Automatic ROI.
- Fluorescence or wound/scratch automation.
- Pathology image workflows.
- Ollama integration.
- Cloud AI, login, credits, payment, API keys, server upload.
- Packaging or desktop app refresh.

ImageJ/Fiji detection remains local-only:

- No network install.
- No silent download.
- No upload.
- No automatic macro execution outside user-triggered detection or future workflow setup.

## Future Consumer

LabTools should consume this shared foundation in a later stage. The recommended next consumer stage is:

1. Replace LabTools-specific ImageJ/Fiji status/config plumbing with `app.shared.local_engines`.
2. Keep LabTools UI feature-triggered; do not add a main-screen engine center.
3. Add the first ImageJ/Fiji-backed workflow only after a separate Tool Logic Card defines inputs, macro parameters, output files, provenance, warnings, manual-review wording, and no-overwrite export behavior.

## Validation

Target validation for this stage:

```bash
python3 -m pytest tests/shared -q
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q
python3 -m app.main --smoke-test
git diff --check
git diff --cached --check
```
