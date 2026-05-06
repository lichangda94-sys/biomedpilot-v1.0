# Meta Exclusion Criteria Library v1

Stage M9 adds a project-level exclusion criteria library for reviewer-controlled screening and PRISMA reason mapping.

## Active Service

- Service: `app/meta_analysis/services/exclusion_criteria_library_service.py`
- Library artifact: `criteria/exclusion_criteria_library_v1.json`
- PRISMA mapping artifact: `criteria/prisma_reason_map_v1.json`

## Built-in Reasons

The library includes common reasons such as Review, Meta-analysis, Conference abstract, Editorial, Letter, Comment, Case report, Animal study, Cell study, Non-original article, Wrong population, Wrong intervention / exposure, Wrong comparator, Wrong outcome, Insufficient data, Full text unavailable, Duplicate publication, Non-target language, Protocol only, and Preprint only.

Each reason stores:

- stable code
- English label
- Chinese label
- applicable stage: title/abstract and/or full text
- PRISMA reason mapping
- enabled / disabled status
- built-in vs custom marker

## Governance

- Saving a draft library writes a draft research-governance event.
- Confirming the library writes a reviewer confirmation event.
- The library does not automatically screen, exclude, or include records.
- PRISMA reason counts are derived from real reviewer decision records, not from the existence of the library.

## Integration

- Criteria page state exposes library status, reason counts, and PRISMA map path.
- Title / Abstract Screening v2 can show enabled title/abstract exclusion reasons from the library.
- Full-text workflows can reuse the same reason mapping in later stages.

## Current Limitations

- No multi-reviewer criteria approval workflow.
- No UI checkbox grid yet; current service and page state provide the data contract.
- No automatic PRISMA advancement from library creation or confirmation.
