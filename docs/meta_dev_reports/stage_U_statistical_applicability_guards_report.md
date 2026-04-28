# Stage U Statistical Applicability Guards Report

## Goal

Prevent testing statistical outputs from being silently interpreted as formal conclusions.

## Completed

- Added statistical applicability service.
- Analysis runs preserve applicability warnings and block configured applicability errors.
- Warnings cover random-effects small-study instability, OR/RR correction explanation, HR log-scale CI-to-SE, prevalence transformation, diagnostic basic limitations, and network meta not implemented.
- Advanced publication bias and funnel plot warnings are explicit for small study counts.

## Testing Status

Focused Stage U tests cover SMD blocking errors, random-effects warnings, network meta blocking, publication-bias/funnel warnings, and analysis_result warning persistence.

Validation completed on 2026-04-28:

- `python -m compileall -q .`: not available in local shell (`python` command missing).
- `pytest -q`: not available in local shell (`pytest` command missing).
- `/Users/changdali/Documents/model9/.venv/bin/python -m compileall -q .`: passed.
- `/Users/changdali/Documents/model9/.venv/bin/python -m pytest -q`: 273 passed.
- `/Users/changdali/Documents/model9/.venv/bin/python scripts/run_tests.py`: 273 passed.
- `python3 -m app.main --smoke-test`: passed.

## Known Limits

Applicability rules are conservative guardrails, not a substitute for statistical expert review.
