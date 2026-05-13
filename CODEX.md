# CODEX.md - Bioinformatics

## 当前工作区

路径：/Users/changdali/Developer/biomedpilot v1.0/Bioinformatics  
分支：dev/bioinformatics 或 dev/bioinformatics-analysis  

## 职责

本工作区负责 Bioinformatics Analysis / 生信分析模块。

主流程：

项目首页 -> 数据选择 -> 数据识别 -> 数据标准化 -> 分析任务中心 -> 结果浏览 -> 项目报告

## 当前优先任务

1. 数据选择页和中文研究主题检索独立页。
2. GSE 详情页和下载列表。
3. 标准化页从调试页改成用户流程页。
4. DEG preflight：输入物化与强校验。

## 禁止事项

- 不要执行 PubMed 文献检索作为生信数据结果。
- 不要把 Meta 文献候选混入生信。
- 不要生成假 DEG、假火山图、假富集结果。
- 不要把 dry-run 写成真实分析。
- 不要让 AI 直接执行下载或分析。
- 不要保存 raw prompt / response。
- 不要在主 UI 暴露大量 manifest、asset id、raw path。

## 测试
