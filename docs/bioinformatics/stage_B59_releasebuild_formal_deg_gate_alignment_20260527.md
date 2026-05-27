# B59 ReleaseBuild Formal DEG Gate Script Alignment

## Audit

B58 identified one major issue: `scripts/releasebuild_formal_deg_gate.py` was absent in this Bioinformatics worktree, so the ReleaseBuild formal DEG gate command could not run here.

## Implementation

- Added `scripts/releasebuild_formal_deg_gate.py`.
- The script supports `--skip-full-tests` and `--json-output`.
- In full mode it runs `tests/bioinformatics` and `tests/ui`.
- In all modes it runs the formal DEG runtime validation through `app.main --bio-formal-deg-runtime-check` and embeds the direct runtime payload.
- Missing dependencies remain graceful blockers through the existing runtime validation contract.

## Boundary

The script does not activate new DEG methods and does not install or bundle dependencies.

## Validation

- `python3 scripts/releasebuild_formal_deg_gate.py --skip-full-tests --json-output /tmp/biomedpilot_deg_production_gate.json`: passed.
