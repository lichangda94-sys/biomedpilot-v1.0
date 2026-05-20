# UI Visual Style Guide v1

Date: 2026-05-20

Status: current visual style guide draft for UI-B1

Scope: Low-fidelity UIShell rebuild and future high-fidelity preparation

## 1. Purpose

This guide defines the first visual governance layer for UI rebuild work. It is not a Figma file, final brand guide, final Logo spec, or final App icon decision.

Use this guide to build UI-B1 tokens and primitives before page rebuild work.

## 2. Brand Hierarchy

Current target brand hierarchy:

| layer | value | rule |
|---|---|---|
| Visible primary brand | `萤火虫 / Firefly` | Use on Welcome and About after brand confirmation. |
| Product family / subtitle | `BioMedPilot / 医研智析` | May remain as subtitle and technical lineage. |
| Technical bundle name | `BioMedPilot` | Do not change during UI-B0-B9. Packaging decision belongs to UI-B10. |
| Developer status | `Developer Preview / 本地测试版` | Must remain visible in relevant shell/about/testing contexts. |

Do not replace App icon, Finder icon, or bundle display name until brand and resource decisions are confirmed.

## 3. Visual Direction

The UI is a professional biomedical research desktop workbench. It should feel quiet, precise, local-first, and work-focused.

Avoid:

- Marketing landing-page composition.
- Decorative hero gradients.
- Oversized cards for dense operational workflows.
- One-hue palettes.
- Production-like visual treatment for planned/testing/shell-only functions.
- Visible UI text explaining design or shortcuts.

Prefer:

- Dense but readable information hierarchy.
- Restrained contrast.
- Clear status chips.
- Compact action rows.
- Tables and forms that remain stable with long English or Spanish labels.
- Developer diagnostics collapsed away from ordinary flows.

## 4. Token Source Rule

UI-B1 must establish one token source. Existing multiple palettes and inline styles should stop expanding.

Minimum token groups:

- `brand.*`
- `color.*`
- `module.bioinformatics.*`
- `module.meta_analysis.*`
- `module.labtools.*`
- `status.*`
- `font.*`
- `space.*`
- `radius.*`
- `border.*`
- `shadow.*`
- `layout.*`
- `component.*`

## 5. Color Rules

Initial color policy:

- Keep first implementation light-mode only unless explicitly expanded.
- Do not let Bioinformatics, Meta Analysis, and LabTools rely only on one dominant hue.
- Reserve color for module identity, status, selection, focus, and warnings.
- Do not encode status by color alone.
- Status tokens must include background, border, text, optional icon, and semantic key.

Required status color groups:

- Developer Preview
- testing
- planned
- shell-only
- preflight-only
- blocked
- available
- not configured
- missing
- failed
- draft
- report-ready later

## 6. Typography Rules

Initial typography policy:

- Use stable font-size tokens, not viewport-scaled font sizes.
- Letter spacing remains `0`.
- Hero-scale type is reserved for Welcome only.
- Dashboard, Settings, Bioinformatics, Meta and LabTools pages use compact page-title and section-title sizes.
- Long labels must wrap or use tooltip/secondary text instead of shrinking unpredictably.

Minimum font tokens:

- `font.size.hero`
- `font.size.page_title`
- `font.size.section_title`
- `font.size.card_title`
- `font.size.body`
- `font.size.secondary`
- `font.size.caption`
- `font.weight.regular`
- `font.weight.medium`
- `font.weight.semibold`
- `font.line_height.body`

## 7. Spacing, Radius, and Layout

Rules:

- Cards should use 8px radius or less unless a later confirmed design system changes this.
- Icon buttons and fixed controls must have stable dimensions.
- Sidebar width must account for English and Spanish labels.
- Tables may use horizontal scroll rather than compressing scientific headers.
- Dashboard module cards must keep stable height when labels wrap.
- Settings secondary navigation must support grouped tabs or short labels plus descriptions.

Minimum layout tokens:

- `layout.window.min_width`
- `layout.window.min_height`
- `layout.sidebar.width`
- `layout.content.max_width`
- `layout.card.min_height`
- `layout.table.min_column_width`
- `space.xs/sm/md/lg/xl`
- `radius.control`
- `radius.card`
- `radius.panel`

## 8. Component Primitives

UI-B1 should create or standardize these primitives before page rebuild:

| primitive | required behavior |
|---|---|
| Button | role-based: primary, secondary, destructive, ghost, icon. Short labels only. |
| Status chip | semantic key, label, color, optional icon, tooltip. |
| Card | no nested cards; repeated items only. |
| Table | stable headers, empty state, horizontal overflow support. |
| Form field | label, help text, validation state, disabled state. |
| Tabs / segmented control | Settings and module internal grouping. |
| Empty state | title, body, action, optional illustration. |
| Developer diagnostic disclosure | collapsed by default, copy/export actions inside. |
| Resource status row | detect-first state, path/version/status/action. |
| Report/export status panel | draft/testing/report-ready gating. |

## 9. Page-Level Visual Guidance

| page_area | low_fidelity_now | high_fidelity_blocker |
|---|---:|---|
| Welcome | yes | Final brand/logo/welcome visual. |
| Dashboard | yes | LabTools icon, final module icon system. |
| Sidebar | yes | Final icon set optional. |
| About | yes | Brand copy and visual assets. |
| Settings | yes | Resource icons and status taxonomy. |
| Bioinformatics | yes as IA shell/gated states | B8.1/result schema and report/plot schemas. |
| LabTools | yes as shell after minimal boundary | LabTools runtime calibration and module icons. |
| Meta Analysis | yes as shell | Meta runtime calibration. |
| Result/Report/Export | yes as status shell | Report template, result artifact schema, provenance. |

## 10. Resource Rules

Resource inventory fields:

`resource_id / path / type / purpose / module / status / size / format / light_dark_policy / source / used_by / owner_decision_required`

Resource status values:

- `placeholder`
- `current`
- `legacy`
- `target-needed`
- `final`
- `orphan`
- `conflict`

Rules:

- Archive resources are reference only.
- New App icon cannot replace current icon before brand confirmation.
- LabTools module icon is a P0 Dashboard resource gap.
- Status icons, empty states, report/export icons and Settings resource icons are high-fidelity prerequisites.
- Packaging icon changes belong to UI-B10.

## 11. Accessibility and Text Fit

Required for UI-B1+:

- Text must not overlap.
- Buttons cannot depend on long sentence labels.
- Status chips must handle longer English/Spanish labels.
- Tooltips should carry long explanations.
- Tables and cards must remain stable when translated labels expand.
- Warning dialogs use short title, body, and action buttons.

## 12. UI-B1 Acceptance Criteria

UI-B1 can pass when:

- One token source exists.
- Core primitives use tokens.
- Status semantics have visual mapping.
- Sidebar, Dashboard and Settings can use primitives without adding new ad hoc styles.
- Existing UI smoke passes.
- No final Logo/App icon replacement is required.
