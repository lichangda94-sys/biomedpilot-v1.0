# Meta Full-text Management v1

Stage M10 adds a manual full-text management layer for records that pass title / abstract screening.

## Active Service

- Service: `app/meta_analysis/services/fulltext_management_service.py`
- Registry artifact: `fulltext/fulltext_management_registry_v1.json`
- Existing attachment registry remains available at `attachments/attachment_registry.json`
- Existing full-text eligibility decisions remain separate from this management registry

## Supported Statuses

- `pdf_attached`
- `link_available`
- `full_text_unavailable`
- `needs_manual_retrieval`
- `parsed`
- `parse_failed`

M10 only manages these statuses. PDF parsing is reserved for the next stage.

## Supported Sources

- local PDF binding
- DOI link
- PubMed / PMID link
- publisher link
- PMCID / open-access link
- manual notes

## Governance

- Building the registry from reviewer screening decisions is a draft engineering action.
- PDF attachment, link recording, and unavailable-status changes require an actor and write audit plus research-governance events.
- No action in this service writes a full-text screening decision.
- No action in this service advances PRISMA full-text exclusion counts.

## Current Limitations

- No automatic PDF download.
- No institutional proxy or publisher login integration.
- No OCR, PDF parsing, or table extraction.
- No automatic full-text inclusion/exclusion decision.
