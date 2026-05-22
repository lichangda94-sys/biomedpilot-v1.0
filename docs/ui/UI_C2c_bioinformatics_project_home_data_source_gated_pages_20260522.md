# UI-C2c Bioinformatics Project Home + Data Source Gated Pages

## 1. Scope

This stage implemented gated PySide UI updates for the Bioinformatics Project Home and Data Source pages only.

In scope:
- Project Home workflow labels, gate summary, and readiness cards.
- Data Source gated layout for GEO, TCGA, GTEx, and Local File.
- Current-project recent import/status preview tables.
- UI tests for gated source cards, disabled legacy actions, and no fake result state.

Out of scope:
- Formal DEG execution.
- ORA / GSEA execution.
- KM / log-rank / Cox / survival execution.
- GEO / TCGA / GTEx download.
- Real local file import.
- Fake expression matrix, fake result, fake plot, report generation, or export.
- Packaged app, App icon, Finder icon, `.icns`, `Info.plist`, LaunchServices, signing, or desktop app replacement.

## 2. Project Home Updates

The Project Home page now shows the target 7-step Bioinformatics flow:

1. Project Home / 项目首页
2. Data Source / 数据来源
3. Data Check & Preparation / 数据检查与准备
4. Group & Design / 分组与设计
5. Analysis Tasks / 分析任务
6. Result & Report / 结果与报告
7. Report Export / 报告导出

The top status copy was changed to `Project Open / Developer Preview / 本地测试版`.

Added summary cards:

| card | purpose | boundary |
|---|---|---|
| Data Readiness | Shows that registered/imported sources still require Data Check & Preparation | Does not claim formal input readiness |
| Analysis Readiness | Shows DEG / ORA / GSEA / KM / Cox actions disabled | Does not enable executors |
| Gate Summary | Shows result entry count and report/export not-ready state | Does not create report-ready or export-ready state |

## 3. Data Source Updates

The normal-user Data Source page now exposes exactly four main source cards:

| source | allowed UI action | blocked action |
|---|---|---|
| GEO | Select / configuration preview | Download, analysis |
| TCGA | Select / configuration preview | TCGA+GTEx auto merge, analysis |
| GTEx | Select / configuration preview | TCGA+GTEx auto merge, analysis |
| Local File | Select / configuration preview | Real local import, analysis |

`External Result` is not a main source card.

Legacy entry cards remain present only as hidden developer/diagnostic-compatible widgets:
- Local import card.
- GSE accession card.
- Chinese research topic card.

Their visible high-risk buttons are disabled in the UI-C2c page:
- `选择本地数据`
- `选择本地文件夹`
- `检索数据集`
- `进入检索界面`

Existing direct test/helper paths remain available for older internal workflow tests, but the normal Data Source surface does not expose them as active main actions.

## 4. Gate Semantics

Project Home and Data Source preserve these semantics:

| semantic area | current state |
|---|---|
| formal DEG | disabled / not carried into this stage |
| ORA / GSEA | disabled / not carried into this stage |
| KM / Cox / survival | disabled / not carried into this stage |
| source acquisition | configuration preview only |
| recent import status | current project preview or empty-safe state only |
| result semantic | no formal computed result |
| report status | draft / not ready |
| export gate | disabled missing report-ready |

The Recent Imports preview explicitly uses an empty-safe row when no project data exists and states `No fake expression matrix; no fake result.`

## 5. Tests Updated

Updated focused tests:
- Project Home status-card test now verifies the 7-step target flow and new readiness/gate cards.
- Data Source primary-module test now verifies four gated source cards.
- Added Data Source gated-selection test to verify source preview status, blocked download/analysis state, and empty-safe recent import table.
- Updated one old GSE status assertion to preserve specific status text instead of forcing the old generic status copy.

## 6. Verification

Commands run:

| command | result |
|---|---|
| `python3 -m py_compile app/bioinformatics/project_home.py app/bioinformatics/workflow_pages.py` | passed |
| `python3 -m pytest -q tests/ui/test_bioinformatics_gate_shell.py` | 5 passed |
| `python3 -m pytest -q tests/ui/test_bioinformatics_project_home.py tests/ui/test_bioinformatics_workflow_pages.py` | 99 passed |
| `python3 -m pytest -q tests/ui/test_bioinformatics_ia_shell.py` | 9 passed |
| `python3 -m app.main --smoke-test` | passed |
| `git diff --check` | passed |
| `git diff --cached --check` | passed |

## 7. Business-Code Boundary Statement

This stage did modify active UI shell code and focused UI tests, but did not modify Bioinformatics executor business logic.

No formal analysis executors were enabled. No downloads, imports, fake outputs, reports, exports, packaging, signing, desktop app replacement, App icon, Finder icon, `.icns`, `Info.plist`, or LaunchServices work was performed.
