# UI Route Feature Inventory

Date: 2026-05-29

Purpose: track every visible button, card, route, page, handler, runtime, artifact, and test before any feature is declared connected or migrated.

Allowed statuses:

`connected`, `partial`, `placeholder`, `empty-button`, `missing-handler`, `missing-target-page`, `old-page`, `figma/new`, `broken`, `not migrated`

Allowed page styles:

`figma/new`, `old`, `hybrid`, `placeholder`, `missing`, `unknown`

## Route Inventory

| Module | UI Text | Source UI Baseline | File | objectName/handler | Click Result | Target Page | Runtime | Test | Status | Page Style |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Shell | Welcome / enter local workspace | `9d4edf3` preview | needs audit | needs audit | needs audit | needs audit | none expected | needs audit | partial | unknown |
| Shell | About | `9d4edf3` preview | needs audit | needs audit | needs audit | needs audit | none expected | needs audit | partial | unknown |
| Shell | Settings | `9d4edf3` preview | needs audit | needs audit | needs audit | needs audit | needs audit | needs audit | partial | unknown |
| Project | Project Management | `9d4edf3` preview is regressed | needs source search | needs audit | image-only/regressed | missing complete project page | needs audit | missing | broken | missing |
| Bioinformatics | Module home buttons | `9d4edf3` preview visual only | needs audit | needs audit | needs audit | needs audit | needs audit | needs audit | not migrated | unknown |
| Meta Analysis | Module home buttons | `9d4edf3` preview visual only plus Phase 4 L3 separately | needs audit | needs audit | needs audit | needs audit | needs audit | needs audit | not migrated | unknown |
| LabTools | Module home buttons | `9d4edf3` preview visual only | needs audit | needs audit | needs audit | needs audit | needs audit | needs audit | not migrated | unknown |

## Audit Rules

- Every user-visible entry must have one row.
- Button existence alone is not connected.
- A row can be marked `connected` only when UI, handler, target page/runtime, output/artifact or state, test, and documentation all exist.
- `old-page` and `placeholder` must not be promoted to complete.
