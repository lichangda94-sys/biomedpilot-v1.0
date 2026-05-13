# CODEX.md - MainLine

## 当前工作区

路径：/Users/changdali/Developer/biomedpilot v1.0/MainLine  
分支：stable/mainline  

## 职责

本工作区只负责总应用树干、桌面壳、登录、模块选择、设置、测试模式、Bioinformatics 稳定主流程、Shared 接口、Meta 最小入口。

## 当前第一任务

修复 mainline GUI import 阻塞：

`app/bioinformatics/workflow_pages.py` 引用了不存在的 `app/bioinformatics/deg_executor_preflight.py`，导致 UI 初始化失败。

## 禁止事项

- 不要开发完整 Meta workflow。
- 不要提交 shared vocabulary 大资产。
- 不要生成假 DEG。
- 不要把 PubMed 放进 Bioinformatics 数据检索。
- 不要绕过 AI Gateway。
- 不要保存 raw prompt / response。
- 不要在主 UI 暴露 manifest、schema、branch、raw path。

## 测试
