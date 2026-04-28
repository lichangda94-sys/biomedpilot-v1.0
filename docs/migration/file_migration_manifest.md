# File Migration Manifest

| 来源路径 | 目标路径 | 操作 | 原因 | 风险 |
|---|---|---|---|---|
| `/Users/changdali/Documents/New project 2/README.md` | `/Users/changdali/Documents/BioMedPilot/README.md` | copy | Current unified project README. | Low. |
| `/Users/changdali/Documents/New project 2/pyproject.toml` | `/Users/changdali/Documents/BioMedPilot/pyproject.toml` | copy | Current package/test config. | Low. |
| `/Users/changdali/Documents/New project 2/requirements.txt` | `/Users/changdali/Documents/BioMedPilot/requirements.txt` | copy | Current dependency note. | Low. |
| `/Users/changdali/Documents/New project 2/app/` | `/Users/changdali/Documents/BioMedPilot/app/` | copy | Current app shell, workspaces, shared layer, and embedded legacy snapshots. | Medium: includes legacy snapshots; exclude caches. |
| `/Users/changdali/Documents/New project 2/docs/` | `/Users/changdali/Documents/BioMedPilot/docs/` | copy | Current architecture, migration, and user-testing docs. | Low. |
| `/Users/changdali/Documents/New project 2/tests/` | `/Users/changdali/Documents/BioMedPilot/tests/` | copy | Current unified tests. | Low. |
| `/Users/changdali/Documents/New project 2/scripts/` | `/Users/changdali/Documents/BioMedPilot/scripts/` | copy | Current run/test/package scripts. | Low. |
| `/Users/changdali/Documents/New project 2/assets/` | `/Users/changdali/Documents/BioMedPilot/assets/` | copy | Current final asset structure. | Low. |
| `/Users/changdali/Documents/New project 2/examples/` | `/Users/changdali/Documents/BioMedPilot/examples/` | copy | Current examples structure. | Low. |
| `/Users/changdali/Documents/New project 2/project_storage/` | `/Users/changdali/Documents/BioMedPilot/project_storage/` | copy | Runtime storage structure. | Low if only structure/gitkeep copied; generated JSON ignored. |
| `/Users/changdali/Documents/model9/` | `/Users/changdali/Documents/BioMedPilot/archive/legacy_sources/model9/` | copy | Preserve latest Meta source outside active imports. | Medium: source tree has uncommitted changes; exclude `.git`, venv, dist/build, caches. |
| `/Users/changdali/Documents/New project/` | `/Users/changdali/Documents/BioMedPilot/archive/legacy_sources/bioinformatics_project/` | copy | Preserve latest Bioinformatics source outside active imports. | Medium: exclude `.git`, venv, caches. |
| `/Users/changdali/Documents/model9-main-clean/` | `/Users/changdali/Documents/BioMedPilot/archive/duplicate_candidates/model9-main-clean.txt` | needs_review | Older baseline and duplicate candidate. | Medium: full copy may be unnecessary; keep source path and reason. |
| `/Users/changdali/Documents/model9-module4-analysis-profiles/` | `/Users/changdali/Documents/BioMedPilot/archive/duplicate_candidates/model9-module4-analysis-profiles.txt` | needs_review | Old phase snapshot, many duplicate files. | Low if logged only. |
| `/Users/changdali/Documents/model9-module4-rule-consumer/` | `/Users/changdali/Documents/BioMedPilot/archive/duplicate_candidates/model9-module4-rule-consumer.txt` | needs_review | Old phase snapshot, many duplicate files. | Low if logged only. |
| `/Users/changdali/Documents/model9-module4-rule-service/` | `/Users/changdali/Documents/BioMedPilot/archive/duplicate_candidates/model9-module4-rule-service.txt` | needs_review | Old phase snapshot, many duplicate files. | Low if logged only. |
| `/Users/changdali/Documents/model9-module5-profile-consumption/` | `/Users/changdali/Documents/BioMedPilot/archive/duplicate_candidates/model9-module5-profile-consumption.txt` | needs_review | Old phase snapshot, many duplicate files. | Low if logged only. |
| `/Users/changdali/Documents/model9-module6-profile-reporting/` | `/Users/changdali/Documents/BioMedPilot/archive/duplicate_candidates/model9-module6-profile-reporting.txt` | needs_review | Old phase snapshot, many duplicate files. | Low if logged only. |
| `/Users/changdali/Documents/model9-pico-search-foundation/` | `/Users/changdali/Documents/BioMedPilot/archive/duplicate_candidates/model9-pico-search-foundation.txt` | needs_review | Old phase snapshot, may contain PICO/Search references. | Medium: review before discarding. |
| `/Users/changdali/Documents/model9-ui-reporting-summary-data/` | `/Users/changdali/Documents/BioMedPilot/archive/duplicate_candidates/model9-ui-reporting-summary-data.txt` | needs_review | Old phase snapshot for UI/reporting. | Low if logged only. |
| `/Users/changdali/Documents/model9/.venv` | none | ignore | Large virtual environment, reproducible. | Do not copy. |
| `/Users/changdali/Documents/model9/.venv-meta` | none | ignore | Large virtual environment, reproducible. | Do not copy. |
| `/Users/changdali/Documents/New project/.venv` | none | ignore | Large virtual environment, reproducible. | Do not copy. |
| `/Users/changdali/Documents/model9/dist` | none | ignore | Generated package output. | Do not copy into active project. |
| `/Users/changdali/Documents/model9/build` | none | ignore | Generated build output. | Do not copy into active project. |
| `/Users/changdali/Documents/AO_PI_染色拍照记录表模板.xlsx` | none | ignore | Personal/research spreadsheet template, not app code. | Do not migrate. |
| `/Users/changdali/Documents/EndNote` | none | ignore | External app/plugin data. | Do not migrate. |
| `/Users/changdali/Documents/Paradox Interactive` | none | ignore | Unrelated application data. | Do not migrate. |
| `/Users/changdali/Documents/GitHub` | none | needs_review | Generic folder; no BioMedPilot-specific source identified in current scan. | User should identify any relevant repo before migration. |

