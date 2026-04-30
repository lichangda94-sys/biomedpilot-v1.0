# Meta Analysis Known Limitations

Current status: Developer Preview / testing.

- Not production clinical or statistical software.
- Formal PDF export is not implemented for internal beta.
- Network meta-analysis is a placeholder and must not run as a formal result.
- Diagnostic methods are basic only; bivariate models and HSROC are not implemented.
- Full-text PDF management and extraction remain testing workflows.
- Extraction and quality assessment still require human data entry and review.
- AI suggestions cannot directly overwrite formal screening, extraction, analysis, or report data.
- Stage W realistic sample uses PubMed-derived metadata, but binary extraction values are manually seeded validation data.
- AB13 internal beta sample projects commit source inputs and expected manifests only; generated reports, figures, and ZIP packages must be produced in temporary project directories.
- The treatment-effect and biomarker sample extraction values are validation seeds, not clinically curated datasets.
- The Mac app bundle smoke target is suitable for internal beta checks only; it is not a standalone production installer.
- AB14 internal beta acceptance verifies source/package metadata and sample-project artifact generation, but it does not convert any Meta capability to production status.
- `/Users/changdali/Desktop/BioMedPilot.app` is the unified desktop testing entry on this machine; if it is rebuilt from a newer commit, rerun packaged smoke before giving it to testers.
