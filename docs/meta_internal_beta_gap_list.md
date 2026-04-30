# Meta Internal Beta Gap List

Status: Developer Preview / testing.

This gap list summarizes what still blocks BioMedPilot Meta Analysis from being production or publication-grade software after AB14 acceptance.

## Internal Beta Candidate Status

The current build can be used for controlled internal testing through:

```text
/Users/changdali/Desktop/BioMedPilot.app
```

Current version identity:

```text
0.1.0-internal-beta · Developer Preview / testing
```

It should not be presented as production-ready clinical, statistical, or publication software.

## Blocking Gaps Before Broader User Testing

| Area | Gap | Severity | Notes |
| --- | --- | --- | --- |
| UI workflow | UI Phase 1A-1E now cover the main Meta workflow page states with Chinese copy, but detailed desktop controls still need usability testing and visual refinement | Major | Next stage should be internal UI acceptance testing with a small sample project |
| Extraction | Sample extraction values are validation seeds; real projects still require careful manual extraction and review; UI1D adds Chinese field labels but not a full grid editor | Major | Must remain clearly marked and auditable |
| Quality assessment | Quality assessment forms exist and UI1D adds Chinese labels, but real reviewer ergonomics need more desktop UI polish | Major | Users should not need to inspect JSON |
| Report interpretation | Reports are internal beta Markdown/HTML/DOCX testing outputs, not journal-ready reports | Major | Formal PDF is not implemented |
| Statistical interpretation | Statistical core has reference tests, but outputs still require expert review and applicability warnings | Major | Do not describe results as final publication conclusions |
| Packaging | Desktop app is a local Python launcher bundle, not a standalone installer | Major | Target machine still needs Python/PySide6 availability |
| Full text | No automatic PDF download, OCR, institutional access, or publisher login workflow | Major | Only local link/copy/availability workflows are supported |
| Advanced methods | Network Meta, HSROC, meta-regression, advanced diagnostic models, and publication-grade PRISMA diagram are not implemented | Major | Placeholders must remain explicit |

## Non-Blocking Internal Beta Gaps

| Area | Gap | Severity | Notes |
| --- | --- | --- | --- |
| Workflow dashboard | Chinese status and step labels are now available, but layout has not been visually polished beyond the internal beta baseline | Minor | Keep macOS-like simple layout; avoid a global theme rewrite |
| Protocol/search | Search strategies are draft/copyable text, not validated final search strategies | Minor | PubMed/WOS/CNKI/WanFang automation remains outside current internal beta scope |
| Literature import | Chinese import wizard page-state is available, but real-world database export fixtures should continue expanding | Minor | Keep parser behavior stable; do not add online retrieval in UI Phase 1B |
| Literature table | Chinese duplicate-risk labels are available, but table filtering, column preferences, batch tags, and batch actions are not implemented | Minor | Keep read-only behavior until reviewer workflows are clearer |
| Duplicate review | Merge preview and core decisions now have Chinese page-state labels, but high-throughput manual review still needs a denser comparison table | Minor | No automatic destructive merge should be added |
| Criteria / screening | Criteria and title/abstract screening now expose Chinese labels and progress copy, but real reviewer speed still needs richer desktop controls | Minor | Keep `needs_review` as a UI label unless the save service is deliberately extended |
| Full-text / extraction / quality | UI1D adds Chinese page-state labels, but full reviewer workflow still needs richer desktop controls | Minor | No automatic PDF download, OCR, or forced quality judgement |
| Analysis / reporting | UI1E adds Chinese page-state labels for analysis, PRISMA trace, and reports, but result selection and report preview need desktop usability testing | Minor | Formal PDF remains intentionally unimplemented |
| Figures | Forest/funnel outputs are testing artifacts, not publication-styled figures | Minor | Good enough for internal validation, not final manuscripts |
| Sample projects | Sample projects are compact validation fixtures rather than clinically curated example reviews | Minor | Keep this explicit in walkthroughs |

## Acceptance Evidence Available

- AB14 acceptance report: `docs/meta_dev_reports/stage_AB14_internal_beta_acceptance_report.md`
- Internal beta checklist: `docs/meta_internal_beta_acceptance_checklist.md`
- Known limitations: `docs/meta_known_limitations.md`
- Tester guide: `docs/tester_guide.md` and `docs/user_testing/tester_guide.md`
- Packaging notes: `docs/packaging.md`

## Next Stage

Proceed to UI Phase 1: Meta Analysis Usable Workflow UI.

Priority should be usability and clarity, not new statistical features:

1. Use the Chinese Meta workflow dashboard as the user's main route through the process.
2. Run an internal UI acceptance walkthrough across UI Phase 1A-1E using a small sample project.
3. Keep every unfinished capability visibly labeled Developer Preview / testing.
4. Preserve all manifest, audit, lineage, and artifact references.
5. Do not add production claims or automatic full-text/AI/statistical shortcuts.
