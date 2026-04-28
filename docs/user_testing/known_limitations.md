# Known Limitations

- This build is for first-round user experience testing, not final analysis work.
- The Dashboard, project creation, recent projects, workspace switching, status labels, and Testing Mode are the main things to test.
- Meta Literature Import is connected for NBIB / RIS / CSV smoke testing; other Meta workflow steps are still status entries.
- Bioinformatics and Meta Analysis legacy code is preserved, but not all legacy screens are embedded in the unified shell yet.
- Features marked `待接入` or `暂未开放` should not be tested as completed workflows.
- Formal differential expression, enrichment, correlation, survival, and complete Meta statistics are not exposed as real runs in this build.
- Report export is not a complete end-to-end workflow yet.
- Duplicate Review, Screening, Extraction, Analysis, and Reporting should not be treated as complete workflows yet.
- Packaging/installer generation is still a placeholder.
- Some automated GUI checks are intentionally non-window tests because Qt window creation may not work in every local test environment.
