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
5. Return to the Dashboard and click each recent project.
6. Open `测试模式`.
7. Generate a feedback template.
8. Record anything confusing, broken, missing, or mislabeled.

## 5. Features To Test Now

- Dashboard layout and wording.
- Project creation for both project types.
- Recent project list.
- Workspace switching.
- Feature status labels: `已开放`, `测试中`, `待接入`, `暂未开放`.
- Testing Mode page and feedback template generation.

## 6. Features Not Ready For Testing

Do not treat the following as completed workflows yet:

- formal bioinformatics differential expression analysis
- enrichment analysis
- correlation analysis
- survival analysis
- complete Meta statistical analysis
- final report export workflows
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

