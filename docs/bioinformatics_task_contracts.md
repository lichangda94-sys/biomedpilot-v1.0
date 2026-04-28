# Bioinformatics Task Contracts

Task Center records use the shared `TaskRecord` shape:

```json
{
  "task_id": "task-...",
  "task_type": "import|download|preprocess|analysis|visualization|report_export",
  "status": "pending|running|completed|failed|cancelled",
  "module": "bioinformatics",
  "title": "...",
  "created_at": "...",
  "updated_at": "...",
  "project_id": "...",
  "started_at": "...",
  "finished_at": "...",
  "summary": "...",
  "error_message": ""
}
```

Each current Bioinformatics service starts a task, writes a JSON/Markdown artifact when successful, registers a Data Center asset when applicable, and saves the task as `completed` or `failed` with a user-readable message.

## Current Task Types By Step

| Step | Service title | TaskType | Current completion semantics |
| --- | --- | --- | --- |
| 数据检索 / 导入 | `GEO Query Import` | `IMPORT` | Query/accession plan JSON was written; no online search |
| Local Expression Matrix Import | `Local Expression Matrix Import` | `IMPORT` | Local file preflight JSON was written; no normalization |
| 数据下载 | `GEO Download Plan` | `DOWNLOAD` | Download plan JSON was written; no download execution |
| 数据资产识别 | `GEO Asset Detection` | `PREPROCESS` | Local asset detection JSON was written |
| 数据清洗 | `GEO Cleaning Plan` | `PREPROCESS` | Cleaning plan JSON was written; no cleaning execution |
| 样本分组 | `Sample Grouping Plan` | `PREPROCESS` | Grouping plan JSON was written; no final grouping execution |
| 差异表达分析 | `Differential Expression Preflight` | `ANALYSIS` | DEG readiness JSON was written; no statistics |
| 富集分析 | `Enrichment Preflight` | `ANALYSIS` | Enrichment readiness JSON was written; no enrichment run |
| 相关性分析 | `Correlation Preflight` | `ANALYSIS` | Correlation readiness JSON was written; no correlation run |
| 生存分析 | `Survival Preflight` | `ANALYSIS` | Survival readiness JSON was written; no survival run |
| 报告导出 | `Bioinformatics Test Report Export` | `REPORT_EXPORT` | Markdown testing summary was written |

## Failure Contract

Current services return failure results instead of exposing tracebacks in the main UI. Failure tasks are saved with:

- `status`: `failed`
- `summary`: user-readable message
- `error_message`: same user-readable message
- optional detailed error stored in service result `details`, not shown as a traceback by default

## Planned Task Usage

Future stages should continue to reuse existing shared `TaskType` values:

- Import and local asset entry: `IMPORT`
- Controlled download: `DOWNLOAD`
- Cleaning, normalization, grouping, and parsing: `PREPROCESS`
- DEG, enrichment, correlation, and survival runners: `ANALYSIS`
- Figure generation: `VISUALIZATION`
- Reports and reproducibility package export: `REPORT_EXPORT`

Do not add a new TaskType unless an existing value cannot describe the task without ambiguity.
