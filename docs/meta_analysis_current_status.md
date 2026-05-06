# Meta Analysis Current Status

## Module Positioning

Current version: `0.2.0-internal-beta.testing`.

Meta Analysis is currently a Developer Preview / testing module. It is not a production systematic review or pooled meta-analysis application.

No Meta Analysis workflow should be presented as production-ready. Connected features are intended for controlled developer preview testing and workflow stabilization.

## Connected Main Chain

The current testing chain is:

1. PICO / PICOS / PECO Workspace v2 draft and reviewer-confirmed protocol
2. Search strategy draft generation
3. Reviewer-confirmed PubMed execution
4. PubMed literature candidates preview and reviewer-selected handoff
5. Normalized Literature Library v2
6. Literature Import
7. Prepare Screening
8. Duplicate Review
9. Screening
10. Full-text eligibility
11. Extraction Pool
12. Manual Data Extraction UI v1 draft workspace
13. Quality Assessment Framework v1
14. Analysis Plan Builder v1 draft and reviewer-confirmed plan
15. Meta Statistics Engine v2 from reviewer-confirmed analysis plan
16. Analysis Preflight / Analysis-ready Dataset / Basic Testing Meta Analysis / Result Artifacts
17. Reporting Test Summary / PRISMA Summary / Formal Markdown/HTML/DOCX Report Draft / Reproducibility Exports
18. AI Suggestions Queue
19. AI-assisted Extraction Queue v1 suggestion workflow

## Implemented Testing Capabilities

- Literature Import supports NBIB / RIS / CSV smoke testing and registers imported literature records.
- Protocol supports testing-level research question, PICO, PICOS, and PECO draft capture.
- PICO / PICOS / PECO Workspace v2 generates editable Chinese research-question drafts, separates draft and confirmed protocol artifacts, records draft/edit/confirm events in audit and research governance, and keeps meta-analysis type as a candidate until reviewer confirmation.
- `app/meta_analysis/search/` is the active Meta-owned search layer for literature query strategy drafts.
- Search strategy generation builds PubMed, Web of Science, Embase, and CNKI query drafts from shared medical-language translation with `target_context="meta_analysis"`.
- Search Strategy Builder v2 reads M5 `meta_confirmed_protocol.v2` artifacts and generates versioned PubMed, Web of Science, Embase, Cochrane, CNKI, WanFang, and VIP draft strategies with Markdown/TXT exports and reviewer confirmation records.
- PubMed draft queries support MeSH and `tiab` terms.
- Reviewer-confirmed PubMed queries can execute real PubMed E-utilities search inside the Meta search layer and write a structured execution report.
- Web of Science, Embase, and CNKI remain draft-only; no real execution clients are implemented for them.
- PubMed search execution returns literature candidates only. It does not automatically import records into the literature library, run duplicate review, start screening, or update PRISMA counts.
- Reviewer-selected PubMed candidates can be handed off into the normalized Meta literature library with provenance, import batch metadata, research-governance audit, and dedup review preparation.
- PubMed candidate handoff imports only selected records; rejected and pending candidates are not imported. Imported candidates remain `screening_status=not_started` and `dedup_status=pending_review`.
- `LiteratureLibraryService` is the active normalized literature library layer. It writes `meta_literature_library.v2` records, `meta_literature_import_batch.v2` batches, record-level audit JSONL, and `meta_literature_library_manifest.v1`.
- PubMed selected candidates, NBIB, RIS, and CSV imports are bridged into the same normalized record schema with provenance and import batch metadata.
- Multi-source Literature Import v2 adds a Meta-owned file-import adapter path for PubMed XML/MEDLINE, WOS plain text/tab-delimited, EndNote/Zotero RIS, Embase RIS, Cochrane RIS, and CNKI-style local exports, all normalized through `LiteratureLibraryService`.
- Literature library diagnostics record missing DOI, missing PMID, missing abstract, missing year, incomplete author fields, and incomplete source information without crashing.
- Literature library query helpers support listing records, record lookup, and filtering by source type, PMID, DOI, title keyword, and import batch.
- Prepare Screening reads Literature Import output and writes normalized screening-ready records.
- Duplicate Review detects candidate duplicate groups and supports minimal manual deduplication decisions.
- Duplicate Review v2 reads the unified Literature Library v2, generates `meta_duplicate_review_queue.v2` duplicate groups, assigns red/yellow/gray risk levels, builds merge previews, records reviewer dedup decisions, and can export a separate deduplicated literature set without changing the source library.
- Title / Abstract Screening v2 can build a reviewer queue from the deduplicated literature set, or fall back to the normalized literature library when no deduplicated set exists. Queue creation is preview-only and does not count as a screening decision.
- Title / Abstract Screening v2 stores reviewer decisions as include / exclude / uncertain / needs review, requires structured exclusion reasons for exclusions, writes research-governance audit records, and keeps AI/model suggestions separate from final reviewer decisions.
- Exclusion Criteria Library v1 provides built-in project-level exclusion reasons with Chinese/English labels, title/abstract vs full-text applicability, user-selectable/custom reasons, and PRISMA reason mapping. It guides reviewer decisions but does not automatically exclude records.
- The older Screening service still supports minimal include / exclude / maybe testing decisions for compatibility.
- Full-text workflows support testing registries and full-text exclusion CSV export.
- Quality Assessment Framework v1 provides a Meta-owned quality tool registry, suggestion-only tool recommendations by Meta type / study design, study-level quality assessment records, domain-level ratings, reviewer notes/rationale, reviewer-completed status, CSV/JSON exports, audit/governance records, and a report-readable quality summary.
- Supported quality tools include ROB2, ROBINS-I, Newcastle-Ottawa Scale / NOS, QUADAS-2, JBI prevalence checklist, AHRQ cross-sectional checklist, Cochrane RoB generic, and GRADE summary placeholder.
- Quality ratings must be saved or completed by a reviewer. Tool recommendations and overall judgement helpers are suggestion-only and do not write final risk-of-bias conclusions.
- GRADE is a placeholder / summary draft only; no automated evidence certainty or final GRADE conclusion is generated.
- Analysis Plan Builder v1 reads reviewer-confirmed protocol, extraction schema defaults, manual extraction effect-row candidates, and quality assessment summary to generate `meta_analysis_plan_draft.v1` artifacts.
- Analysis Plan Builder v1 separates draft and reviewer-confirmed analysis plans, records audit/governance events, tracks included/excluded candidate effect rows, and warns on missing fields, multiple primary candidates, mixed effect measures, mixed adjusted/unadjusted effects, inconsistent outcome/timepoint, incomplete quality assessment, and low study count for Egger/funnel.
- Confirmed analysis plans are locked for later analysis-run consumption but do not automatically create analysis-ready datasets, run statistics, create final analysis results, update PRISMA, or generate medical interpretation.
- Meta Statistics Engine v2 runs only from `meta_confirmed_analysis_plan.v1`; without a confirmed analysis plan it refuses to run.
- Meta Statistics Engine v2 writes `meta_statistics_analysis_run.v2`, `meta_statistics_standardized_result.v2`, `meta_statistics_analysis_manifest.v2`, and analysis audit JSONL artifacts under `analysis/runs/`, `analysis/results/`, `analysis/analysis_manifest.json`, and `logs/analysis/analysis_audit.jsonl`.
- Meta Statistics Engine v2 supports testing-level binary OR/RR/RD, continuous MD/SMD, survival HR, prevalence/incidence proportion, correlation/Fisher z-style inputs, diagnostic 2x2 DOR/sensitivity/specificity-style outputs, fixed/random pooling, heterogeneity Q/I²/tau², subgroup summaries, leave-one-out, Egger/funnel data, and standardized result objects.
- Statistics Engine v2 results are explicitly marked Developer Preview / testing-level and do not write medical conclusions.
- Full-text Management v1 can create a manual retrieval registry from reviewer screening decisions, bind local PDFs, record DOI / PubMed / PMCID / publisher links, mark full text unavailable with a reason, and write audit/governance records. It does not fetch PDFs automatically, parse PDFs, or create full-text screening decisions.
- PDF / Full-text Parsing v1 can run testing-level local PDF text extraction, save extracted text, parse diagnostics, initial title / DOI / PMID candidates, and coarse abstract / methods / results / tables / references text sections. These artifacts are auxiliary and do not write final extraction, quality, analysis, or report conclusions.
- Data Extraction Schema Registry v1 provides ten testing-level extraction schema templates for binary, continuous, survival, prevalence/incidence, diagnostic 2x2, exposure-risk, biomarker difference, correlation, prognostic-factor, and dose-response Meta types. It stores required/optional fields, validation rules, effect-size mapping, analysis defaults, quality-tool recommendations, and report-template mapping.
- Extraction creates an extraction pool from included screening records and now supports testing-level structured ExtractionRecord save, validation, CSV export, and advanced method outcome structures for prevalence, correlation, and diagnostic basic data.
- Manual Data Extraction UI v1 adds a draft-only `literature record -> study unit -> effect row -> evidence` workspace. It stores study units, candidate effect rows, source evidence refs, validation reports, CSV templates/current exports/import-as-draft diagnostics, extraction audit JSONL, and research-governance events.
- Manual extraction effect rows keep raw group data separate from reported effect sizes, support first-pass binary, continuous, survival, and diagnostic 2x2 dynamic field groups, and treat `completed_by_user` as reviewer completion only, not as an analysis-ready dataset.
- Analysis runs readiness preflight, builds testing-level analysis-ready datasets from structured extraction records, supports basic testing pooled effects, prevalence / incidence proportion effects, Fisher z correlation effects, diagnostic basic 2x2 metrics, subgroup analysis, leave-one-out sensitivity analysis, basic Egger publication-bias testing, and exports forest/funnel plot PNG plus result table CSV.
- Reporting exports the older testing Markdown summary, testing PRISMA flow numbers, a formal Markdown/HTML/DOCX report draft, advanced method and advanced add-on summaries, supplementary CSV tables, a figure package ZIP, project snapshot metadata, and a reproducibility package ZIP; these are testing outputs, not production publication packages.
- AI-assisted Review supports a testing AI suggestion queue with pending / accepted / rejected / edited statuses. AI suggestions require explicit human review and apply action, and they do not directly overwrite screening, extraction, analysis, or report artifacts.
- AI-assisted Extraction Queue v1 can generate testing extraction effect-row suggestions from abstract/manual text or parsed full-text text, attach schema validation diagnostics, disease-guard metadata, confidence, and queue status. Accepted suggestions can be applied only as Manual Data Extraction UI v1 draft effect rows, not as final extraction or analysis-ready data.

## Not Implemented Yet

- Web of Science, Embase, and CNKI real online execution clients are not implemented.
- PubMed search results are not automatically imported into the literature library; reviewer selection is required before PubMed candidates are imported.
- PubMed search results are not automatically merged or silently deduplicated; selected imports only prepare a dedup review queue.
- PubMed search results are not automatically moved into title/abstract screening or PRISMA counting.
- PICO / PICOS / PECO Workspace v2 does not automatically confirm the final research question, execute PubMed, generate final search strategy, create screening decisions, or update PRISMA counts.
- Search Strategy Builder v2 does not run database searches, import literature, create screening artifacts, or update PRISMA counts. PubMed confirmation only marks the strategy as eligible for the existing explicit PubMed execution entry.
- Literature library import does not automatically create title/abstract screening decisions and does not update PRISMA artifacts.
- Duplicate Review v2 does not automatically delete records, merge records, create screening artifacts, or update PRISMA counts.
- Title / Abstract Screening v2 does not automatically include or exclude records. AI/model screening suggestions do not write final decisions, and queue creation alone does not update PRISMA screened / included / excluded counts.
- Exclusion Criteria Library v1 does not automatically create screening or full-text exclusion decisions. PRISMA reason counts still require real reviewer decision records.
- Full-text Management v1 does not automatically download full text, parse PDFs, perform full-text exclusion, create final included-study records, or update PRISMA full-text exclusion counts.
- PDF / Full-text Parsing v1 is not production PDF parsing. It does not run OCR, extract tables reliably, infer final data extraction values, or update screening / PRISMA / quality artifacts.
- Data Extraction Schema Registry v1 does not write final extraction values, does not validate real study data by itself, and does not create analysis-ready datasets.
- Manual Data Extraction UI v1 does not create analysis-ready datasets, does not run statistical analysis, does not promote AI/PDF parsing suggestions into final values, and does not update PRISMA counts. CSV import is draft-only and reports conflicts instead of silently overwriting existing rows.
- AI-assisted Extraction Queue v1 does not automatically write final extraction values. Pending, rejected, or edited suggestions cannot be applied. Accepted suggestions still apply only as manual extraction draft rows and require later reviewer confirmation before analysis use.
- Quality Assessment Framework v1 does not automatically score risk of bias, does not automatically determine GRADE certainty, does not create analysis-ready datasets, does not run statistical analysis, and does not update PRISMA counts.
- Analysis Plan Builder v1 does not automatically confirm analysis plans, does not create analysis-ready datasets, does not run statistical analysis, does not create final results, does not update PRISMA, and does not write medical discussion/conclusion text.
- Meta Statistics Engine v2 does not run without a confirmed analysis plan, does not modify extraction records, does not modify quality assessment, does not update PRISMA, does not create medical conclusions, and does not claim production-grade statistical validity.
- Production-level statistical validation, advanced diagnostic bivariate / HSROC models, network meta-analysis, meta-regression, trim-and-fill, and publication-ready result interpretation.
- Current pooled effects, prevalence/incidence, Fisher z, diagnostic 2x2, subgroup, leave-one-out, Egger, forest/funnel plot, and CSV outputs are testing-level implementations, not a production statistical platform.
- PRISMA diagram generation, production PDF reports, and publication-ready report packages are not complete.
- Automatic full-text acquisition, production PDF parsing, OCR, PDF table extraction, and automated full-text data extraction are not complete.
- Production risk of bias, automated GRADE judgement, multi-reviewer quality adjudication, and related production evidence-certainty workflow are not complete.
- Production-grade online adapters for all planned literature databases are not complete.
- Multi-source Literature Import v2 is file-import oriented; it does not implement WOS, Embase, CNKI, WanFang, VIP, or Cochrane online execution clients.
- Autonomous AI-assisted review, automatic final screening, automatic final extraction, and automatic final conclusions.
- Multi-reviewer adjudication, team workflow, and production audit trail.

## Why This Cannot Be Marked Production

- The current Analysis step has a basic testing statistics core, several advanced method MVP calculations, and common add-on analyses, but it is not production-grade statistical software.
- The current Reporting step exports Markdown/HTML/DOCX testing drafts and ZIP packages; production PDF reporting is not complete, and publication-ready reporting remains incomplete.
- ExtractionRecord form integration, Manual Data Extraction UI v1, analysis-ready dataset builder, basic pooled effects, forest plot PNG, and result table CSV exist at testing level only.
- Screening and Duplicate Review remain testing-level workflows. Title / Abstract Screening v2 adds reviewer-confirmed decisions and audit, but multi-reviewer adjudication and production screening operations are not complete.
- PubMed execution is reviewer-confirmed and auditable. Its results can hand off to the literature library only after explicit reviewer candidate selection, and they still do not automatically enter screening or PRISMA included/screened/full-text counts.
- WOS, Embase, and CNKI are still query drafts only.
- Full-text, quality, publication export, reproducibility package, and AI suggestion workflows are testing-level only.

## Next Priority

The current staged roadmap is implemented at Developer Preview / testing level. Next priorities should be stabilization, boundary hardening, UX hardening, statistical validation review, AI-assisted extraction queue, and production-readiness audit rather than marking workflows production-ready.
