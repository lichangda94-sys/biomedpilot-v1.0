# Feature Asset Inventory

Date: 2026-05-29

Purpose: track the best source, UI state, runtime state, artifact evidence, tests, MainLine migration state, and risk for every BioMedPilot feature asset.

Allowed page styles:

`figma/new`, `old`, `hybrid`, `placeholder`, `missing`, `unknown`

Allowed MainLine states:

`not migrated`, `scoped planned`, `migrated`, `validated`, `blocked`

## Asset Inventory

| Feature ID | Module | Feature Name | Best Source Branch | Best Source Commit | UI Shell Connected? | Feature Page Exists? | Page Style | Handler | Runtime/service | Artifact | Test | Test Result | MainLine Status | Risk |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SHELL-WELCOME | Shell | Welcome / local workspace entry | `codex/integration-labtools-ui-c2-carryover` | `9d4edf3` | yes in preview | yes in preview | unknown | needs audit | none expected | state/UI only | needs audit | missing | not migrated | Source baseline is accepted visually but not in MainLine. |
| SHELL-ABOUT | Shell | About | `codex/integration-labtools-ui-c2-carryover` | `9d4edf3` | yes in preview | yes in preview | unknown | needs audit | none expected | state/UI only | needs audit | missing | not migrated | Must not bring unrelated LabTools/Bio changes. |
| SHELL-SETTINGS | Shell | Settings / release gates | `codex/integration-labtools-ui-c2-carryover` | `9d4edf3` | yes in preview | yes in preview | unknown | needs audit | dependency gates need audit | state/gate | needs audit | missing | not migrated | Gate semantics must stay developer-preview/testing where applicable. |
| PROJECT-MGMT | Project | Project Management | needs source search | needs audit | regressed in `9d4edf3` preview | no complete current evidence | missing | missing | needs audit | none | missing | missing | blocked | Image-only preview is not complete Project Management. |
| BIO-HOME | Bioinformatics | Module home and button routes | needs audit | needs audit | yes in preview | unknown | unknown | needs audit | needs audit | needs audit | needs audit | missing | not migrated | Buttons may be empty or missing target pages. |
| META-HOME | Meta Analysis | Module home and button routes | needs audit plus Phase 4 L3 separately | needs audit | yes in preview | unknown | unknown | needs audit | needs audit | needs audit | needs audit | missing | not migrated | Must not overwrite Phase 4 L3 proof. |
| LAB-HOME | LabTools | Module home and button routes | needs audit | needs audit | yes in preview | unknown | unknown | needs audit | needs audit | needs audit | needs audit | missing | not migrated | Many pages may be old/hybrid and require reconciliation. |

## Rules

- No feature outside this inventory can be described as accepted into MainLine.
- A feature with no runtime/service or artifact evidence cannot be marked complete.
- A feature with only a visible button must be marked `partial`, `empty-button`, or equivalent in the route inventory.
- MainLine status requires migration evidence, tests, and audit.
