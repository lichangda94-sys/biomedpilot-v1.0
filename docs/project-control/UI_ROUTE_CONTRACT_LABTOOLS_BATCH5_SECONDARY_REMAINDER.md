# UI Route Contract LabTools Batch 5: Secondary Remainder

- Created: `2026-06-02T14:00:51+00:00`
- Branch: `integration/release-bio-c1-ui-shell`
- HEAD: `6ffcbe7a650809cbbf25df8842619322d177f83d`
- Scope: LabTools remaining secondary modules: connect Nucleic Acid qPCR mix adapter; keep Immunoassay/Absorbance and IHC disabled with explicit reasons.

## Summary

- Rows: 11
- Connected: 6
- Disabled with reason: 5
- Broken: 0

## Screenshots

- `01_nucleic_qpcr_adapter` / `nucleic_acid_experiments`: `/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260602_labtools_batch5_secondary_remainder/01_nucleic_qpcr_adapter.png`
- `02_immuno_absorbance_disabled` / `immuno_absorbance`: `/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260602_labtools_batch5_secondary_remainder/02_immuno_absorbance_disabled.png`
- `03_ihc_disabled` / `ihc`: `/Users/changdali/Developer/biomedpilot v1.0/Integration/docs/ui/runtime_screenshots/20260602_labtools_batch5_secondary_remainder/03_ihc_disabled.png`

## Rows

| Contract | Surface | Object | Status | Behavior | Evidence |
| --- | --- | --- | --- | --- | --- |
| `LABTOOLS-SECONDARY-NUCLEIC-NAV` | Nucleic Acid | `labtoolsSecondaryEntryButton` | connected | `navigates_to_labtools_secondary_nucleic_acid_experiments` | current_page_key=nucleic_acid_experiments |
| `LABTOOLS-NUCLEIC-QPCR-ADAPTER-PRESENT` | Nucleic Acid | `nucleicAcidExperimentTabs` | connected | `hosts_qpcr_mix_adapter_and_disabled_remaining_gates` | tabs=4 |
| `LABTOOLS-NUCLEIC-QPCR-CALCULATE` | Nucleic Acid qPCR | `qpcrMixCalculateButton` | connected | `calculates_qpcr_mix_plan` | qPCR 配液计算 /  / 结果 / master mix：单反应 10 µL；总用量 100 µL；含 overage 110 µL / forward primer：单反应 0.4 µL；总用量 4 µL；含 overage 4.4 µL / reverse primer：单反应 0.4 µL；总用量 4 µL；含 overage 4.4 µL / template / cDNA：单反应 2 µL；总用量 20 µL；含 overage 22 µL / nuclease-free water：单反应 7.2 µL；总用量 72 µL；含 overage 79.2 µL /  / 说明 / qPCR 配液结果为实验辅助草稿，使用前需人工核对 master mix 类型、primer/template 浓度、重复数、阴阳性对照和实验 SOP。 /  / 人工核对提示 / 计算结果为实验辅助草稿，使用前需结合实验 SOP、试剂说明书和人工复核；不构成临床、诊断或安全操作建议。 |
| `LABTOOLS-NUCLEIC-QPCR-COPY` | Nucleic Acid qPCR | `qpcrMixCopyResultButton` | connected | `copies_qpcr_mix_result_after_calculation` | qPCR 配液计算 /  / 结果 / master mix：单反应 10 µL；总用量 100 µL；含 overage 110 µL / forward primer：单反应 0.4 µL；总用量 4 µL；含 overage 4.4 µL / reverse primer：单反应 0.4 µL；总用量 4 µL；含 overage 4.4 µL / template / cDNA：单反应 2 µL；总用量 20 µL；含 overage 22 µL / nuclease-free water：单反应 7.2 µL；总用量 72 µL；含 overage 79.2 µL /  / 说明 / qPCR 配液结果为实验辅助草稿，使用前需人工核对 master mix 类型、primer/template 浓度、重复数、阴阳性对照和实验 SOP。 /  / 人工核对提示 / 计算结果为实验辅助草稿，使用前需结合实验 SOP、试剂说明书和人工复核；不构成临床、诊断或安全操作建议。 |
| `LABTOOLS-NUCLEIC-GATE-nucleicPrimerRegistryGateDisabledButton` | Nucleic Acid | `nucleicPrimerRegistryGateDisabledButton` | disabled | `disabled_primer_registry_not_connected` | Primer registry, validation, and persistence are not connected in this release batch. |
| `LABTOOLS-NUCLEIC-GATE-nucleicPcrProgramGateDisabledButton` | Nucleic Acid | `nucleicPcrProgramGateDisabledButton` | disabled | `disabled_pcr_program_record_not_connected` | PCR/qPCR program templates, thermal-cycler profile storage, and run history are not connected in this release batch. |
| `LABTOOLS-NUCLEIC-GATE-nucleicResultProcessingGateDisabledButton` | Nucleic Acid | `nucleicResultProcessingGateDisabledButton` | disabled | `disabled_nucleic_result_processing_not_connected` | Ct/Cq import, delta-delta-Ct, melt-curve review, and report export gates are not connected in this release batch. |
| `LABTOOLS-SECONDARY-IMMUNO_ABSORBANCE-NAV` | 免疫与吸光度实验 | `labtoolsSecondaryEntryButton` | connected | `navigates_to_labtools_secondary_immuno_absorbance` | current_page_key=immuno_absorbance |
| `LABTOOLS-SECONDARY-IMMUNO_ABSORBANCE-DISABLED-GATE` | 免疫与吸光度实验 | `labToolsC1DisabledActionButton` | disabled | `disabled_labtools_secondary_backend_not_connected` | ELISA/BCA formal records, curve fitting, and report export are not connected in C1. |
| `LABTOOLS-SECONDARY-IHC-NAV` | 免疫组化 | `labtoolsSecondaryEntryButton` | connected | `navigates_to_labtools_secondary_ihc` | current_page_key=ihc |
| `LABTOOLS-SECONDARY-IHC-DISABLED-GATE` | 免疫组化 | `labToolsC1DisabledActionButton` | disabled | `disabled_labtools_secondary_backend_not_connected` | IHC record model, review workflow, and Settings-linked image assistance are not connected in C1. |
