# Meta Analysis Internal Beta Test Checklist

Use this checklist for internal beta validation only.

- Start the app with `python3 -m app.main --smoke-test`.
- Confirm Meta Analysis workspace is visible.
- Import the Stage M mock sample and Stage W PubMed-derived realistic sample.
- Run Import -> Dedup -> Screening -> Full-text status -> Extraction -> Quality -> Analysis -> Figures -> Reporting.
- Confirm all generated reports say Developer Preview / testing.
- Confirm missing artifacts are warnings, not crashes.
- Confirm `project.json`, `data_manifest.json`, `artifact_manifest.json`, `task_manifest.json`, and `lineage_manifest.json` exist.
- Confirm `reports/report_manifest.json` exists.
- Confirm reproducibility package opens and contains manifests.
- Confirm PDF is shown as not implemented.
- Confirm Network Meta is shown as not implemented.
- Confirm AI suggestions cannot write formal data without human action.

