#!/usr/bin/env Rscript

args <- commandArgs(trailingOnly = TRUE)
if (length(args) < 3) {
  stop("usage: run_module.R <input_json> <output_dir> <mode>")
}

input_json <- normalizePath(args[[1]], mustWork = TRUE)
output_dir <- args[[2]]
mode <- args[[3]]

script_args <- commandArgs(trailingOnly = FALSE)
file_arg <- script_args[grepl("^--file=", script_args)]
script_path <- if (length(file_arg) > 0) {
  raw_file <- sub("^--file=", "", file_arg[[1]])
  normalizePath(gsub("~\\+~", " ", raw_file), mustWork = FALSE)
} else {
  normalizePath("analysis/runners/run_module.R", mustWork = FALSE)
}
repo_root <- normalizePath(file.path(dirname(script_path), "..", ".."), mustWork = FALSE)

required_dirs <- c("tables", "plots", "reports", "logs")
dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)
for (name in required_dirs) {
  dir.create(file.path(output_dir, name), recursive = TRUE, showWarnings = FALSE)
}

input_text <- paste(readLines(input_json, warn = FALSE), collapse = "\n")

json_string <- function(value) {
  if (is.null(value) || is.na(value)) {
    return("null")
  }
  escaped <- gsub("\\\\", "\\\\\\\\", as.character(value))
  escaped <- gsub('"', '\\"', escaped, fixed = TRUE)
  escaped <- gsub("\n", "\\\\n", escaped, fixed = TRUE)
  paste0('"', escaped, '"')
}

read_string_field <- function(text, field, default = "") {
  pattern <- paste0('"', field, '"[[:space:]]*:[[:space:]]*"[^"]+"')
  match <- regmatches(text, regexpr(pattern, text))
  if (length(match) == 1 && nchar(match) > 0) {
    return(sub('.*:[[:space:]]*"([^"]+)".*', "\\1", match))
  }
  default
}

read_integer_field <- function(text, field) {
  pattern <- paste0('"', field, '"[[:space:]]*:[[:space:]]*[0-9]+')
  match <- regmatches(text, regexpr(pattern, text))
  if (length(match) == 1 && nchar(match) > 0) {
    return(as.integer(sub(".*:[[:space:]]*([0-9]+).*", "\\1", match)))
  }
  NA_integer_
}

copy_fixture_package <- function(source, target) {
  if (!dir.exists(source)) {
    return(FALSE)
  }
  files <- list.files(source, recursive = TRUE, all.files = TRUE, no.. = TRUE, full.names = TRUE)
  for (source_file in files) {
    if (dir.exists(source_file)) {
      next
    }
    rel <- substring(source_file, nchar(source) + 2)
    target_file <- file.path(target, rel)
    dir.create(dirname(target_file), recursive = TRUE, showWarnings = FALSE)
    file.copy(source_file, target_file, overwrite = TRUE)
  }
  TRUE
}

write_result <- function(module_id, task_id, mode, status, blockers, warnings, message) {
  table_entries <- if (file.exists(file.path(output_dir, "tables", "mock_summary.tsv"))) {
    '    {"artifact_type": "mock_summary_table", "path": "tables/mock_summary.tsv"}'
  } else {
    ""
  }
  report_entries <- if (file.exists(file.path(output_dir, "reports", "README_mock.md"))) {
    '    {"artifact_type": "mock_limitations_report", "path": "reports/README_mock.md"}'
  } else {
    ""
  }
  blockers_json <- if (length(blockers) > 0) paste(vapply(blockers, json_string, character(1)), collapse = ", ") else ""
  warnings_json <- if (length(warnings) > 0) paste(vapply(warnings, json_string, character(1)), collapse = ", ") else ""
  result <- paste0(
    "{\n",
    '  "schema_version": "biomedpilot.analysis.result.v1",\n',
    '  "module_id": ', json_string(module_id), ",\n",
    '  "mode": ', json_string(mode), ",\n",
    '  "task_id": ', json_string(task_id), ",\n",
    '  "status": ', json_string(status), ",\n",
    '  "result_semantics": "testing_level",\n',
    '  "summary": {"message": ', json_string(message), ', "clinical_conclusion_status": "not_generated"},\n',
    '  "tables": [\n', table_entries, "\n  ],\n",
    '  "plots": [],\n',
    '  "reports": [\n', report_entries, "\n  ],\n",
    '  "blockers": [', blockers_json, "],\n",
    '  "warnings": [', warnings_json, "],\n",
    '  "created_at": ', json_string(timestamp), "\n",
    "}\n"
  )
  writeLines(result, file.path(output_dir, "result.json"))
}

write_provenance <- function(module_id, task_id, mode, command, r_version, bioc_version) {
  seed <- read_integer_field(input_text, "random_seed")
  seed_value <- if (is.na(seed)) "null" else as.character(seed)
  input_hash <- as.character(tools::md5sum(input_json))
  provenance <- paste0(
    "{\n",
    '  "schema_version": "biomedpilot.analysis.provenance.v1",\n',
    '  "module_id": ', json_string(module_id), ",\n",
    '  "mode": ', json_string(mode), ",\n",
    '  "task_id": ', json_string(task_id), ",\n",
    '  "created_at": ', json_string(timestamp), ",\n",
    '  "input_path": ', json_string(input_json), ",\n",
    '  "input_hash": ', json_string(input_hash), ",\n",
    '  "parameter_hash": ', json_string(input_hash), ",\n",
    '  "random_seed": ', seed_value, ",\n",
    '  "engine": {"name": "biomedpilot_standard_r_worker", "version": "v1"},\n',
    '  "runtime": {"r_version": ', json_string(r_version), ', "bioconductor_version": ', json_string(bioc_version), ', "package_versions": {}, "external_tool_versions": {}},\n',
    '  "command": ', json_string(command), "\n",
    "}\n"
  )
  writeLines(provenance, file.path(output_dir, "provenance.json"))
}

timestamp <- format(Sys.time(), "%Y-%m-%dT%H:%M:%SZ", tz = "UTC")
task_id <- read_string_field(input_text, "task_id", "unknown-task")
module_id <- read_string_field(input_text, "module_id", "unknown-module")
input_mode <- read_string_field(input_text, "mode", mode)
command <- paste(c("Rscript", "analysis/runners/run_module.R", input_json, output_dir, mode), collapse = " ")

if (input_mode != mode) {
  blocker <- paste0("module_input_mode_arg_mismatch:input=", input_mode, ",arg=", mode)
  write_result(
    module_id,
    task_id,
    mode,
    "blocked",
    c(blocker),
    c(),
    "Standard R worker blocked because CLI mode and input manifest mode differ."
  )
  write_provenance(module_id, task_id, mode, command, "not_executed", "not_executed")
  writeLines(paste(timestamp, "status=blocked", paste0("module_id=", module_id), blocker), file.path(output_dir, "logs", "worker.log"))
  quit(status = 2)
}

if (mode != "mock") {
  blocker <- paste0("standard_worker_mode_not_enabled:", mode)
  write_result(
    module_id,
    task_id,
    mode,
    "blocked",
    c(blocker),
    c(),
    "Standard R worker blocked before lite/full execution."
  )
  write_provenance(module_id, task_id, mode, command, "not_executed", "not_executed")
  writeLines(paste(timestamp, "status=blocked", paste0("module_id=", module_id), paste0("mode=", mode), blocker), file.path(output_dir, "logs", "worker.log"))
  quit(status = 2)
}

fixture_package <- file.path(repo_root, "analysis", "fixtures", "outputs", module_id, "mock_result_package")
fixture_found <- copy_fixture_package(fixture_package, output_dir)
if (!fixture_found) {
  write_result(
    module_id,
    task_id,
    mode,
    "blocked",
    c(paste0("mock_fixture_output_package_not_found:", module_id)),
    c("mock_fixture_unavailable"),
    "Standard R worker could not find the module mock fixture package."
  )
  write_provenance(module_id, task_id, mode, command, "not_executed", "not_executed")
  writeLines(paste(timestamp, "status=blocked", paste0("module_id=", module_id), "mock_fixture_missing"), file.path(output_dir, "logs", "worker.log"))
  quit(status = 2)
}

write_result(
  module_id,
  task_id,
  mode,
  "passed",
  c(),
  c("mock_result_not_scientific_output"),
  paste("Mock", module_id, "package generated for UI/API/task-flow development only.")
)
write_provenance(module_id, task_id, mode, command, R.version.string, "not_required_for_mock")
writeLines(paste(timestamp, "status=passed", paste0("module_id=", module_id), "mode=mock", paste0("task_id=", task_id), paste0("fixture_source=", fixture_package)), file.path(output_dir, "logs", "worker.log"))
