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

- formal bioinformatics differential expression analysis
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
