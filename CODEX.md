# CODEX.md - Vocabulary

## 当前工作区

路径：/Users/changdali/Developer/biomedpilot v1.0/Vocabulary  
分支：dev/shared-vocabulary  

## 职责

本工作区负责共享医学词库。

核心目录：
- data/medical_terms/
- app/shared/query_intelligence/medical_terms/
- scripts/audit_medical_vocabulary_coverage.py
- scripts/update_medical_term_index.py
- tests/shared/

## 当前优先任务

1. short-token / modality-only false positive hardening。
2. 减少 Bioinformatics search_center 中重复硬编码 fallback。
3. unknown term review queue。
4. legacy 词库迁移计划。

## 禁止事项

- 不要让 Bioinformatics 和 Meta 各自维护疾病词库副本。
- 不要把本地模型输出直接写入正式词库。
- 不要直接全量导入 ontology 到 runtime。
- 不要破坏 Bioinformatics / Meta context isolation。
- 不要修改词库后不跑 audit 和 tests。

## 测试
