# LabTools Backend Gap Audit for UI Planning

日期：2026-05-22

范围：评估当前 LabTools 后端相对于 BioMedPilot 桌面 UI mockup 和 integration 的缺口。本文不新增功能。

## 1. 功能状态矩阵

| 功能 | 当前后端能力 | UI 状态 | 建议 |
|---|---|---|---|
| 通用实验计算器 | quick task specs、v1 dataclass calculators、copy text | `active_backend_ready` + `ui_adapter_needed` | P0 接入任务卡片。 |
| 动态公式求解 | `FormulaSpec` + solver functions + unit helper | `active_backend_ready` + `ui_adapter_needed` | P0 接入高级公式求解。 |
| 稀释 | `calculate_dilution_v1`, `solve_dilution_equation` | `active_backend_ready` | 快速计算和公式求解都可接。 |
| 浓度换算 | `solve_concentration_bridge`, `convert_mass_concentration_unit` | `active_backend_ready` | P0 放公式求解，P1 放独立换算小工具。 |
| 溶液配制 | `solve_solution_preparation_formula`, `calculate_solution_preparation` | `active_backend_ready` | 新 UI 使用 solver，旧 API 不做主入口。 |
| 试剂模板 | models + `ReagentTemplateStore` + validation | `active_backend_ready` + `ui_adapter_needed` | P0 做列表和编辑 side panel。 |
| 配制记录 | `PreparationRecord`, `PreparationRecordStore` | `active_backend_ready` + `ui_adapter_needed` | P0 本次配制保存，P1 历史列表。 |
| WB loading calculator | `calculate_wb_loading`, records, store, Markdown/CSV export | `active_backend_ready` + `ui_adapter_needed` | P0 完整计算页，P1 历史页。 |
| SDS-PAGE gel helper | template model, batch calculation, JSON/XLSX export | `active_backend_ready` + `ui_adapter_needed` | P0 配胶页；需要持久化 adapter。 |
| BCA helper | OD parser, annotation, linear fit, warnings | `mockup_only` to `ui_adapter_needed` | P0 mockup 可做；正式保存前补 record store。 |
| qPCR mix | `QpcrMixInput`, `calculate_qpcr_mix_v1` | `active_backend_ready` | 当前只保留 mix calculator。 |
| cell plating | `CellSeedingInput`, `calculate_cell_seeding_v1` | `active_backend_ready` | P1 独立页，P0 可在快速计算出现。 |
| 细胞实验记录 | no record model/store | `shell_only` / `blocked_until_backend` | P0 只做模板首页壳；后续补 store。 |
| ELISA / 吸光度 | `labtools.elisa` empty | `blocked_until_backend` | 需要先做 MVP，不能接真实 ELISA 页面。 |
| ImageJ/Fiji 图像分析入口 | no backend API | `shell_only` | 只做入口和外部引擎状态，不做图像分析承诺。 |

## 2. 缺口评估

### 2.1 ELISA 是否需要先做 MVP

结论：需要。

当前 `labtools.elisa` 只是预留命名空间，没有 public API。虽然 BCA helper 已经有 OD matrix、annotation、linear fit、out-of-range warning，但 ELISA 标准曲线、样本稀释倍数、4PL/linear 策略、记录模型和导出都没有固化。

建议 ELISA MVP 后端最小范围：

- `ElisaPlateMatrix`
- `ElisaWellAnnotation`
- `ElisaStandardCurveConfig`
- `ElisaAnalysisResult`
- `parse_elisa_od_matrix`
- `analyze_elisa_linear_curve`
- `ElisaRecord`
- `ElisaRecordStore`

4PL 不应作为第一版默认能力；可作为后续明确假设的高级模式。

### 2.2 qPCR 是否只保留 mix calculator

结论：当前 UI 只保留 qPCR mix calculator。

已有后端只覆盖 reaction mix 体积和 overage。没有 primer dilution、plate setup、Ct/Delta Ct/Delta Delta Ct、standard curve 或 qPCR record store。P0/P1 不应展示超出 mix calculator 的 qPCR 功能。

### 2.3 cell culture 是否需要记录 store

结论：需要，但不属于本阶段。

当前 `labtools.cell_culture` 只重导出 cell seeding calculator。细胞实验记录模板首页可以做 shell，但真实记录需要：

- `CellExperimentTemplate`
- `CellExperimentRecord`
- `CellExperimentRecordStore`
- plate format presets
- optional attachment / notes model

在补 store 前，不应提供“保存细胞实验记录”的真实按钮。

### 2.4 ImageJ/Fiji 是否只做入口和外部引擎状态

结论：是。

当前 LabTools 没有 ImageJ/Fiji 后端 API，没有 executable discovery、macro runner、ROI model、result parser 或安全边界。UI 可以做：

- 外部引擎未连接状态
- 配置入口占位
- 支持范围说明

不应做：

- 自动条带识别
- 灰度定量承诺
- ROI 自动分析
- 后台运行 Fiji macro

### 2.5 导出按钮是否已有后端支持

部分已有。

| 区域 | 后端导出状态 | 缺口 |
|---|---|---|
| WB loading | Markdown / CSV 已有 | 需要 UI file picker adapter。 |
| SDS-PAGE 配胶 | XLSX 已有 | 需要 UI file picker adapter。 |
| SDS-PAGE 模板 | JSON 导入/导出已有 | 需要模板持久化 adapter。 |
| 通用快速计算 | 复制文本部分已有，统一导出未完成 | 需要统一 CalculationRecord store/export。 |
| 试剂配制 | record store 已有，文件导出未统一 | 可先复制文本，后续加 Markdown/CSV。 |
| BCA / OD | copy text helper 存在但未导出 public `__all__`，无 record/export | 需要 store 和 export。 |
| ELISA | 无 | blocked。 |
| cell culture records | 无 | blocked。 |

### 2.6 历史记录是否每个页面都需要

不是每个页面 P0 都需要，但每个真实计算工作流最终都应该有保存路径。

优先级：

1. P0 必须保存：试剂模板、本次试剂配制、WB loading。
2. P1 保存：通用快速计算、动态公式求解、SDS-PAGE 模板/计算、BCA/OD。
3. blocked：ELISA、细胞实验记录、ImageJ/Fiji。

当前最大缺口是通用 `CalculationRecordStore` 不存在。`CalculationResult.to_record()` 可以生成记录，但没有统一本地 store。

### 2.7 本地存储路径与 BioMedPilot storage root 是否需要 adapter

结论：需要。

当前默认存储根目录来自：

```text
LABTOOLS_STORAGE_ROOT 或 ~/.labtools
```

桌面 UI 不应默认写入 `~/.labtools`，应由 BioMedPilot adapter 明确传入路径：

- `ReagentTemplateStore(path=...)`
- `PreparationRecordStore(path=...)`
- `WBLoadingRecordStore(path=...)`

建议新增 integration adapter，但不在本阶段实现：

- `BioMedPilotLabToolsStorageAdapter`
- app-specific root path resolution
- migration/version checks
- backup and corruption recovery strategy

## 3. Backend Gap List

| 缺口 | 阻塞页面 | 建议优先级 |
|---|---|---|
| `CalculationRecordStore` | 通用快速计算历史、动态公式历史 | P1 |
| BioMedPilot storage root adapter | 所有保存/历史页面 | P0 before real desktop integration |
| BCA record model/store/export | BCA / OD 记录正式保存 | P1 |
| ELISA MVP backend | ELISA / 吸光度 | P2 |
| Cell experiment record store | 细胞实验记录模板首页真实保存 | P2 |
| ImageJ/Fiji external engine adapter | ImageJ/Fiji 图像分析入口 | P2 |
| SDS-PAGE persistent template store | SDS-PAGE 模板库 | P1 |
| Unified export/copy adapter | 多数结果页 | P1 |
| UI-facing error normalization layer | 所有页面 | P0 adapter work |

## 4. 不应在本阶段声明完成的能力

- LabTools 完整桌面产品化
- BioMedPilot 页面已接入
- ELISA 分析可用
- ImageJ/Fiji 图像分析可用
- 细胞实验记录可保存
- 所有计算都有历史记录
- 所有页面都有文件导出
- 打包、LaunchServices 或 Finder-style launch validation

## 5. 推荐下一步

1. 用本阶段 screen inventory 做 P0 mockup。
2. 为 UI adapter 设计统一 error/warning/result view model。
3. 在真实桌面接入前补 BioMedPilot storage root adapter。
4. P0 页面先接 active backend：快速计算、公式求解、试剂模板、本次配制、WB loading、SDS-PAGE。
5. BCA/OD 先做 mockup 和 adapter spike，确认 record store 后再进入正式保存。
