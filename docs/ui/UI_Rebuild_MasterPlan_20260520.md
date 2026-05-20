# UI Rebuild MasterPlan

Date: 2026-05-20

Status: current UI rebuild master document

Scope: UIShell / global UI / Bioinformatics / Meta Analysis / LabTools / Settings

## 1. Document Priority

This document is the highest-priority UI rebuild standard after UI-B0.

Priority order:

1. `docs/ui/UI_Rebuild_MasterPlan_20260520.md`
2. `docs/ui/UI_Visual_Style_Guide_v1_20260520.md`
3. `docs/ui/UI_I18N_Strategy_v1_20260520.md`
4. `docs/ui/UI_Rebuild_Stage_Index_20260520.md`
5. UI-A1 / UI-A2 / UI-A3 / UI-A4 audit reports
6. `docs/ui/target_design_drafts/**`
7. Historical stage reports and archived/legacy UI references

`docs/ui/target_design_drafts/**` are target-draft inputs. They are not direct implementation standards unless this MasterPlan adopts the relevant decision.

## 2. Current Phase Boundary

Current checkpoint after UI-C0: low-fidelity shell usability pass.

Completed:

- UI-B0: governance documents.
- UI-B1: design tokens, theme and basic primitives.
- UI-B2: Welcome / Dashboard / Sidebar / About / Test Feedback low-fidelity shell.
- UI-B3: Settings secondary navigation and external capability management shell.
- UI-B4: LabTools IA shell.
- UI-B5 shell: Bioinformatics target IA shell and gated/preflight copy.
- UI-B5.1: Bioinformatics legacy page routing calibration.
- UI-B5.2: Bioinformatics target page consolidation.
- UI-B6 shell: Meta Analysis target IA shell and active Meta type display.
- UI-B6.1: Meta Analysis target shell interaction calibration.
- UI-B7 shell: shared Result / Report / Export semantic shell.
- UI-B7.1: Result / Report / Export shell adoption calibration.
- UI-B8a: resource inventory / placeholder strategy.
- UI-B9a: semantic key registry.
- UI-B9b: key adoption / test migration.
- UI-B9c: selective key adoption / test migration expansion.
- UI-C0: low-fidelity shell usability pass.

Partially completed:

- Full UI-B9 i18n adoption / language switch has not started.

Not started:

- UI-B8b formal resource replacement.
- UI-B10 packaging / desktop entry.

Current hard boundary:

- Do not handle App icon, Finder icon, Info.plist icon binding, LaunchServices, packaged app validation, or desktop `.app` overwrite before UI-B10.
- Do not treat UI-B8a as resource replacement; it is only inventory and placeholder policy.
- Do not treat UI-B9a/B9b/B9c as full i18n; they are key registry, selective key adoption and focused test migration only.

Recommended next stage:

- UI-B8b formal resource replacement only after brand/resource confirmation, or
- UI-C1 module-specific usability follow-up if a new shell surface needs deeper calibration.

## 3. Rebuild Principles

1. MasterPlan first, code second.
2. Low-fidelity shell first, high-fidelity visual polish later.
3. Tokens and primitives first, pages second.
4. Hide or downgrade old entries before exposing new entries.
5. Settings external resource architecture first, module calls second.
6. Semantic state keys first, button copy second.
7. Do not package planned, testing, shell-only, or Developer Preview capabilities as production features.
8. Do not handle packaging, desktop `.app` overwrite, Finder icon, or LaunchServices validation before UI-B10.
9. Integration-unmerged module capabilities must be dependencies or blockers, not available UI.
10. Old Markdown, old branches, and historical pages cannot bypass this MasterPlan.

## 4. Target Global IA

```text
Welcome / 欢迎页
-> Dashboard / 工作台
   -> Bioinformatics / 生信分析
   -> Meta Analysis / Meta 分析
   -> LabTools / 实验工具
   -> Settings / 设置中心

Auxiliary:
-> Test Feedback / 测试反馈
-> About / 关于
```

### 4.1 Welcome

Target role: replace the current pseudo-login page.

Required content:

- Primary brand: `萤火虫 / Firefly`
- Subtitle: `BioMedPilot / 医研智析`
- Status: `Developer Preview / 本地测试版`
- Primary action: `进入本地工作台`
- Secondary actions: recent projects, Settings, About

Forbidden in first version:

- Login
- Register
- VIP
- License purchase
- Subscription purchase
- Fake account flow

### 4.2 Dashboard

Target role: three-module workbench entry, not project center, settings page, test page, or marketing page.

Cards:

- `Bioinformatics / 生信分析`
- `Meta Analysis / Meta 分析`
- `LabTools / 实验工具`

Each card shows module name, short goal, status, and one enter action. Do not list unimplemented sub-capabilities on Dashboard cards.

### 4.3 Sidebar

Primary user navigation:

```text
Dashboard / 工作台
Bioinformatics / 生信分析
Meta Analysis / Meta 分析
LabTools / 实验工具
Settings / 设置中心
```

Auxiliary/bottom navigation:

```text
测试反馈
关于
```

Not top-level navigation:

- Project Center
- Data Center
- Task Center
- Report Center
- External Engines
- Packaging
- Developer Diagnostics
- Account / Subscription
- Local AI
- PDF OCR
- ImageJ / Fiji

## 5. Settings Target IA

```text
Settings / 设置中心
-> 常规设置
-> 账户与订阅
-> 本地项目与存储
-> 外部引擎、模型与分析资源
-> 开发者诊断
```

Rules:

- Settings uses detect-first and user-triggered actions.
- Automatic detection reads state only.
- No automatic install, download, update, delete, upload, enable, or cloud configuration.
- Cloud AI remains future/open only in this phase; no API key or purchase UI.
- Developer diagnostics stay out of Dashboard and ordinary user flows.

Every future external engine, model, package, database, or analysis resource added by Codex must get a Settings management item. It must not be silently invoked from module code.

## 6. Bioinformatics Target IA

Main flow:

```text
Project Home
-> Data Source
-> Data Check & Preparation
-> Group & Design
-> Analysis Tasks
-> Result & Report
-> Report Export
```

Auxiliary:

```text
Bioinformatics Settings
Project Logs & Technical Details
```

Page rules:

- `Project Home` shows current project status, recent content, and recommended next step.
- `Data Source` covers local import, GEO, TCGA, GTEx, and Chinese research question search.
- `Data Check & Preparation` is file-level recognition. It must show all included files, not only the first file.
- `Group & Design` is shared sample grouping and comparison design, not DEG-only.
- `Analysis Tasks` groups DEG, GSEA/ORA, correlation, clinical/survival, visualization and report assistance.
- Before B8.1, no formal DEG / GSEA / survival / clinical association / report-ready buttons.
- `Result & Report` is a single task result page, not a result center.
- `Report Export` reads only results added by the user to the report draft. Markdown first; HTML optional; DOCX/PDF later.
- `Bioinformatics Settings` must affect later page behavior.
- `Project Logs & Technical Details` centralizes technical logs and feedback packages.

## 7. LabTools Target IA

Top-level LabTools structure:

```text
LabTools / 实验工具
-> 通用计算器
-> 试剂制备
-> 实验模块
```

Not top-level LabTools entries:

- Image analysis assist
- Experiment record system
- Materials/inventory records
- Image analysis engine settings
- External image analysis engine
- Full collaboration system

Rules:

- General calculators only contain cross-experiment formulas and unit conversion.
- Experiment-specific calculations stay inside the relevant experiment module.
- Reagent preparation follows template -> configured preparation -> current preparation sheet -> saved record.
- Current preparation cannot temporarily mutate the source template; template changes require copy/new template.
- Materials records are horizontal local capability only in first phase.
- No cloud collaboration, LAN collaboration, LIMS, electronic signature, or compliance audit.
- Image analysis is embedded into concrete experiment modules; ImageJ/Fiji configuration belongs in Settings.

Experiment module groups:

- Cell experiments
- Protein experiments
- Nucleic acid experiments
- Immunoassay and absorbance assays
- Immunohistochemistry

## 8. Meta Analysis Target IA

Main flow:

```text
Project Home
-> Question & Meta Type
-> Search Strategy
-> Import & Deduplication
-> Screening
-> Full-text & Extraction
-> Quality Assessment
-> Meta Analysis Tasks
-> Result & Report
-> Report Export
```

Auxiliary:

```text
Meta Settings
Meta 项目日志与复现包
```

Current Meta type keys:

- `binary_outcome_meta`
- `continuous_outcome_meta`
- `survival_outcome_meta`
- `prevalence_incidence_meta`
- `diagnostic_accuracy_meta`
- `exposure_disease_risk_meta`
- `biomarker_expression_difference_meta`
- `correlation_meta`
- `prognostic_factor_meta`
- `dose_response_meta`

Rules:

- Network Meta is planned only and not an available type.
- PubMed is the first online database that may become confirmable/executable.
- WOS, Embase, CNKI and other sources are search-string generation or local import only until proven.
- Screening decisions and exclusion reasons must remain user-confirmed.
- PDF/OCR assists extraction but does not complete extraction automatically.
- Quality assessment must be user-confirmed.
- Meta Analysis Tasks remain testing-level workflow until calibrated.
- No medical conclusions are generated.
- Cloud AI result analysis is future work.

## 9. Merge / Hide / Downgrade Rules

Do not expose these as ordinary user standalone primary pages:

- Project Center
- Data Center
- Task Center
- Report Center
- Acquisition Status
- Recognition
- Readiness Dashboard
- Standardized Assets
- Workflow Status
- Manifest Viewer
- Raw JSON Viewer
- Developer Diagnostics
- ImageJ/Fiji LabTools main task page
- Network Meta formal entry
- Cloud AI configuration / API key
- Account purchase / VIP / License

Destination:

- Dashboard recent projects
- Bioinformatics Data Source / Data Check / Logs
- Settings external resources and developer diagnostics
- Meta planned/testing status
- LabTools concrete experiment modules

## 10. Unified Status Semantics

Initial status vocabulary:

- `Developer Preview`
- `本地测试版`
- `testing`
- `planned`
- `shell-only`
- `preflight-only`
- `blocked`
- `available`
- `not configured`
- `missing`
- `failed`
- `draft`
- `report-ready` later only

Critical rules:

- Bioinformatics B8.1 gates formal analysis buttons.
- Meta shell-only/testing must not become production workflow copy.
- LabTools planned submodules must not enter the main operation area.
- ImageJ/Fiji configuration belongs in Settings.
- First i18n version can remain Chinese-first but must preserve key boundaries.
- Packaging and desktop entry are last-stage work.

## 11. Immediate Next Stage

After UI-C0, proceed only with one of the following confirmed next stages:

```text
UI-C1: module-specific usability follow-up, if deeper shell calibration is needed
UI-B8b: formal resource replacement, only after brand/resource confirmation
UI-B10: packaging / desktop entry, only when explicitly authorized
```

Do not treat UI-C0 as permission to replace icons, bind App icons, update Finder/LaunchServices metadata, or run packaged app validation.

## 12. UI-B0 Completion Statement

This MasterPlan is one of four UI-B0 outputs. It is a documentation-only change and does not authorize business code or UI implementation changes by itself.
