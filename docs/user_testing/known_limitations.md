# Known Limitations

- This build is for first-round user experience testing, not final analysis work.
- The Dashboard, project creation, recent projects, workspace switching, status labels, and Testing Mode are the main things to test.
- Meta Literature Import is connected for NBIB / RIS / CSV smoke testing.
- Meta Prepare for Screening is connected for imported JSON output, but it does not perform manual duplicate decisions yet.
- Meta Duplicate Review can generate duplicate candidate group summaries, but manual keep/merge decisions are not implemented yet.
- Bioinformatics and Meta Analysis legacy code is preserved, but not all legacy screens are embedded in the unified shell yet.
- Features marked `待接入` or `暂未开放` should not be tested as completed workflows.
- Formal differential expression, enrichment, correlation, survival, and complete Meta statistics are not exposed as real runs in this build.
- Report export is not a complete end-to-end workflow yet.
- Manual duplicate decisions, Screening, Extraction, Analysis, and Reporting should not be treated as complete workflows yet.
- Packaging/installer generation is still a placeholder.
- Some automated GUI checks are intentionally non-window tests because Qt window creation may not work in every local test environment.
