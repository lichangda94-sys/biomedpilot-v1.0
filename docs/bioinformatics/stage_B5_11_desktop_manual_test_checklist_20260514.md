# Stage B5.11 Desktop Manual Test Checklist

Date: 2026-05-14

Scope: desktop manual test checklist for the local import -> recognition -> standardization confirmation -> DEG preflight readiness / imported result readiness -> report draft loop.

This stage is docs-only. Do not modify runtime code, package the app, overwrite desktop entry points, push remotely, or delete `docs/bioinformatics/Bioinformatics_handoff_report_20260513.md`.

## Test Data

Prepare a local folder with 4 files:

- One GEO Series Matrix file, preferably `GSE*_series_matrix.txt.gz`.
- One `*_family.soft` file with only metadata/platform annotation, or one with `ID_REF/VALUE` sample table.
- One XLSX processed matrix with count / FPKM / DEG / gene annotation candidate sheets or columns.
- One imported DEG result table or another tabular file that should not be treated as raw expression.

Record test file names:

| Slot | File Name | Expected Role |
| --- | --- | --- |
| 1 |  | Series Matrix expression / metadata candidate |
| 2 |  | family.soft metadata or expression candidate |
| 3 |  | XLSX count / FPKM / DEG / annotation candidates |
| 4 |  | imported DEG or non-expression tabular candidate |

## 1. Local Multi-file Import

| Step | Expected Result | Pass |
| --- | --- | --- |
| Open Bioinformatics desktop app and create or open a test project. | Project opens without crash. |  |
| Go to local data import. | Local import controls are visible. |  |
| Select the 4 prepared files in one import action. | Status shows that 4 files were selected. |  |
| Check the pending dataset table. | Dataset / filename displays `本地导入批次：4 个文件` or equivalent batch name, not only the first filename. |  |
| Check available content column. | Shows `待识别：4 个文件`. |  |
| Check notes column. | Shows `包含 <第一个文件名> 等 4 个文件`. |  |
| Open import details. | Full list of all 4 file names is visible. |  |
| Check storage/source status. | Details show whether files use original locations or were copied into the project. |  |
| Check raw path exposure. | Main UI does not expose raw absolute paths; full paths appear only in detail or developer diagnostics if needed. |  |

Failure triggers:

- Only the first file is shown as the sole data source.
- Details omit any selected file.
- `source_files` / selected-file handoff appears reduced to one file.

## 2. Data Recognition

Run data recognition for the imported batch.

| Item | Expected Result | Pass |
| --- | --- | --- |
| Series Matrix row is present. | Shows GEO Series Matrix source file as its own file-level result. |  |
| Series Matrix parser depth. | Shows `parser_depth` such as `metadata_parsed`, `matrix_detected`, or `matrix_previewed`. |  |
| Series Matrix sample count. | Shows parsed sample count. |  |
| Series Matrix matrix presence. | Shows whether expression matrix region was detected. |  |
| Series Matrix ID_REF warning. | Explains `ID_REF` may be platform probe ID and needs platform annotation / ID mapping confirmation. |  |
| family.soft row is present. | Shows family.soft as its own file-level result. |  |
| family.soft parser depth. | Shows SOFT `parser_depth`, not “complete parse” unless table structure is actually parsed. |  |
| family.soft metadata. | Shows sample/platform metadata and platform annotation presence when available. |  |
| family.soft expression candidate. | Only SOFT with confirmed `ID_REF/VALUE` table appears as expression candidate and requires user confirmation. |  |
| XLSX candidates. | Shows count / FPKM / DEG / gene annotation candidates according to workbook content. |  |
| Source separation. | XLSX result is not attached under SOFT; SOFT result does not inherit XLSX count/FPKM/DEG assets. |  |
| Shallow parse wording. | Shallow SOFT or metadata-only Series Matrix is not described as fully parsed expression matrix. |  |

Failure triggers:

- XLSX candidates appear under family.soft.
- metadata-only SOFT or Series Matrix unlocks expression readiness.
- UI says or implies full expression parsing when only metadata/container parsing happened.

## 3. Standardization Confirmation

Open the standardization page and inspect the confirmation candidate area.

| Candidate Area | Expected Result | Pass |
| --- | --- | --- |
| Expression matrix candidates | Series Matrix / SOFT table / XLSX expression candidates appear with source file and parser. |  |
| Sample metadata candidates | SAMPLE / Sample metadata candidates appear with source file and parser. |  |
| Group candidates | Candidate phenotype/group fields from characteristics/source/title/treatment protocol are visible as candidates only. |  |
| Species evidence | Species evidence shows species name, source field, source file, and confidence. |  |
| Gene ID / probe ID candidates | Shows Ensembl / Entrez / Gene Symbol / Probe ID / unknown candidate. Probe ID is not shown as gene symbol. |  |
| Platform annotation candidates | Platform annotation or platform reference candidates are visible. |  |
| Imported DEG candidates | External DEG result candidates are visible as imported results, not recomputed results. |  |
| Confirmation manifest refresh | Refresh or generate action can create/update `manifests/standardization_confirmation.json`. |  |
| Main UI path hygiene | Main confirmation table shows source file names, not raw absolute paths. |  |

Manual confirmation checks:

| Operation | Expected Result | Pass |
| --- | --- | --- |
| Confirm an expression candidate with `unknown` expression value type. | Manifest updates, but DEG preflight readiness remains false. |  |
| Confirm an expression candidate with `count_like_candidate` but do not confirm value type. | Manifest updates, but DEG preflight readiness remains false. |  |
| Confirm `count_like_candidate` explicitly. | Expression value type confirmation is saved. |  |
| Confirm species. | `species_confirmed` is saved with source or manual confirmation flag. |  |
| Confirm gene ID type as `probe_id`. | Manifest saves `probe_id` and warns that platform mapping is needed. |  |
| Confirm candidate group design. | `confirmed_group_design.group_confirmed=true` appears in manifest. |  |

## 4. Readiness Checks

Run readiness check after each relevant confirmation step.

| Scenario | Expected Result | Pass |
| --- | --- | --- |
| Expression candidate exists but expression value type is not confirmed. | `standardization_confirmed=false`. |  |
| Expression value type is `unknown`. | `deg_preflight_ready=false`. |  |
| Expression value type is `count_like_candidate` but not confirmed. | `deg_preflight_ready=false`. |  |
| Group design is not confirmed. | `deg_preflight_ready=false`. |  |
| Expression is `count` or confirmed `count_like_candidate`, and group design is confirmed. | `deg_preflight_ready=true`. |  |
| Imported DEG candidate exists. | `imported_result_ready=true`, but it is not described as real computed result. |  |
| No real DEG executor is run. | No limma / DESeq2 / edgeR execution occurs. |  |

Expected manifest fields:

```json
{
  "selected_expression_candidate": {},
  "expression_value_type_confirmed": {},
  "selected_sample_metadata_candidate": {},
  "confirmed_group_design": {},
  "species_confirmed": {},
  "gene_id_type_confirmed": {},
  "platform_annotation_confirmed": {},
  "readiness": {
    "standardization_confirmed": false,
    "deg_preflight_ready": false,
    "imported_result_ready": false
  }
}
```

## 5. Report Checks

Refresh or generate the report draft after recognition, standardization confirmation, and readiness checks.

| Check | Expected Result | Pass |
| --- | --- | --- |
| Imported DEG wording | Report describes imported DEG as user-imported external result. |  |
| Real DEG status | Report states real DEG executor is not currently open / not run. |  |
| No raw absolute path | Main report text does not expose local raw absolute paths. |  |
| No pseudo conclusion | Report does not say the software discovered differential genes. |  |
| No publication claim | Report does not claim results are publishable. |  |
| No formal DEG result wording | Report does not call candidate/preflight/imported state a formal DEG result. |  |
| Report semantics | Preflight is described as input check only, not analysis execution. |  |

Forbidden wording scan for report and visible UI:

- `本软件发现`
- `可用于发表`
- `正式 DEG 结果`
- `已完成标准化`
- `可直接做 DEG`

## 6. Issue Log

| 页面 | 操作 | 期望结果 | 实际结果 | 是否通过 | 严重程度 | 备注 |
| --- | --- | --- | --- | --- | --- | --- |
| 本地数据导入 | 选择 4 个文件 | 显示本地导入批次和完整详情 |  |  |  |  |
| 数据识别 | 运行识别 | Series Matrix / SOFT / XLSX 各自独立显示 |  |  |  |  |
| 标准化确认 | 刷新候选 | 候选资产来源和 parser 清晰 |  |  |  |  |
| 标准化确认 | 确认表达值类型 | Manifest 写入确认状态 |  |  |  |  |
| 标准化确认 | 确认分组 | `group_confirmed=true` |  |  |  |  |
| Readiness | 重新检查 | readiness 符合确认状态 |  |  |  |  |
| 报告草稿 | 刷新报告 | 不出现伪结论或 raw path 泄漏 |  |  |  |  |

Severity guide:

- P0: crash, data loss, destructive action, wrong file deletion.
- P1: raw path leak in main UI/report, parser source mixed between files, false real-DEG conclusion, readiness gate wrong.
- P2: missing warning, confusing parser depth, incomplete candidate display.
- P3: wording polish, layout issue that does not block test.

## 7. Pass Criteria

Pass and proceed to B6 only if all are true:

- Local multi-file import shows batch-level display and full file details.
- Recognition keeps Series Matrix, family.soft, XLSX, and imported DEG candidates file-scoped.
- Standardization confirmation shows candidates with source file, parser, parser depth, warnings, and confirmation status.
- `standardization_confirmation.json` persists expression, value type, group, species, gene ID, platform, and readiness fields.
- Readiness semantics match user confirmations.
- Imported DEG candidates remain external imported results, not real recomputed results.
- Report draft has no raw absolute path leak and no pseudo scientific conclusion.

Do not enter B6 yet if any of the following occurs:

- Raw path leak in main UI or report.
- Parser source confusion, such as XLSX assets appearing under SOFT.
- Any pseudo conclusion or formal DEG wording before a real executor exists.
- Crash or frozen UI.
- Readiness status contradicts the confirmation manifest.

If all pass, recommended next stage:

- B6 — Real DEG Executor Pre-audit, after this desktop manual UI test passes.
