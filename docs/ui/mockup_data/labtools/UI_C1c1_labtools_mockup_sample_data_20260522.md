# UI-C1c1 LabTools Mockup Sample Data

Date: 2026-05-22

This file provides non-production example data for LabTools P0 wireframes. Values are only for UI layout, field naming, warning placement, and empty/result state planning. They must not be used as validated experiment protocols, clinical guidance, production reports, or saved records.

## 1. Quick Dilution Example

Purpose: Quick Calculator input/result layout.

| Field | Example Value |
| --- | --- |
| Calculator | Dilution |
| Stock concentration | 10 mM |
| Final concentration | 100 uM |
| Final volume | 2 mL |
| Solvent / diluent | PBS |
| Review note | Confirm solvent compatibility before use. |

Expected UI result preview:

| Result Field | Example Value |
| --- | --- |
| Stock volume | 20 uL |
| Diluent volume | 1980 uL |
| Result status | testing helper / user review required |

Warnings to show when applicable:

- Concentration units must be compatible before calculation.
- Very small stock volume should show pipetting precision warning.
- Copy result is allowed; save/history requires future storage adapter where applicable.

## 2. Dynamic Formula Solver Example

Purpose: Formula Solver form, solve-target selector, result card, and warning layout.

Formula:

```text
C1 * V1 = C2 * V2
```

| Field | Example Value |
| --- | --- |
| Solve target | V1 |
| C1 | 5 mg/mL |
| C2 | 0.25 mg/mL |
| V2 | 10 mL |
| Unit mode | concentration-volume |

Expected UI result preview:

| Result Field | Example Value |
| --- | --- |
| V1 | 0.5 mL |
| Remaining volume | 9.5 mL |
| Review note | Confirm density and concentration basis if mixing mass/volume units. |

## 3. PBS Reagent Template Example

Purpose: Reagent Template List and Template Editor side panel.

Template summary:

| Field | Example Value |
| --- | --- |
| Template name | PBS 1x |
| Category | buffer |
| Target volume | 1000 mL |
| pH target | 7.40 |
| Component count | 4 |
| Last edited | mockup-only timestamp |

Components:

| Component | Type | Amount | Unit | Notes |
| --- | --- | ---: | --- | --- |
| NaCl | solid | 8.00 | g | analytical grade |
| KCl | solid | 0.20 | g | optional vendor field |
| Na2HPO4 | solid | 1.44 | g | hydrate form must be explicit in real use |
| KH2PO4 | solid | 0.24 | g | pH adjustment may be required |

Template editor validation examples:

- Missing component unit should block save.
- Unknown component type should show controlled dropdown warning.
- Store path must come from BioMedPilot storage adapter; do not default to `~/.labtools`.

## 4. Reagent Preparation Run Example

Purpose: Preparation Run screen with request, calculated preparation, review notice, and adapter-needed storage boundary.

| Field | Example Value |
| --- | --- |
| Template | PBS 1x |
| Target volume | 500 mL |
| Operator | demo user |
| Preparation date | mockup-only date |
| Lot note | optional |
| pH measured | 7.36 |
| pH adjusted | 7.40 |

Calculated component preview:

| Component | Required Amount | Unit | User Check |
| --- | ---: | --- | --- |
| NaCl | 4.00 | g | unchecked |
| KCl | 0.10 | g | unchecked |
| Na2HPO4 | 0.72 | g | unchecked |
| KH2PO4 | 0.12 | g | unchecked |

Actions:

- Copy preparation summary: allowed in mockup.
- Save preparation record: adapter-needed until BioMedPilot storage root is wired.
- Export record: adapter-needed file picker boundary.

## 5. Western Blot Loading Sample Table

Purpose: Western Blot Loading calculator table layout.

Configuration:

| Field | Example Value |
| --- | --- |
| Target protein per lane | 20 ug |
| Sample buffer | 4x |
| Final loading volume | 20 uL |
| Reducing agent | yes |
| Denaturation note | user review required |

Samples:

| Sample ID | Protein Concentration | Unit | Replicate | Notes |
| --- | ---: | --- | --- | --- |
| S1 | 2.0 | ug/uL | A | control |
| S2 | 1.5 | ug/uL | A | treatment low |
| S3 | 0.8 | ug/uL | A | treatment high |

Expected result preview:

| Sample ID | Sample Volume | Buffer Volume | Water Volume | Warning |
| --- | ---: | ---: | ---: | --- |
| S1 | 10.0 uL | 5.0 uL | 5.0 uL | none |
| S2 | 13.3 uL | 5.0 uL | 1.7 uL | none |
| S3 | 25.0 uL | 5.0 uL | -10.0 uL | exceeds final volume; review required |

## 6. SDS-PAGE Gel Example

Purpose: SDS-PAGE Gel template, batch calculation, safety/review notice, and export boundary.

| Field | Example Value |
| --- | --- |
| Gel format | mini gel |
| Number of gels | 2 |
| Resolving gel | 10% |
| Stacking gel | 4% |
| Resolving gel volume | 8 mL each |
| Stacking gel volume | 3 mL each |

Result preview:

| Section | Component | Amount | Unit | Notes |
| --- | --- | ---: | --- | --- |
| Resolving | Acrylamide/Bis | 2.67 | mL | example only |
| Resolving | Tris buffer | 2.00 | mL | pH must match template |
| Resolving | SDS | 80 | uL | example only |
| Stacking | Acrylamide/Bis | 0.40 | mL | example only |
| Stacking | Tris buffer | 0.75 | mL | pH must match template |

Boundary:

- XLSX export button can be shown as adapter-needed until UI file picker is connected.
- Template JSON import/export can be shown as future P1.
- Safety/review notice must remain visible.

## 7. BCA OD Matrix Example

Purpose: BCA / OD MVP Boundary screen. This is not formal ELISA and not a production save/export flow.

OD matrix, 8 x 12:

| Row | C1 | C2 | C3 | C4 | C5 | C6 | C7 | C8 | C9 | C10 | C11 | C12 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| A | 0.052 | 0.051 | 0.121 | 0.125 | 0.243 | 0.239 | 0.491 | 0.502 | 0.736 | 0.744 | 0.918 | 0.925 |
| B | 0.049 | 0.053 | 0.119 | 0.126 | 0.247 | 0.241 | 0.488 | 0.497 | 0.739 | 0.746 | 0.921 | 0.929 |
| C | 0.060 | 0.058 | 0.132 | 0.130 | 0.251 | 0.248 | 0.500 | 0.506 | 0.760 | 0.754 | 0.940 | 0.936 |
| D | 0.055 | 0.057 | 0.128 | 0.131 | 0.249 | 0.252 | 0.503 | 0.509 | 0.755 | 0.758 | 0.938 | 0.941 |
| E | 0.071 | 0.069 | 0.211 | 0.215 | 0.318 | 0.322 | 0.456 | 0.461 | 0.612 | 0.619 | 0.804 | 0.811 |
| F | 0.073 | 0.070 | 0.209 | 0.218 | 0.315 | 0.326 | 0.459 | 0.465 | 0.618 | 0.622 | 0.808 | 0.816 |
| G | 0.066 | 0.067 | 0.198 | 0.202 | 0.300 | 0.306 | 0.442 | 0.449 | 0.590 | 0.596 | 0.780 | 0.784 |
| H | 0.064 | 0.068 | 0.195 | 0.205 | 0.303 | 0.309 | 0.445 | 0.452 | 0.594 | 0.601 | 0.781 | 0.789 |

Annotation example:

| Wells | Role | Concentration | Unit |
| --- | --- | ---: | --- |
| A1:B2 | blank | 0 | ug/mL |
| A3:B12 | standard | 25-2000 | ug/mL |
| E1:H12 | sample | unknown | sample-specific |

Linear-fit summary preview:

| Field | Example Value |
| --- | --- |
| Fit model | linear |
| R2 | 0.992 |
| Slope | mockup-only |
| Intercept | mockup-only |
| Warnings | low R2 threshold warning if configured; high CV warning if replicate mismatch |

Disabled / adapter-needed:

- Save BCA record: disabled until BCA record store exists.
- Export BCA result: disabled or adapter-needed until export model exists.
- ELISA action: not shown as active analysis.
