#!/usr/bin/env Rscript

args <- commandArgs(trailingOnly = TRUE)
if (length(args) < 3) {
  stop("usage: run_module.R <input_json> <output_dir> <mode>")
}

input_json <- normalizePath(args[[1]], mustWork = TRUE)
output_dir <- args[[2]]
mode <- args[[3]]

dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)
for (name in c("tables", "plots", "reports", "logs")) {
  dir.create(file.path(output_dir, name), recursive = TRUE, showWarnings = FALSE)
}

json_string <- function(value) {
  paste0('"', gsub('"', '\\"', value, fixed = TRUE), '"')
}

timestamp <- format(Sys.time(), "%Y-%m-%dT%H:%M:%SZ", tz = "UTC")
task_id <- "unknown-task"
module_id <- "unknown-module"
input_text <- paste(readLines(input_json, warn = FALSE), collapse = "\n")
task_match <- regmatches(input_text, regexpr('"task_id"[[:space:]]*:[[:space:]]*"[^"]+"', input_text))
module_match <- regmatches(input_text, regexpr('"module_id"[[:space:]]*:[[:space:]]*"[^"]+"', input_text))
if (length(task_match) == 1 && nchar(task_match) > 0) {
  task_id <- sub('.*:[[:space:]]*"([^"]+)".*', "\\1", task_match)
}
if (length(module_match) == 1 && nchar(module_match) > 0) {
  module_id <- sub('.*:[[:space:]]*"([^"]+)".*', "\\1", module_match)
}

if (mode != "mock") {
  result <- paste0(
    "{\n",
    '  "schema_version": "biomedpilot.analysis.result.v1",\n',
    '  "module_id": ', json_string(module_id), ",\n",
    '  "mode": ', json_string(mode), ",\n",
    '  "task_id": ', json_string(task_id), ",\n",
    '  "status": "blocked",\n',
    '  "blockers": ["standard_worker_mode_not_enabled:', mode, '"],\n',
    '  "warnings": []\n',
    "}\n"
  )
  writeLines(result, file.path(output_dir, "result.json"))
  writeLines("mode blocked by standard worker boundary", file.path(output_dir, "logs", "worker.log"))
  quit(status = 2)
}

result <- paste0(
  "{\n",
  '  "schema_version": "biomedpilot.analysis.result.v1",\n',
  '  "module_id": ', json_string(module_id), ",\n",
  '  "mode": "mock",\n',
  '  "task_id": ', json_string(task_id), ",\n",
  '  "status": "passed",\n',
  '  "summary": {"message": "Mock result package generated for UI/API/task-flow development only.", "clinical_conclusion_status": "not_generated"},\n',
  '  "tables": [],\n',
  '  "plots": [],\n',
  '  "reports": [],\n',
  '  "blockers": [],\n',
  '  "warnings": ["mock_result_not_scientific_output"]\n',
  "}\n"
)

provenance <- paste0(
  "{\n",
  '  "schema_version": "biomedpilot.analysis.provenance.v1",\n',
  '  "module_id": ', json_string(module_id), ",\n",
  '  "mode": "mock",\n',
  '  "task_id": ', json_string(task_id), ",\n",
  '  "created_at": ', json_string(timestamp), ",\n",
  '  "input_path": ', json_string(input_json), ",\n",
  '  "input_hash": "not_computed_by_base_mock_runner",\n',
  '  "parameter_hash": "not_computed_by_base_mock_runner",\n',
  '  "random_seed": null,\n',
  '  "engine": {"name": "biomedpilot_mock_r_worker", "version": "v1"},\n',
  '  "runtime": {"r_version": ', json_string(R.version.string), ', "bioconductor_version": "not_required_for_mock", "package_versions": {}, "external_tool_versions": {}},\n',
  '  "command": ', json_string(paste(c("Rscript", "analysis/runners/run_module.R", input_json, output_dir, mode), collapse = " ")), "\n",
  "}\n"
)

writeLines(result, file.path(output_dir, "result.json"))
writeLines(provenance, file.path(output_dir, "provenance.json"))
writeLines("mock mode completed", file.path(output_dir, "logs", "worker.log"))
