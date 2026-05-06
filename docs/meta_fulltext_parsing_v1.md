# Meta PDF / Full-text Parsing v1

Stage M11 adds testing-level local PDF text extraction and parsing diagnostics.

## Active Service

- Service: `app/meta_analysis/services/fulltext_parsing_service.py`
- Parse result: `fulltext/parsed_fulltext/<record_id>_fulltext_parse_v1.json`
- Extracted text: `fulltext/extracted_text/<record_id>.txt`
- Section text: `fulltext/parsed_fulltext/<record_id>/sections/*.txt`
- Manifest: `fulltext/fulltext_parse_manifest_v1.json`

## Captured Fields

- parse status: `parsed` or `parse_failed`
- parser diagnostics and warnings
- page count when available
- title guess
- DOI candidates
- PMID candidates
- coarse text sections: abstract, methods, results, tables, references

## Governance

- Parsing creates auxiliary draft artifacts only.
- Parsing writes `record_parsed` audit events and `fulltext_parsing` draft governance events.
- Parsing does not write final extraction values.
- Parsing does not create screening decisions, quality assessment scores, analysis inputs, or PRISMA counts.

## Current Limitations

- This is testing-level extraction, not production PDF parsing.
- OCR is not implemented.
- PDF table extraction is not implemented.
- Section detection is heuristic and intended only to help manual review.
- Failed parsing writes diagnostics and leaves the workflow available for manual extraction.
