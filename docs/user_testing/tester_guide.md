# BioMedPilot Tester Guide

This guide is for first-round external testers. The goal is to check whether the
software opens clearly, lets you create simple projects, and makes unfinished
features obvious.

## 1. Start The Software

From the project folder, run:

```bash
python3 scripts/run_app.py
```

If the app opens correctly, you should see the BioMedPilot Dashboard with:

- `BioMedPilot / 医研智析`
- `新建生信项目`
- `新建 Meta 项目`
- recent projects
- environment status
- Testing Mode entry in the left navigation

## 2. Create A Bioinformatics Project

1. On the Dashboard, click `新建生信项目`.
2. Enter a project name, for example `GEO test project`.
3. Confirm the dialog.
4. The app should enter the Bioinformatics workspace.
5. Check that the page lists data search/import, download, asset detection,
   cleaning, and sample grouping steps.
6. In `数据检索 / 导入`, enter a GEO search term or GSE accession.
7. Click `生成 GEO 查询计划`.
8. Confirm that the output path is shown and that the page says online search was not executed.
9. Copy the GEO query plan output path into `数据下载`.
10. Click `生成下载计划`.
11. Confirm that the download plan says actual download was not executed and requires user confirmation.
12. Copy the GEO download plan output path into `数据资产识别`.
13. Click `识别本地数据资产`.
14. Confirm that the page says no network was used. If the local target folder is empty, it should report zero expression candidates clearly.
15. Copy the asset detection output path into `数据清洗`.
16. Click `生成清洗计划`.
17. Confirm that the page reports whether each local dataset has expression matrix candidates. It should also say matrix standardization was not executed.
18. Copy the cleaning plan output path into `样本分组`.
19. Click `生成样本分组计划`.
20. Confirm that the page reports whether sample annotation candidates exist. It should also say automatic group inference and differential analysis were not executed.
21. Copy the sample grouping plan output path into `差异表达分析`.
22. Click `运行差异分析预检`.
23. Confirm that the page checks expression matrix, sample annotation, and case/control group readiness. It should also say formal differential statistics were not executed.

## 3. Create A Meta Analysis Project

1. Return to the Dashboard from the left navigation.
2. Click `新建 Meta 项目`.
3. Enter a project name, for example `Meta test project`.
4. Confirm the dialog.
5. The app should enter the Meta Analysis workspace.
6. Check that the page lists literature import, deduplication, screening,
   extraction, analysis, and reporting steps.

## 4. Recommended Test Flow

1. Start the app.
2. Create one Bioinformatics project.
3. Return to the Dashboard.
4. Create one Meta Analysis project.
5. In the Meta Analysis workspace, find `文献导入`.
6. Paste or choose a `.nbib`, `.ris`, or `.csv` literature file.
7. Click `导入`.
8. Confirm that the result summary shows the source file, format, total records,
   imported records, and output path.
9. Copy the Literature Import output path into `去重准备 / Prepare for Screening`.
10. Click `准备筛选记录`.
11. Confirm that the result summary shows total records, prepared records, and output path.
12. Copy the Prepare for Screening output path into `Duplicate Review`.
13. Click `生成重复候选摘要`.
14. Confirm that the summary shows total records, duplicate candidate groups, candidate record count, and output path.
15. Copy either the Duplicate Review output path or the Prepare for Screening output path into `Screening / 标题摘要筛选`.
16. Click `生成标题摘要筛选队列`.
17. Confirm that the summary shows total records, pending records, and output path.
18. In the Screening section, copy one `screening_record_id` from the generated JSON output.
19. Enter the Screening output path, the `screening_record_id`, and a decision such as `included`, `excluded`, `maybe`, or `pending`.
20. Click `保存筛选决策`. If you use `excluded`, also enter an exclusion reason.
21. Confirm that the decision counts update clearly.
22. Copy the Screening output path into `Extraction / 数据提取`.
23. Click `生成数据提取池`.
24. Confirm that included records become extraction records, and that the app clearly reports zero records if no item was marked included.
25. Copy the Extraction output path into `Analysis / Meta 统计分析预检`.
26. Click `运行 Analysis 预检`.
27. Confirm that the result clearly says whether formal statistics can run. In this build it will usually report missing outcome data.
28. Copy the Analysis preflight output path into `Reporting / 报告导出`.
29. Click `导出测试报告摘要`.
30. Confirm that a Markdown report path is shown and that the report says no pooled meta-analysis was executed.
31. Return to the Dashboard and click each recent project.
32. Open `测试模式`.
33. Generate a feedback template.
34. Record anything confusing, broken, missing, or mislabeled.

## 5. Features To Test Now

- Dashboard layout and wording.
- Project creation for both project types.
- Recent project list.
- Workspace switching.
- Bioinformatics `数据检索 / 导入` GEO query plan and GSE accession import record.
- Bioinformatics `数据下载` GEO download plan generation without actual NCBI download.
- Bioinformatics `数据资产识别` local scan from a GEO download plan, without network use.
- Bioinformatics `数据清洗` preflight plan from asset detection output, without running matrix standardization.
- Bioinformatics `样本分组` preflight plan from cleaning output, without automatic case/control inference.
- Bioinformatics `差异表达分析` preflight from sample grouping output, without p-values, FDR, limma, DESeq2, or edgeR.
- Meta Analysis `文献导入` for NBIB / RIS / CSV files.
- Meta Analysis `去重准备 / Prepare for Screening` using the Literature Import output JSON.
- Meta Analysis `Duplicate Review` summary using the Prepare for Screening output JSON.
- Meta Analysis `Screening / 标题摘要筛选` queue generation and minimal decision save using Prepare or Duplicate Review output JSON.
- Meta Analysis `Extraction / 数据提取` pool generation from Screening output JSON, including clear handling when no records are marked included.
- Meta Analysis `Analysis / Meta 统计分析预检` using Extraction output JSON. This checks readiness only and does not run pooled statistics.
- Meta Analysis `Reporting / 报告导出` test Markdown summary from Analysis preflight output.
- Feature status labels: `已开放`, `测试中`, `待接入`, `暂未开放`.
- Testing Mode page and feedback template generation.

## 6. Features Not Ready For Testing

Do not treat the following as completed workflows yet:

- formal bioinformatics differential expression analysis beyond readiness/preflight
- live GEO online search and GEO data download as complete workflows
- automatic Bioinformatics sample group inference and manual group editing
- enrichment analysis
- correlation analysis
- survival analysis
- complete Meta statistical analysis beyond the preflight readiness check
- Meta manual duplicate merge decisions, full multi-reviewer Screening workflow, manual Extraction forms, Analysis, and Reporting as complete end-to-end workflows
- final report export workflows beyond the test Markdown preflight summary
- installer/package generation

## 7. How To Record Errors

Please record:

- what you clicked
- what you expected
- what actually happened
- any message shown by the app
- screenshot if possible
- whether the issue happens every time

Feedback templates are generated under:

```text
project_storage/test_feedback/
```
