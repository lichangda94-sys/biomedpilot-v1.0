# BioMedPilot Meta UI Acceptance Report

## Scope

- Branch: `feature/unified-workbench-shell`
- Baseline commit tested: `163300d feat(meta-ui): add macOS app launcher for meta dashboard`
- Acceptance focus: Meta Analysis desktop UI launch readiness, dashboard completeness, sidebar workflow coverage, toolbar safety, and macOS launcher validation.
- Out of scope: bioinformatics UI, statistical backend expansion, advanced export generation, and unrelated dirty files outside `app_meta`, `packaging`, `assets`, and docs.

## Launch Methods Tested

| Launch method | Result | Notes |
| --- | --- | --- |
| `./.venv/bin/python app_meta/main.py` | Blocked by local Qt runtime | PySide6 imports, but this workstation reports: `Could not find the Qt platform plugin "cocoa"` from the PySide6 plugin path. |
| `packaging/meta_app_launcher.command` | Script valid; app blocked by same Qt runtime | Launcher now prints a clear reinstall instruction when Qt platform startup fails. |
| `python packaging/create_meta_app_bundle.py` | Passed | Regenerates `dist/BioMedPilot Meta.app`. |
| `dist/BioMedPilot Meta.app/Contents/MacOS/BioMedPilotMeta` | Bundle executable valid; app blocked by same Qt runtime | The generated launcher prints an actionable error and attempts a macOS dialog for Finder launches. |

Manual validation step after repairing PySide6/Qt locally:

```bash
python packaging/create_meta_app_bundle.py
open "dist/BioMedPilot Meta.app"
```

If the `cocoa` plugin error appears, reinstall PySide6 in the project virtual environment:

```bash
./.venv/bin/python -m pip install --force-reinstall PySide6
```

## Dashboard Audit

Present:

- Top metric cards: `检索文献数`, `纳入研究数`, `当前结局`, `异质性 I²`
- Central forest plot card using demo study rows and pooled estimate
- Right PRISMA workflow card
- Right analysis settings card
- Right GRADE overview card
- Bottom RoB 2.0 overview card
- Bottom recent outputs card
- Left sidebar project progress card

Status: dashboard structure is complete for first-round visual review once the local Qt runtime can launch the app.

## Sidebar Navigation Audit

Sidebar items present:

- `首页`
- `PICO/Search`
- `文献导入`
- `去重审查`
- `筛选`
- `数据提取`
- `分析设置`
- `Forest Plot`
- `Funnel Plot`
- `Reporting`
- `项目管理`

Implemented workflow pages:

- Dashboard
- PICO/Search
- Literature Import
- Deduplication
- Screening
- Data Extraction
- Forest Plot
- Funnel Plot
- Reporting
- Project Management

Placeholder status:

- `分析设置` remains a polished placeholder page with a title, short description, and `Coming soon / 待开发`.

## Toolbar Audit

Toolbar actions reviewed:

- `新建项目`
- `打开`
- `保存`
- `导出`
- `分享`
- `报告`
- search box

Current behavior:

- New/Open/Save are wired to local project persistence.
- Export and unsupported toolbar actions use safe status messages and logging where appropriate.
- Search is visual placeholder only.
- No toolbar action expands statistical or backend scope.

## User-Facing Content Audit

Developer-facing terms searched:

- `Task ID`
- `Result ID`
- `Runner`
- `Materialize`
- `Debug`
- `Payload`
- `Trace`
- `Raw JSON`
- `Developer`
- `Backend Job`

Result:

- No developer/debug terms appear in normal dashboard or workflow pages.
- The only `Developer` label is `Developer diagnostics` in Project Management, intentionally collapsed.

Bioinformatics-specific terms searched with word boundaries:

- `GEO`
- `TCGA`
- `GTEx`
- `differential expression`
- `enrichment`
- `survival analysis`
- `expression matrix`
- `gene`
- `pathway`

Result:

- No bioinformatics-specific content appears in the normal Meta Analysis app UI.

## Validation Commands

Passed:

```bash
./.venv/bin/python -m compileall -q app_meta packaging
zsh -n packaging/meta_app_launcher.command
python packaging/create_meta_app_bundle.py
plutil -lint "dist/BioMedPilot Meta.app/Contents/Info.plist"
zsh -n "dist/BioMedPilot Meta.app/Contents/MacOS/BioMedPilotMeta"
git diff --check -- app_meta packaging docs assets
```

Additional UI-safe checks:

- Dashboard state and sidebar item structure check: passed.
- Meta UI bioinformatics contamination search: passed.
- Developer-facing normal UI search: passed, with collapsed Project Management diagnostics noted.

## Known Limitations

- This local workstation currently cannot complete a live Qt window launch because the PySide6 `cocoa` platform plugin fails to initialize.
- The generated `.app` is unsigned and not notarized by design.
- `dist/` is generated locally and must remain uncommitted.
- Export buttons are placeholders unless already backed by local project metadata logging.
- Search box remains a visual placeholder.
- `分析设置` is still a polished placeholder page.

## Readiness Conclusion

The Meta Analysis UI shell is structurally ready for first-round visual and workflow testing by a non-developer user after the local PySide6/Qt runtime issue is repaired. The app bundle can be regenerated, launchers are syntactically valid, dashboard/workflow pages are present, and no bioinformatics or normal-page developer/debug content was found.

## PICO/Search Layout Repair

Date: 2026-04-27

Before:

- PICO/Search used a page header outside the scroll region plus an inner scroll region for only the left form column.
- The right readiness card stretched vertically and looked mostly empty.
- Search term fields could appear compressed at smaller window sizes.
- Toolbar used a report dropdown, which could appear as a dangling arrow/control in the top row.
- Deduplication and Screening had initialization-order issues that could raise errors while constructing those pages.

After:

- PICO/Search now uses one page-level `QScrollArea`.
- The page is a stable two-column layout: a flexible left workflow column and a fixed-width right support column.
- Left cards are grouped as Research Question, PICO Framework, Review Type and Databases, Search Terms, and Boolean Query Preview.
- Right column contains compact Protocol readiness, Search strategy tips, and Actions cards.
- Search term fields and PICO fields now have explicit readable heights.
- The report dropdown was replaced with a normal toolbar button to keep the toolbar aligned in a single row.
- Deduplication and Screening selection initialization was deferred until detail widgets exist.

Current status:

- PICO/Search is ready for first-round visual review once the local Qt runtime launches successfully.
- No real database search was added.
- No bioinformatics labels were introduced.
- Remaining limitation: live GUI validation is still dependent on the local PySide6/macOS `cocoa` runtime behaving correctly.
