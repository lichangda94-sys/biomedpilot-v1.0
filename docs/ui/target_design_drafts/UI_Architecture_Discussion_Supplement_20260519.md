# UI 架构讨论记录补充：Settings、主导航与 Bioinformatics 收敛方案

日期：2026-05-19
适用范围：UIShell / Settings / Sidebar / Dashboard / Bioinformatics / 后续 Codex UI 开发
文件性质：阶段性 UI 设计决策与 Codex 实现输入，不是完整 Figma 设计稿

---

## 1. 文件背景

本文件是在上一份阶段性 UI 讨论记录之后继续补充形成的 UI 架构决策。

上一份已确认内容包括：

- Welcome Page / 启动页；
- About Firefly / 关于萤火虫；
- Dashboard / 全局工作台；
- 三大主模块卡片；
- 用户第一层不直接暴露 ImageJ / Fiji；
- Dashboard 三模块：Bioinformatics、Meta Analysis、LabTools。

本文件记录上一份文件之后新增确认的内容，主要包括：

1. Settings / 设置中心结构；
2. 外部引擎与模型结构；
3. 云端 AI 服务命名；
4. PDF 识别与 OCR 引擎；
5. 全局侧边栏 / 主导航；
6. Bioinformatics 模块页面压缩方案；
7. Bioinformatics 项目首页；
8. Bioinformatics 数据来源页面；
9. “已记录 / 已下载”数据来源状态；
10. 数据来源详情默认折叠规则；
11. 后续 Codex 实现原则。

---

## 2. Settings / 设置中心结构决策

### 2.1 设置中心总体结构

设置中心不应作为杂物箱，也不应把技术诊断直接暴露给普通用户。
设置中心目标结构确定为：

```text
Settings / 设置中心
├── 常规设置
├── 账户与订阅
├── 本地项目与存储
├── 外部引擎与模型
└── 开发者诊断
```

### 2.2 常规设置

用于普通用户可理解的基础偏好。

可包含：

- 语言；
- 外观；
- 默认启动行为；
- 导出格式偏好；
- 单位显示偏好。

注意：

- 当前如果只支持浅色主题，不要假装深色模式已完整可用；
- 不在此处放 manifest、cache path、internal id 等技术字段。

### 2.3 账户与订阅

用于承接从启动页和 Dashboard 移除的账户、VIP、订阅、License 信息。

当前状态：

```text
当前版本：本地测试版
登录系统：暂未开放
账户：后续开放
VIP / 订阅：后续开放
License：后续开放
当前测试权限：已开放本地功能可免费测试
```

要求：

- 不在启动页和 Dashboard 主流程中显示账号登录；
- 不显示购买、升级、价格套餐、支付入口；
- 账户与订阅页面当前应作为 Planned / Disabled / 后续开放；
- 未来真实接入账号系统后再启用交互。

### 2.4 本地项目与存储

用于本地项目路径、缓存、导出位置等。

可包含：

- 默认项目保存路径；
- 最近项目记录；
- 缓存位置；
- 导出文件保存位置；
- 清理缓存。

要求：

- 普通用户主视图只显示可理解的路径设置；
- manifest、JSON、internal id 放到开发者诊断或折叠技术详情。

### 2.5 开发者诊断

用于开发者和内部测试，不面向普通用户主流程。

可包含：

- 图标资源状态；
- manifest；
- cache path；
- package metadata；
- codesign 状态；
- debug 信息；
- 测试报告；
- 内部路径；
- 资源生成状态。

要求：

- 默认折叠或仅在开发者模式显示；
- 不进入 Dashboard；
- 不作为普通用户一级页面。

---

## 3. 外部引擎与模型

### 3.1 命名决策

“本地 AI”和“外部引擎”不再拆成两个一级区块，统一合并为：

```text
外部引擎与模型
```

原因：

这些能力本质上都是 BioMedPilot / 萤火虫 调用的外部能力，不属于主程序自身：

- 图像分析引擎；
- PDF 识别与 OCR；
- 本地语言模型；
- 云端 AI 服务；
- 未来其他外部处理工具。

### 3.2 外部引擎与模型内部结构

确定结构：

```text
外部引擎与模型
├── 图像分析引擎
├── PDF 识别与 OCR 引擎
├── 本地语言模型
└── 云端 AI 服务
```

---

## 4. 图像分析引擎

### 4.1 页面定位

图像分析引擎用于 LabTools 的实验图像分析辅助流程。

包括但不限于：

- Western Blot；
- 细胞图像；
- 划痕实验；
- Transwell；
- 荧光 / 染色图像；
- 其他实验图像分析辅助。

### 4.2 用户层表达规则

Dashboard、启动页、About 页面、主模块卡片和普通用户第一层文案中，不直接暴露具体引擎名称。

统一使用：

```text
外部图像分析引擎
外部图像分析辅助
图像分析辅助
```

具体引擎名称只在以下位置出现：

- 设置中心；
- 外部引擎与模型；
- 外部引擎配置页；
- 技术详情；
- 开发者诊断；
- 安装 / 配置说明。

### 4.3 禁止表达

用户层禁止写成：

- 内置图像识别；
- 自动 ROI；
- 自动细胞计数；
- 自动条带识别；
- 自动 WB 灰度结论；
- 自动实验解释；
- 自动诊断。

---

## 5. PDF 识别与 OCR 引擎

### 5.1 页面定位

PDF 识别与 OCR 引擎用于 Meta Analysis 的全文 PDF 转换、文字识别和文本抽取辅助。

该能力面向文献处理，不归入实验图像分析。

### 5.2 应归属的位置

PDF 识别与 OCR 不属于 Dashboard 主模块卡片，也不属于普通用户第一层入口。
它应作为 Settings 中“外部引擎与模型”的子项。

路径：

```text
设置中心 → 外部引擎与模型 → PDF 识别与 OCR 引擎
```

### 5.3 当前状态表达

当前应标记为：

```text
外部依赖 / 可选配置 / 后续接入状态
```

具体实际能力以后以模块接入状态为准。

### 5.4 用户层说明方向

可写：

```text
用于 Meta 分析中全文 PDF 的文字识别、文本转换和结构化抽取辅助。当前功能需要外部引擎支持，识别结果需人工复核。
```

禁止写成：

- 自动全文提取；
- 自动识别所有 PDF 表格；
- 自动完成数据提取；
- 自动替代人工筛选；
- 自动绕过全文获取限制。

---

## 6. 本地语言模型

### 6.1 命名

本地部署的大语言模型统一称为：

```text
本地语言模型
```

不建议在用户层泛泛称为“本地 AI”。

### 6.2 页面定位

本地语言模型用于：

- 草稿；
- 翻译；
- 术语解释；
- 检索词辅助；
- 摘要辅助；
- 其他本地文本辅助任务。

### 6.3 状态表达

默认状态：

```text
默认关闭，用户自行启用。
```

要求：

- 不默认联网；
- 不自动上传数据；
- 不自动生成最终科研结论；
- 不直接写入最终分析结果；
- 输出需人工确认。

---

## 7. 云端 AI 服务

### 7.1 命名决策

未来联网商业 AI 模型服务统一称为：

```text
云端 AI 服务
```

不用“联网 AI”作为正式 UI 名称。

### 7.2 页面定位

云端 AI 服务表示未来接入的商业或云端模型 API 服务。

可用于未来：

- 商业 AI 模型 API 调用；
- 云端大模型推理；
- 高级文本辅助；
- 可能的付费 AI 能力。

### 7.3 当前状态

当前版本：

```text
后续开放 / 默认关闭 / 不自动上传数据
```

### 7.4 禁止表达

当前阶段不显示：

- API Key 输入主流程；
- 购买 AI 服务；
- 自动生成科研结论；
- 一键 AI 分析；
- 外部商业模型 Logo 集合；
- 默认联网。

---

## 8. 全局侧边栏 / 主导航决策

### 8.1 主导航

左侧主导航保留 5 个一级入口：

```text
Dashboard / 工作台
Bioinformatics / 生信分析
Meta Analysis / Meta 分析
LabTools / 实验工具
Settings / 设置中心
```

### 8.2 底部或辅助入口

底部或辅助区域保留：

```text
测试反馈
关于
```

### 8.3 不进入主导航的内容

以下内容不作为左侧主导航一级入口：

- Project Center；
- Data Center；
- Task Center；
- Report Center；
- External Engines；
- Packaging；
- Developer Diagnostics；
- Account / Subscription；
- Local AI；
- PDF OCR；
- ImageJ / Fiji。

### 8.4 归属规则

这些内容应分别归入：

```text
Project / Data / Task / Report
→ 归入具体模块内部流程，暂不作为全局中心。

External Engines / 本地语言模型 / 云端 AI 服务 / PDF OCR
→ 归入 Settings → 外部引擎与模型。

Developer Diagnostics
→ 归入 Settings → 开发者诊断。

Account / Subscription / VIP / License
→ 归入 Settings → 账户与订阅。
```

### 8.5 当前全局结构

```text
Welcome Page
└── Dashboard / 工作台
    ├── Bioinformatics / 生信分析
    ├── Meta Analysis / Meta 分析
    ├── LabTools / 实验工具
    └── Settings / 设置中心

辅助入口：
- 测试反馈
- 关于
```

---

## 9. Bioinformatics 页面收敛总决策

### 9.1 总体方向

Bioinformatics 目标 UI 不再按当前 UI-03 到 UI-13 的历史页面编号平铺展示。
后续应从普通用户任务出发，将当前约 13 个页面压缩为 7–8 个主页面。

目标是：

- 减少普通用户主流程页面数量；
- 合并技术状态页；
- 降低 manifest / acquisition / readiness / asset registry 等技术术语暴露；
- 让用户按“项目 → 数据 → 检查 → 分组 → 分析 → 结果 → 报告”的自然流程前进；
- 保留技术详情，但放入折叠区或开发者诊断区。

### 9.2 Bioinformatics 目标主页面

确定目标结构：

```text
Bioinformatics / 生信分析

1. 项目首页 / Project Home
2. 数据来源 / Data Source
3. 数据检查与准备 / Data Check & Preparation
4. 分组与分析设计 / Group & Design
5. 分析任务 / Analysis Tasks
6. 结果浏览 / Results
7. 报告导出 / Report
8. 生信设置 / Bioinformatics Settings
```

### 9.3 当前页面合并关系

```text
当前页面 → 目标页面

UI-03 Project Home
→ 项目首页 / Project Home

UI-04 Data Source & Registration
Chinese Dataset Search
UI-05 Acquisition Status
→ 数据来源 / Data Source

UI-06 Recognition
UI-07 Readiness Dashboard
UI-08 Standardized Assets
→ 数据检查与准备 / Data Check & Preparation

Group Comparison Design
→ 分组与分析设计 / Group & Design

UI-09 Workflow Status
UI-10 Analysis Task Center
DEG Config / Preflight
→ 分析任务 / Analysis Tasks

UI-11 Results Browser
Imported DEG Browser
→ 结果浏览 / Results

UI-12 Report Viewer
→ 报告导出 / Report

UI-13 Settings & Local AI
→ 生信设置 / Bioinformatics Settings
```

### 9.4 关键合并决策

1. UI-05 Acquisition Status 不再作为普通用户独立页面。
   它并入“数据来源”，只作为数据获取状态摘要和技术详情。

2. Recognition / Readiness / Standardized Assets 合并为“数据检查与准备”。
   用户不需要理解这些内部阶段，只需要知道数据是否可用、缺什么、下一步是什么。

3. Workflow Status / Analysis Task Center / DEG Preflight 合并为“分析任务”。
   分析任务页负责展示任务配置、preflight、可执行状态和 testing 边界。

---

## 10. Bioinformatics：项目首页 / Project Home

### 10.1 页面定位

项目首页不再作为复杂功能入口页，而是作为当前生信项目的状态总览和下一步引导页。

页面目标：

- 让用户知道当前打开的是哪个生信项目；
- 让用户知道项目进行到哪一步；
- 显示数据、分组、分析、结果和报告的大致状态；
- 提供一个最明确的推荐下一步；
- 避免在首页暴露技术细节。

### 10.2 顶部显示内容

项目首页顶部显示：

- Bioinformatics / 生信分析；
- 项目名称；
- 最近修改时间；
- 当前状态。

示例：

```text
Bioinformatics / 生信分析

甲状腺癌 TCGA 分析项目
最近修改：2026-05-19
当前状态：数据已构建，等待数据检查与准备
```

### 10.3 不显示 Developer Preview / 测试中

项目首页不显示：

```text
Developer Preview · 测试中
```

原因：

- 全局版本状态已经在启动页、Dashboard 或必要的全局状态区域表达；
- 模块内部项目首页不需要反复显示测试标签；
- 项目首页应更像真实工作台页面，重点显示项目本身状态。

注意：

结果页、分析任务页、报告页仍然需要在结果或报告区域显示 testing / draft / manual review 等边界。
只是项目首页不需要重复显示。

### 10.4 当前项目状态摘要

页面主体建议显示 3–5 个轻量状态卡：

```text
数据来源
数据检查
分组设计
分析任务
结果 / 报告
```

显示示例：

```text
数据来源：已登记 1 个 TCGA 项目
数据检查：待运行
分组设计：未确认
分析任务：未配置
结果报告：暂无
```

### 10.5 推荐下一步

项目首页最重要的是“推荐下一步”。

每次只突出一个主操作。

可选主操作包括：

- 选择数据来源；
- 运行数据检查；
- 确认分组设计；
- 配置分析任务；
- 查看结果；
- 生成报告。

示例：

```text
推荐下一步：
当前项目已有数据来源，但尚未完成数据检查。

[运行数据检查与准备]
```

### 10.6 最近内容摘要

可显示：

- 最近数据来源；
- 最近分析任务；
- 最近结果；
- 最近报告。

如果没有内容，显示空状态：

```text
暂无数据来源。请先导入本地数据或选择 GEO / TCGA / GTEx 数据来源。
```

### 10.7 技术详情

技术详情默认折叠。

可包含：

- 项目保存路径；
- project manifest；
- config 文件；
- 内部状态；
- 最近运行记录；
- 调试信息。

### 10.8 项目首页主界面不应显示

主界面不显示：

- manifest；
- source_files；
- project_config.json；
- asset id；
- cache path；
- backend diagnostics；
- 多个同权重主按钮；
- 打开项目文件夹大按钮；
- 查看项目结构大按钮；
- 测试 runner 信息。

这些内容如有必要，放入默认折叠的技术详情 / Developer Diagnostics。

### 10.9 项目首页结构草稿

```text
Bioinformatics / 生信分析

[项目名称]
甲状腺癌 TCGA 分析项目
最近修改：2026-05-19
当前状态：数据已构建，等待数据检查与准备

当前项目状态
[数据来源]      已登记
[数据检查]      待运行
[分组设计]      未确认
[分析任务]      未配置
[结果报告]      暂无

推荐下一步
当前项目已有数据来源，但尚未完成数据检查。
[运行数据检查与准备]

最近内容
数据来源：TCGA-THCA
最近任务：暂无
最近结果：暂无
最近报告：暂无

技术详情，默认折叠
```

---

## 11. Bioinformatics：数据来源 / Data Source

### 11.1 页面定位

数据来源页用于帮助用户选择、登记、导入或下载生信分析数据来源。

该页面不只是“数据库检索页”，而是所有数据来源的统一入口。

数据来源包括：

1. 本地数据导入；
2. GEO 数据库；
3. TCGA 数据库；
4. GTEx 数据库；
5. 中文研究问题检索，作为辅助智能搜索入口。

### 11.2 页面入口顺序

确认顺序为：

```text
1. 本地数据导入
2. GEO 数据库
3. TCGA 数据库
4. GTEx 数据库
5. 中文研究问题检索
```

逻辑：

```text
用户优先使用本地已有数据。
如果没有本地数据，再选择常见公共数据库。
如果用户不知道该选哪个数据库或数据集，再使用中文研究问题检索。
```

### 11.3 本地数据导入

本地导入放在第一位。

它是最基础、最直接的数据入口。

本地导入需要支持两种模式：

```text
复制到项目目录
按原路径引用
```

如果用户选择外置磁盘或本地已有文件，并选择不复制，只按原路径操作，则该数据来源状态应显示为：

```text
已记录
```

而不是“已下载”。

### 11.4 GEO / TCGA / GTEx

GEO、TCGA、GTEx 三个数据库并列展示。

它们是三个最常见的数据来源，应作为同级公共数据库入口。

但每个卡片内部应根据数据库自身特点组织功能：

```text
GEO：
- GSE 编号检索
- Series Matrix / supplementary files
- 样本注释
- 平台信息

TCGA：
- 项目选择
- 癌种 / project
- metadata preview
- raw download
- expression matrix build
- clinical metadata

GTEx：
- tissue / organ
- normal tissue reference
- expression resource
- 与 TCGA 的边界说明，不自动合并
```

页面一级看起来并列，但进入各自卡片后，不能强行做成完全相同的表单。

### 11.5 中文研究问题检索

中文研究问题检索作为单独卡片，放在 GEO / TCGA / GTEx 三个数据库卡片的下方。

它不是唯一入口，也不替代数据库入口。

适用情况：

- 用户不知道应该选 GEO、TCGA 还是 GTEx；
- 用户不知道具体 GSE 编号；
- 用户只有中文研究问题；
- 用户希望得到候选数据集建议。

该卡片应明确：

```text
候选结果需要人工确认。
不会自动下载。
不会自动确认研究设计。
不会自动决定最终数据来源。
```

### 11.6 数据来源状态：已记录 / 已下载

数据来源页中的数据获取状态重点区分两个状态：

```text
已记录
已下载
```

#### 已记录

“已记录”表示该数据来源已经被项目登记，但数据文件不一定已经复制或下载到项目目录。

包括两种情况：

1. 用户检索并选择了某些公共数据集，但尚未下载；
2. 用户选择了本地或外置磁盘上的数据文件，但没有复制到项目目录，只按原路径引用。

显示示例：

```text
状态：已记录
来源：TCGA
数据：TCGA-THCA
说明：已选择数据来源，等待下载。

状态：已记录
来源：本地文件
路径：/Volumes/ExternalDisk/project/expression_matrix.tsv
说明：按原路径引用，未复制到项目目录。
```

#### 已下载

“已下载”表示公共数据库数据已经下载到本地，或者项目目录中已经存在对应数据文件。

显示示例：

```text
状态：已下载
来源：GEO
数据：GSEXXXXX
文件：Series Matrix 已下载
下一步：运行数据检查
```

### 11.7 当前项目数据来源区域

数据来源页下方应有一个区域，建议命名为：

```text
当前项目数据来源
```

也可使用：

```text
已记录的数据来源
```

不建议叫：

```text
Acquisition Status
```

因为 acquisition 是技术术语。

主视图只显示摘要：

- 来源名称；
- 来源类型；
- 当前状态：已记录 / 已下载；
- 下一步操作。

示例：

```text
当前项目数据来源

TCGA-THCA
类型：TCGA 数据库
状态：已记录
下一步：下载数据
[展开详情]

GSEXXXXX
类型：GEO 数据库
状态：已下载
下一步：运行数据检查
[展开详情]

local_expression.tsv
类型：本地数据
状态：已记录
下一步：运行数据检查
[展开详情]
```

### 11.8 所有详情默认折叠

数据来源页中，所有详细信息默认折叠。

普通用户主视图只显示极简摘要，不展开路径、文件类型、引用方式、下载计划、manifest 等内容。

默认折叠的信息包括：

- 本地文件路径；
- 文件类型；
- 引用方式：复制到项目 / 原路径引用；
- 数据库来源；
- 数据集编号；
- 本地保存位置；
- 下载状态细节；
- download plan；
- receipt；
- manifest；
- cache path；
- internal id；
- source record；
- raw path。

用户需要时才手动展开查看。

### 11.9 技术详情

技术详情仍然可以存在，但必须默认折叠。

可包含：

- source record；
- download plan；
- receipt；
- manifest；
- raw path；
- cache path；
- internal id。

普通用户主视图只回答：

```text
我记录了什么数据？
数据有没有下载？
数据在哪里？
下一步该做什么？
```

### 11.10 数据来源页结构草稿

```text
数据来源 / Data Source

顶部：
选择或登记数据来源

第一部分：
[本地数据导入]

第二部分：
公共数据库
[GEO 数据库]   [TCGA 数据库]   [GTEx 数据库]

第三部分：
不知道选哪个数据集？
[中文研究问题检索]
输入中文研究问题，生成 GEO / TCGA / GTEx 候选。候选结果需要人工确认。

第四部分：
当前项目数据来源
- 来源名称
- 类型
- 状态：已记录 / 已下载
- 下一步
- 展开详情

所有详情：
默认折叠
```

---

## 12. 后续 Codex 实现原则

后续交给 Codex 实现本文件相关内容时，应遵守：

1. 不进入 Figma；
2. 不做高保真视觉；
3. 不生成图标；
4. 不把 planned 功能伪装为可用；
5. 不把 technical diagnostics 放入普通用户主视图；
6. Settings 按“常规设置 / 账户与订阅 / 本地项目与存储 / 外部引擎与模型 / 开发者诊断”组织；
7. 外部引擎与模型包含图像分析引擎、PDF 识别与 OCR 引擎、本地语言模型、云端 AI 服务；
8. 主导航包含 Dashboard、Bioinformatics、Meta Analysis、LabTools、Settings；
9. 测试反馈和关于放在底部或辅助入口；
10. Bioinformatics 从历史 13 个页面收敛到 7–8 个主页面；
11. Project Home 作为项目状态总览和下一步引导页；
12. Project Home 不显示 Developer Preview · 测试中；
13. Data Source 页面按本地导入、GEO、TCGA、GTEx、中文研究问题检索组织；
14. 中文研究问题检索作为单独卡片，放在三个数据库下方；
15. 数据来源状态区分“已记录”和“已下载”；
16. 所有数据来源详情默认折叠；
17. UI-05 Acquisition Status 不再作为普通用户独立页面，应并入 Data Source 或降级为技术详情。

---

## 13. 当前确认决策摘要

已确认：

```text
1. Settings 分为常规设置、账户与订阅、本地项目与存储、外部引擎与模型、开发者诊断。
2. 本地 AI 和外部引擎合并为“外部引擎与模型”。
3. 外部引擎与模型包含：图像分析引擎、PDF 识别与 OCR 引擎、本地语言模型、云端 AI 服务。
4. 未来联网商业 AI 统一称为：云端 AI 服务。
5. PDF 识别与 OCR 引擎用于 Meta Analysis 全文 PDF 转换和文字识别，不归入实验图像分析。
6. 左侧主导航为 Dashboard、Bioinformatics、Meta Analysis、LabTools、Settings。
7. 测试反馈和关于作为底部或辅助入口。
8. Bioinformatics 页面从当前约 13 个页面收敛为 7–8 个主页面。
9. Bioinformatics Project Home 是项目状态总览 + 推荐下一步，不显示 Developer Preview · 测试中。
10. Bioinformatics Data Source 顺序为：本地导入、GEO、TCGA、GTEx、中文研究问题检索。
11. 中文研究问题检索是单独卡片，放在三个数据库下方，作为辅助智能搜索入口。
12. 数据来源状态区分已记录和已下载。
13. 所有数据来源详情默认折叠。
```

---

## 14. 后续待讨论项

后续仍需继续讨论：

1. Bioinformatics：数据检查与准备 / Data Check & Preparation；
2. Bioinformatics：分组与分析设计 / Group & Design；
3. Bioinformatics：分析任务 / Analysis Tasks；
4. Bioinformatics：结果浏览 / Results；
5. Bioinformatics：报告导出 / Report；
6. Bioinformatics：生信设置 / Bioinformatics Settings；
7. Meta Analysis 的 shell-only 与目标结构；
8. LabTools 模块级信息架构重构；
9. 测试反馈页面内容；
10. Settings 各子页面的具体布局。
