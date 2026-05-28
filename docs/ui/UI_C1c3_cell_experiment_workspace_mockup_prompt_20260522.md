# UI-C1c3 Cell Experiment Workspace Mockup Prompt

Date: 2026-05-22

## 1. Prompt Status

Prompt name: `Cell Experiment Workspace`

This prompt supersedes UI-C1c2 Prompt 6 for the cell experiment area. It must not be named `Cell Records / ELISA / ImageJ-Fiji Shell-Only Boundary Page`.

Target path:

`LabTools > 实验模块 > 细胞实验 / Cell Experiment`

## 2. High-Fidelity Mockup Prompt

Create a high-fidelity desktop PySide mockup for BioMedPilot LabTools > Experiment Modules > `细胞实验 / Cell Experiment`. The page is a dedicated cell experiment workspace, not a generic boundary page. It uses the existing light workbench style, left app sidebar, Chinese primary UI copy, practical card/table density, and clear status chips.

The page title is:

`细胞实验 / Cell Experiment`

Subtitle:

`细胞信息、实验记录模板与结果处理工具的独立工作区。`

Top status chips:

- `Developer Preview / 本地测试版`
- `记录保存需适配`
- `结果处理仅外部能力配置`

Add a compact review notice under the header:

`细胞状态和实验记录需由实验人员复核；当前页面不执行自动图像分析，也不保存正式细胞记录。`

## 3. Layout Structure

Use a three-column desktop workbench layout:

| Region | Width | Content |
| --- | --- | --- |
| Left panel | 300-340 px | Cell Profile & Dynamic State |
| Center panel | Flexible / largest | Experiment Record Templates |
| Right panel | 340-400 px | Result Processing + ImageJ/Fiji external engine callout |

Below the main row, include a full-width state timeline / recent activity shell. It must use an empty or mock-labelled state, not fake saved records.

## 4. Left Panel - Cell Profile & Dynamic State

Panel title:

`细胞信息 / Cell Profile`

Show a profile card for one mock cell line:

- `细胞名称`: `A549`
- `来源`: `Human / lung`
- `模型`: `carcinoma model`
- `当前 passage`: `P12`
- `培养条件`: `DMEM + 10% FBS, 37 C, 5% CO2`
- `当前状态`: chip group with `培养中` selected, and muted alternatives `冻存`, `复苏`, `传代后`, `待处理`

Show a dynamic state stack:

- `冻存批次`: empty / shell row, status `需记录模型`
- `冻存管`: empty / shell row, status `需记录模型`
- `污染检查`: `未记录`, status `需人工记录`
- `支原体`: `未记录`, status `需人工记录`
- `形态观察`: `待记录`
- `汇合度`: `待记录`

Add small copy:

`细胞状态由实验记录更新；当前为 mockup / adapter-needed 状态。`

Do not show automatic state transitions or fake record-derived history.

## 5. Center Panel - Experiment Record Templates

Panel title:

`细胞实验记录 / Experiment Record Templates`

Use a grid of record template cards. Each card has a status chip, one-line purpose, and an action button. Use existing LabTools cell experiment icon as a section marker only.

Cards:

1. `传代`
   - Purpose: `记录传代比例、消化时间、接种密度`
   - Status: `仅壳层`
   - Button: disabled `新建记录 - 需记录存储适配`
2. `复苏`
   - Purpose: `记录复苏批次、复苏时间、培养条件`
   - Status: `仅壳层`
   - Button: disabled
3. `冻存`
   - Purpose: `记录冻存批次、冻存管、冻存液`
   - Status: `仅壳层`
   - Button: disabled
4. `接种`
   - Purpose: `记录接种密度、孔板格式、体积`
   - Status: `计算辅助可用 / 保存需适配`
   - Button: active-looking secondary `打开接种计算辅助`; disabled primary `保存记录 - 需适配`
5. `给药 / 处理`
   - Purpose: `记录处理条件、剂量、时间点`
   - Status: `仅壳层`
   - Button: disabled
6. `转染`
   - Purpose: `记录转染试剂、核酸量、时间点`
   - Status: `仅壳层`
   - Button: disabled
7. `从上次记录创建`
   - Purpose: `基于历史记录延续实验流程`
   - Status: `需要历史记录存储`
   - Button: disabled

Center panel empty state:

`当前项目暂无保存的细胞实验记录；记录保存需要后续 CellExperimentRecordStore。`

Important: the mockup may show template cards, but must not show fake saved records or real saved timelines.

## 6. Right Panel - Result Processing

Panel title:

`细胞结果处理工具 / Result Processing`

Show result-processing entry rows:

- `划痕实验`
  - Status chip: `规划中`
  - Description: `可设计图像标注与复核流程；不执行自动 ROI`
- `Transwell`
  - Status chip: `规划中`
  - Description: `可设计计数复核界面；不执行自动细胞计数`
- `荧光 / 染色图像`
  - Status chip: `规划中`
  - Description: `可设计图像预览与人工标注；不执行自动分割`

Then show an external engine callout:

Title:

`ImageJ/Fiji 外部引擎`

Status:

`Settings 外部能力配置`

Rows:

- `检测状态`: `未在此页检测`
- `配置入口`: `设置中心 > 外部能力`
- `运行状态`: `暂不执行图像分析`

Buttons:

- Active navigation: `前往设置中心`
- Disabled: `运行图像分析 - 暂未开放`

Do not show automatic ROI, automatic cell counting, automatic scratch closure measurement, automatic Transwell counting, fluorescence quantification, ImageJ/Fiji macro execution, or batch image analysis completed state.

## 7. Bottom Timeline / Recent Activity Shell

Panel title:

`状态时间线 / State Timeline`

Show a quiet empty state:

`暂无可读取的细胞实验记录。接入记录模型后，这里将显示传代、复苏、冻存、接种、处理和转染事件。`

State chips:

- `仅壳层`
- `需记录存储适配`

Do not show fake event rows such as "P11 passaged yesterday" unless explicitly marked as mock example. Prefer empty state for the first candidate.

## 8. Visual Style Rules

- Keep Chinese UI copy primary; English terms can be secondary.
- Keep the app sidebar visible and LabTools selected.
- Use compact cards with 8 px radius or less.
- Use status chips with visible text labels.
- Use warning rows for blocked/adapter-needed states.
- Use existing LabTools cell experiment icon as a marker only.
- Do not use ImageJ/Fiji as a large primary LabTools card.
- Do not use ELISA graphics or absorbance plate UI in this cell workspace.
- Do not use App icon, Finder icon, `.icns`, packaging, or desktop-entry resources.

## 9. Must Not Claim

- No ELISA inside this workspace.
- No real cell record save.
- No real cell profile persistence.
- No freeze batch/vial persistence.
- No automatic state timeline.
- No automatic image analysis.
- No automatic ROI.
- No automatic cell counting.
- No ImageJ/Fiji execution.
- No ImageJ/Fiji built-in algorithm.
- No cloud sync, LAN sharing, collaboration, or inventory decrement.
- No default write path to `~/.labtools`.

## 10. Separate ELISA Direction

ELISA should be handled in a separate mockup under:

`LabTools > 实验模块 > 免疫与吸光度`

Its current state remains:

- `blocked_until_backend`
- no active ELISA analysis
- no 4PL default workflow
- no formal report
- no production save/export

Do not include ELISA in the Cell Experiment Workspace candidate.

## 11. Expected Review Decision For First Candidate

The first generated Cell Experiment Workspace image should be reviewed against:

- `docs/ui/UI_C1c3_cell_experiment_screen_acceptance_checklist_20260522.md`
- `docs/ui/UI_C1c3_cell_experiment_ia_recalibration_20260522.md`

Likely acceptable first-pass status:

- `accepted_with_boundary_review` if IA is correct and only text needs tightening.
- `needs_redesign` if ELISA appears, ImageJ/Fiji becomes a first-level entry, or fake records/results are shown.
