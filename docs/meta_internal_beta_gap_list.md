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
| UI workflow | Many Meta capabilities are implemented as page-state/service flows, but the desktop UI still needs a simpler step-by-step usable workflow | Major | Next stage should be UI Phase 1: Meta Analysis Usable Workflow UI |
| Extraction | Sample extraction values are validation seeds; real projects still require careful manual extraction and review | Major | Must remain clearly marked and auditable |
| Quality assessment | Quality assessment forms exist, but real reviewer ergonomics need more desktop UI polish | Major | Users should not need to inspect JSON |
| Report interpretation | Reports are internal beta Markdown/HTML/DOCX testing outputs, not journal-ready reports | Major | Formal PDF is not implemented |
| Statistical interpretation | Statistical core has reference tests, but outputs still require expert review and applicability warnings | Major | Do not describe results as final publication conclusions |
| Packaging | Desktop app is a local Python launcher bundle, not a standalone installer | Major | Target machine still needs Python/PySide6 availability |
| Full text | No automatic PDF download, OCR, institutional access, or publisher login workflow | Major | Only local link/copy/availability workflows are supported |
| Advanced methods | Network Meta, HSROC, meta-regression, advanced diagnostic models, and publication-grade PRISMA diagram are not implemented | Major | Placeholders must remain explicit |

## Non-Blocking Internal Beta Gaps

| Area | Gap | Severity | Notes |
| --- | --- | --- | --- |
| Protocol/search | Search strategies are draft/copyable text, not validated final search strategies | Minor | PubMed/WOS/CNKI/WanFang automation remains outside current internal beta scope |
| Literature import | RIS/NBIB/CSV import has diagnostics but still needs more real-world database export fixtures | Minor | Continue expanding fixtures from tester files |
| Duplicate review | Merge preview supports auditability, but high-throughput manual review UI needs polish | Minor | No automatic destructive merge should be added |
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

1. Make the Meta workflow dashboard the user's main route through the process.
2. Convert service/page-state capabilities into understandable desktop panels.
3. Keep every unfinished capability visibly labeled Developer Preview / testing.
4. Preserve all manifest, audit, lineage, and artifact references.
5. Do not add production claims or automatic full-text/AI/statistical shortcuts.
