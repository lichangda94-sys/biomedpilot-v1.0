# LabTools Cell Records Structure Template

Product: BioMedPilot / LabTools
Record type: cell_records_structure
Experiment / Tool: Cell Experiment Workspace
Created at: 2026-05-22T00:00:00+08:00
Operator: demo user
Project: not attached
Sample / Template: A549 shell example
Storage status: blocked_until_backend
Export status: blocked_until_backend
Software version: 0.1.0 internal beta

## Cell Profile

| Field | Example |
|---|---|
| Cell line | A549 |
| Species | human |
| Tissue | lung |
| Current passage | P8 |
| Culture condition | DMEM + 10% FBS |
| Current state | culture_in_progress |

## Planned Record Templates

- Passage
- Thawing
- Freezing
- Seeding
- Treatment
- Transfection

## Boundary

- Real save is blocked until CellExperimentRecordStore exists.
- Timeline persistence is not active.
- Do not show fake records or fake timeline events.
- ImageJ/Fiji is a Settings-linked external capability only.

## Review Notice

本记录由 LabTools 生成，仅作为实验计算和记录辅助。
所有结果需由实验人员复核后用于台面操作。
