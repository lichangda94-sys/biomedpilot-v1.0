# Meta Runtime Seed Correction Report

Generated: 2026-05-18

Scope: existing Meta runtime seed 11 entries and shared promotion 4 entries only. No shared core entries were added or modified.

| zh term | preferred label | final decision | shared promotion decision | reason |
| --- | --- | --- | --- | --- |
| 乳腺癌 | breast cancer | approved_runtime_ok | align_existing_shared_concept: mini:breast_cancer | Disease seed is semantically aligned across Meta and Bioinformatics; align to the existing shared concept only. |
| 甲状腺癌 | thyroid cancer | approved_runtime_ok | align_existing_shared_concept: mini:thyroid_cancer | Disease seed is semantically aligned across Meta and Bioinformatics; align to the existing shared concept only. |
| 2型糖尿病 | type 2 diabetes mellitus | approved_runtime_ok | align_existing_shared_concept: mini:type_2_diabetes_mellitus | Disease seed is semantically aligned across Meta and Bioinformatics; align to the existing shared concept only. |
| 肥胖 | obesity | needs_type_fix | blocked_from_shared_promotion | Meta uses risk_factor/exposure semantics while shared core currently carries disease/phenotype semantics. BMI/body mass index were moved to measurement terms, and overweight was downgraded to related term. |
| 糖尿病前期 | prediabetes | needs_type_fix | meta_only_not_shared | Corrected from generic exposure to phenotype_risk_state while retaining PICO exposure role. Expansion requires population/disease context and must not expand to type 2 diabetes. |
| 二甲双胍 | metformin | approved_runtime_ok | meta_only_not_shared | Valid Meta intervention seed; intervention terms are not shared-core promotion candidates in this stage. |
| 放射性碘治疗 | radioactive iodine therapy | approved_runtime_ok | meta_only_not_shared | Valid Meta intervention seed; intervention terms are not shared-core promotion candidates in this stage. |
| 复发 | recurrence | needs_expansion_guard | meta_only_not_shared | Valid outcome seed, but it must not trigger unconditional topic expansion and is no longer standalone-searchable. |
| 风险 | risk | approved_runtime_ok | meta_only_not_shared | Research intent marker only; query expansion remains disabled and standalone search remains disabled. |
| 危险因素 | risk factor | approved_runtime_ok | meta_only_not_shared | Research intent marker only; query expansion remains disabled and standalone search remains disabled. |
| Meta分析 | meta-analysis | approved_runtime_ok | meta_only_not_shared | Study-design/review marker only. It may be used as a filter but not as a topic expansion. |

Shared promotion correction:

| term | decision |
| --- | --- |
| 2型糖尿病 | align_existing_shared_concept; do not create a new shared concept. |
| 乳腺癌 | align_existing_shared_concept; do not create a new shared concept. |
| 甲状腺癌 | align_existing_shared_concept; do not create a new shared concept. |
| 肥胖 | blocked_from_shared_promotion until shared disease/phenotype semantics and Meta risk_factor/exposure semantics are reconciled. |
