# BioMedPilot Branch Development Rules

## Current Mainline

The unified mainline branch is:

```text
stable/mainline
```

Desktop app packaging should use `stable/mainline` unless the user explicitly approves another target branch.

## Long-lived Development Branches

Use these branches for ongoing module work:

```text
dev/bioinformatics
dev/meta-analysis
dev/shared-vocabulary
```

## Repository Guardrail

Do not continue BioMedPilot development in this old directory:

```text
/Users/changdali/Documents/New project 2
```

All BioMedPilot branch organization and development work should happen in:

```text
/Users/changdali/Documents/BioMedPilot
```

## Required Preflight Checks

Before starting development, run and inspect:

```bash
pwd
git rev-parse --show-toplevel
git branch --show-current
git status --short
```

Stop before making changes if:

- `pwd` is not `/Users/changdali/Documents/BioMedPilot`.
- `git rev-parse --show-toplevel` is not `/Users/changdali/Documents/BioMedPilot`.
- The current branch does not match the intended module.
- `git status --short` shows unexpected files.

## Module Branch Rules

Bioinformatics module development must be based on:

```text
dev/bioinformatics
```

Meta Analysis module development must be based on:

```text
dev/meta-analysis
```

Shared vocabulary, Chinese search mapping, query intelligence, and AI Gateway shared logic must be based on:

```text
dev/shared-vocabulary
```

## Desktop App Packaging

Package the desktop app only from:

```text
stable/mainline
```

or from another target branch only after explicit user confirmation.

After packaging, inspect `BUILD_INFO.json` and confirm:

- `source_root` is `/Users/changdali/Documents/BioMedPilot`.
- `git_head` matches the intended branch HEAD.

## Old Branches

Old `codex/*` branches are historical references only. Do not directly merge them into long-lived dev branches or `stable/mainline`.

High-risk historical branches include:

```text
codex/bio-search-ui-main
codex/bioinformatics-safe-stage2
codex/ai-gateway-call-isolation-audit
```

If any historical branch contains useful material, review it file by file and extract only explicitly approved changes.

## Completion Checklist

After each development task:

- Run the corresponding module tests.
- Run compile checks:

```bash
python3 -m compileall -q app tests scripts
```

- Run the app smoke test:

```bash
QT_QPA_PLATFORM=offscreen python3 -m app.main --smoke-test
```

- Run full tests when the change crosses module boundaries, touches shared code, or prepares a merge-back:

```bash
python3 scripts/run_tests.py
```

- If the desktop entry point, packaging, app shell, settings, or user-facing bundle is affected, rebuild the app:

```bash
python3 scripts/package_app.py --output-dir /Users/changdali/Desktop --app-name BioMedPilot --smoke-test
```

- Check packaged `BUILD_INFO.json` for the expected `source_root` and `git_head`.
