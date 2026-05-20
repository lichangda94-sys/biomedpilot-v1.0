# Bioinformatics GEO Long-Tail Candidate Intake Policy

Date: 2026-05-20

## Policy

New GEO long-tail terms default to a candidate queue. They must not enter shared core and must not be visible to Meta scope unless a separate reviewed decision explicitly allows it.

## Categories

- species
- assay
- data_format
- grouping
- treatment_status
- platform
- tissue
- cell_line
- metadata_field

## Batch Requirements

Every reviewed expansion batch must include an audit diff, scope isolation tests, GEO core regression tests, and manual review for ambiguous grouping or treatment terms.

Long-tail intake must not change the current GEO core audit status until a reviewed expansion is approved.
