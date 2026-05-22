# LabTools Western Blot Loading Record

Product: BioMedPilot / LabTools
Record type: western_blot_loading
Experiment / Tool: WB Loading
Created at: 2026-05-22T00:00:00+08:00
Operator: demo user
Project: not attached
Sample / Template: S1/S2/S3 loading demo
Storage status: disabled_missing_storage_adapter
Export status: disabled_missing_file_picker
Software version: 0.1.0 internal beta

## WB Configuration

| Field | Value |
|---|---|
| Target protein per lane | 20 ug |
| Sample buffer | 4x |
| Final loading volume | 20 uL |
| Reducing agent | yes |
| Denaturation | 95 C, 5 min |

## Sample Inputs

| Sample ID | Protein Concentration | Unit | Note |
|---|---:|---|---|
| S1 | 2.0 | ug/uL | control |
| S2 | 1.5 | ug/uL | treatment low |
| S3 | 0.8 | ug/uL | treatment high |

## Loading Result

| Sample ID | Sample Volume | 4x Buffer | Water | Total | Status |
|---|---:|---:|---:|---:|---|
| S1 | 10.0 uL | 5.0 uL | 5.0 uL | 20.0 uL | OK |
| S2 | 13.3 uL | 5.0 uL | 1.7 uL | 20.0 uL | OK |
| S3 | 25.0 uL | 5.0 uL | -10.0 uL | 20.0 uL | Warning |

## Lane Layout Summary

- Lane 1: Marker
- Lane 2: S1, 20 uL
- Lane 3: S2, 20 uL
- Lane 4: S3, 20 uL, warning
- Remaining lanes: Empty / 空白

## Warnings

- S3 sample volume exceeds final loading volume; water volume is negative.
- Lane layout is schematic and does not represent a gel image.
- This page does not provide image analysis, band quantification, or antibody recommendation.

## Review Notice

本记录由 LabTools 生成，仅作为实验计算和记录辅助。
所有结果需由实验人员复核后用于台面操作。

## Disabled Actions

- Save WB record: disabled_missing_storage_adapter
- Export CSV / Markdown: disabled_missing_file_picker
- History: disabled_missing_storage_adapter
