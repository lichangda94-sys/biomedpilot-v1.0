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

hash_string <- function(value) {
  path <- tempfile("biomedpilot_hash_")
  writeLines(value, path, useBytes = TRUE)
  digest <- as.character(tools::md5sum(path))
  unlink(path)
  digest
}

read_object_field_text <- function(text, field, default = "{}") {
  field_pattern <- paste0('"', field, '"[[:space:]]*:')
  field_match <- regexpr(field_pattern, text)
  if (field_match[[1]] < 0) {
    return(default)
  }
  search_start <- field_match[[1]] + attr(field_match, "match.length")
  tail_text <- substring(text, search_start)
  open_offset <- regexpr("\\{", tail_text)
  if (open_offset[[1]] < 0) {
    return(default)
  }
  object_start <- search_start + open_offset[[1]] - 1
  chars <- strsplit(substring(text, object_start), "", fixed = TRUE)[[1]]
  depth <- 0
  in_string <- FALSE
  escaped <- FALSE
  for (index in seq_along(chars)) {
    char <- chars[[index]]
    if (escaped) {
      escaped <- FALSE
      next
    }
    if (char == "\\") {
      escaped <- TRUE
      next
    }
    if (char == '"') {
      in_string <- !in_string
      next
    }
    if (!in_string && char == "{") {
      depth <- depth + 1
    }
    if (!in_string && char == "}") {
      depth <- depth - 1
      if (depth == 0) {
        return(substring(text, object_start, object_start + index - 1))
      }
    }
  }
  default
}

resolve_input_path <- function(value) {
  if (value == "") {
    return("")
  }
  path <- path.expand(value)
  if (grepl("^/", path)) {
    return(normalizePath(path, mustWork = FALSE))
  }
  normalizePath(file.path(repo_root, path), mustWork = FALSE)
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

table_artifact_type <- function(module_id, mode, table_file) {
  if (table_file == "mock_summary.tsv") {
    return("mock_summary_table")
  }
  if (module_id == "enrichment" && mode == "lite" && table_file == "lite_ora_result.tsv") {
    return("lite_enrichment_ora_result_table")
  }
  if (module_id == "deg" && mode == "lite" && table_file == "lite_deg_result.tsv") {
    return("lite_deg_result_table")
  }
  if (module_id == "survival" && mode == "lite" && table_file == "lite_km_curve.tsv") {
    return("lite_survival_km_curve_table")
  }
  if (module_id == "survival" && mode == "lite" && table_file == "lite_logrank_result.tsv") {
    return("lite_survival_logrank_result_table")
  }
  if (module_id == "univariate" && mode == "lite" && table_file == "lite_univariate_association.tsv") {
    return("lite_univariate_clinical_association_table")
  }
  if (module_id == "multivariate" && mode == "lite" && table_file == "lite_multivariate_association.tsv") {
    return("lite_multivariate_clinical_association_table")
  }
  if (module_id == "immune_infiltration" && mode == "lite" && table_file == "lite_immune_scores.tsv") {
    return("lite_immune_infiltration_score_table")
  }
  if (module_id == "docking" && mode == "lite" && table_file == "lite_docking_command_manifest.tsv") {
    return("lite_docking_external_tool_command_manifest")
  }
  if (module_id == "molecular_dynamics" && mode == "lite" && table_file == "lite_md_command_manifest.tsv") {
    return("lite_molecular_dynamics_external_tool_command_manifest")
  }
  "analysis_table"
}

plot_artifact_type <- function(module_id, mode, plot_file) {
  if (module_id == "immune_infiltration" && mode == "lite" && plot_file == "lite_immune_heatmap.svg") {
    return("lite_immune_infiltration_heatmap_svg")
  }
  "analysis_plot"
}

write_result <- function(module_id, task_id, mode, status, blockers, warnings, message) {
  table_files <- list.files(file.path(output_dir, "tables"), full.names = FALSE)
  plot_files <- list.files(file.path(output_dir, "plots"), full.names = FALSE)
  report_files <- list.files(file.path(output_dir, "reports"), full.names = FALSE)
  table_entries_vector <- character(0)
  for (table_file in table_files) {
    artifact_type <- table_artifact_type(module_id, mode, table_file)
    table_entries_vector <- c(table_entries_vector, paste0('    {"artifact_type": ', json_string(artifact_type), ', "path": ', json_string(file.path("tables", table_file)), '}'))
  }
  plot_entries_vector <- character(0)
  for (plot_file in plot_files) {
    if (!grepl("\\.(svg|png|pdf)$", plot_file, ignore.case = TRUE)) {
      next
    }
    artifact_type <- plot_artifact_type(module_id, mode, plot_file)
    plot_entries_vector <- c(plot_entries_vector, paste0('    {"artifact_type": ', json_string(artifact_type), ', "path": ', json_string(file.path("plots", plot_file)), '}'))
  }
  report_entries_vector <- character(0)
  for (report_file in report_files) {
    artifact_type <- if (report_file == "README_mock.md") "mock_limitations_report" else "lite_analysis_limitations_report"
    report_entries_vector <- c(report_entries_vector, paste0('    {"artifact_type": ', json_string(artifact_type), ', "path": ', json_string(file.path("reports", report_file)), '}'))
  }
  table_entries <- paste(table_entries_vector, collapse = ",\n")
  plot_entries <- paste(plot_entries_vector, collapse = ",\n")
  report_entries <- paste(report_entries_vector, collapse = ",\n")
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
    '  "plots": [\n', plot_entries, "\n  ],\n",
    '  "reports": [\n', report_entries, "\n  ],\n",
    '  "blockers": [', blockers_json, "],\n",
    '  "warnings": [', warnings_json, "],\n",
    '  "created_at": ', json_string(timestamp), "\n",
    "}\n"
  )
  writeLines(result, file.path(output_dir, "result.json"))
}

run_lite_enrichment_ora <- function() {
  gene_list_path <- resolve_input_path(read_string_field(input_text, "gene_list_path", ""))
  term2gene_path <- resolve_input_path(read_string_field(input_text, "term2gene_path", ""))
  term2name_path <- resolve_input_path(read_string_field(input_text, "term2name_path", ""))
  blockers <- character(0)
  if (gene_list_path == "" || !file.exists(gene_list_path)) {
    blockers <- c(blockers, "lite_enrichment_gene_list_missing")
  }
  if (term2gene_path == "" || !file.exists(term2gene_path)) {
    blockers <- c(blockers, "lite_enrichment_term2gene_missing")
  }
  if (length(blockers) > 0) {
    write_result(module_id, task_id, mode, "blocked", blockers, c(), "Lite enrichment ORA blocked because required fixture inputs are missing.")
    write_provenance(module_id, task_id, mode, command, "not_executed", "not_executed")
    writeLines(paste(timestamp, "status=blocked", paste0("module_id=", module_id), paste(blockers, collapse = ";")), file.path(output_dir, "logs", "worker.log"))
    quit(status = 2)
  }
  genes <- unique(trimws(readLines(gene_list_path, warn = FALSE)))
  genes <- genes[nchar(genes) > 0]
  term2gene <- read.delim(term2gene_path, stringsAsFactors = FALSE)
  if (!all(c("term", "gene") %in% colnames(term2gene))) {
    write_result(module_id, task_id, mode, "blocked", c("lite_enrichment_term2gene_schema_invalid"), c(), "Lite enrichment ORA blocked because TERM2GENE columns are invalid.")
    write_provenance(module_id, task_id, mode, command, "not_executed", "not_executed")
    writeLines(paste(timestamp, "status=blocked", paste0("module_id=", module_id), "term2gene_schema_invalid"), file.path(output_dir, "logs", "worker.log"))
    quit(status = 2)
  }
  term_names <- data.frame(term = character(0), name = character(0), stringsAsFactors = FALSE)
  if (term2name_path != "" && file.exists(term2name_path)) {
    term_names <- read.delim(term2name_path, stringsAsFactors = FALSE)
  }
  universe <- unique(term2gene$gene)
  genes_in_universe <- intersect(genes, universe)
  n <- length(genes_in_universe)
  N <- length(universe)
  rows <- list()
  for (term in unique(term2gene$term)) {
    term_genes <- unique(term2gene$gene[term2gene$term == term])
    overlap <- intersect(genes_in_universe, term_genes)
    k <- length(overlap)
    if (k < 1 || n < 1 || N < 1) {
      next
    }
    M <- length(intersect(term_genes, universe))
    pvalue <- phyper(k - 1, M, N - M, n, lower.tail = FALSE)
    description <- term
    if (nrow(term_names) > 0 && all(c("term", "name") %in% colnames(term_names)) && term %in% term_names$term) {
      description <- term_names$name[match(term, term_names$term)]
    }
    rows[[length(rows) + 1]] <- data.frame(
      ID = term,
      Description = description,
      GeneRatio = paste0(k, "/", n),
      BgRatio = paste0(M, "/", N),
      pvalue = pvalue,
      geneID = paste(overlap, collapse = "/"),
      Count = k,
      stringsAsFactors = FALSE
    )
  }
  if (length(rows) == 0) {
    result_table <- data.frame(ID = character(0), Description = character(0), GeneRatio = character(0), BgRatio = character(0), pvalue = numeric(0), p.adjust = numeric(0), qvalue = numeric(0), geneID = character(0), Count = integer(0))
  } else {
    result_table <- do.call(rbind, rows)
    result_table$p.adjust <- p.adjust(result_table$pvalue, method = "BH")
    result_table$qvalue <- result_table$p.adjust
    result_table <- result_table[, c("ID", "Description", "GeneRatio", "BgRatio", "pvalue", "p.adjust", "qvalue", "geneID", "Count")]
  }
  result_path <- file.path(output_dir, "tables", "lite_ora_result.tsv")
  write.table(result_table, file = result_path, sep = "\t", quote = FALSE, row.names = FALSE)
  writeLines(c(
    "# Lite enrichment limitations",
    "",
    "This is a lightweight fixture ORA result for worker and package-contract validation.",
    "It is not a formal enrichment result and is not report-ready."
  ), file.path(output_dir, "reports", "README_lite.md"))
  write_result(
    module_id,
    task_id,
    mode,
    "passed",
    c(),
    c("lite_result_not_formal_analysis", "base_r_fixture_only_no_heavy_resources"),
    "Lite enrichment ORA completed with base R fixture resources."
  )
  write_provenance(module_id, task_id, mode, command, R.version.string, "not_required_for_lite_base_r")
  writeLines(paste(timestamp, "status=passed", paste0("module_id=", module_id), "mode=lite", paste0("task_id=", task_id), paste0("result_table=", result_path)), file.path(output_dir, "logs", "worker.log"))
  quit(status = 0)
}

run_lite_deg_two_group <- function() {
  expression_matrix_path <- resolve_input_path(read_string_field(input_text, "expression_matrix_path", ""))
  sample_metadata_path <- resolve_input_path(read_string_field(input_text, "sample_metadata_path", ""))
  case_group <- read_string_field(input_text, "case_group", "case")
  control_group <- read_string_field(input_text, "control_group", "control")
  blockers <- character(0)
  if (expression_matrix_path == "" || !file.exists(expression_matrix_path)) {
    blockers <- c(blockers, "lite_deg_expression_matrix_missing")
  }
  if (sample_metadata_path == "" || !file.exists(sample_metadata_path)) {
    blockers <- c(blockers, "lite_deg_sample_metadata_missing")
  }
  if (length(blockers) > 0) {
    write_result(module_id, task_id, mode, "blocked", blockers, c(), "Lite DEG blocked because required fixture inputs are missing.")
    write_provenance(module_id, task_id, mode, command, "not_executed", "not_executed")
    writeLines(paste(timestamp, "status=blocked", paste0("module_id=", module_id), paste(blockers, collapse = ";")), file.path(output_dir, "logs", "worker.log"))
    quit(status = 2)
  }
  expression <- read.delim(expression_matrix_path, stringsAsFactors = FALSE, check.names = FALSE)
  metadata <- read.delim(sample_metadata_path, stringsAsFactors = FALSE, check.names = FALSE)
  if (!("gene" %in% colnames(expression)) || ncol(expression) < 3) {
    write_result(module_id, task_id, mode, "blocked", c("lite_deg_expression_matrix_schema_invalid"), c(), "Lite DEG blocked because expression matrix columns are invalid.")
    write_provenance(module_id, task_id, mode, command, "not_executed", "not_executed")
    writeLines(paste(timestamp, "status=blocked", paste0("module_id=", module_id), "deg_expression_schema_invalid"), file.path(output_dir, "logs", "worker.log"))
    quit(status = 2)
  }
  if (!all(c("sample_id", "group") %in% colnames(metadata))) {
    write_result(module_id, task_id, mode, "blocked", c("lite_deg_sample_metadata_schema_invalid"), c(), "Lite DEG blocked because sample metadata columns are invalid.")
    write_provenance(module_id, task_id, mode, command, "not_executed", "not_executed")
    writeLines(paste(timestamp, "status=blocked", paste0("module_id=", module_id), "deg_metadata_schema_invalid"), file.path(output_dir, "logs", "worker.log"))
    quit(status = 2)
  }
  sample_ids <- setdiff(colnames(expression), "gene")
  metadata$sample_id <- as.character(metadata$sample_id)
  metadata$group <- as.character(metadata$group)
  if (!all(sample_ids %in% metadata$sample_id)) {
    write_result(module_id, task_id, mode, "blocked", c("lite_deg_sample_metadata_mismatch"), c(), "Lite DEG blocked because expression samples do not align with metadata.")
    write_provenance(module_id, task_id, mode, command, "not_executed", "not_executed")
    writeLines(paste(timestamp, "status=blocked", paste0("module_id=", module_id), "deg_sample_mismatch"), file.path(output_dir, "logs", "worker.log"))
    quit(status = 2)
  }
  expression_values <- as.data.frame(lapply(expression[, sample_ids, drop = FALSE], as.numeric), check.names = FALSE)
  if (any(is.na(as.matrix(expression_values)))) {
    write_result(module_id, task_id, mode, "blocked", c("lite_deg_expression_matrix_non_numeric"), c(), "Lite DEG blocked because expression values are not numeric.")
    write_provenance(module_id, task_id, mode, command, "not_executed", "not_executed")
    writeLines(paste(timestamp, "status=blocked", paste0("module_id=", module_id), "deg_non_numeric"), file.path(output_dir, "logs", "worker.log"))
    quit(status = 2)
  }
  if (any(as.matrix(expression_values) < 0)) {
    write_result(module_id, task_id, mode, "blocked", c("lite_deg_negative_counts"), c(), "Lite DEG blocked because count values cannot be negative.")
    write_provenance(module_id, task_id, mode, command, "not_executed", "not_executed")
    writeLines(paste(timestamp, "status=blocked", paste0("module_id=", module_id), "deg_negative_counts"), file.path(output_dir, "logs", "worker.log"))
    quit(status = 2)
  }
  case_samples <- metadata$sample_id[metadata$group == case_group]
  control_samples <- metadata$sample_id[metadata$group == control_group]
  case_samples <- intersect(case_samples, sample_ids)
  control_samples <- intersect(control_samples, sample_ids)
  if (length(case_samples) < 2 || length(control_samples) < 2) {
    write_result(module_id, task_id, mode, "blocked", c("lite_deg_requires_two_groups_with_minimum_two_samples"), c(), "Lite DEG blocked because two groups with at least two samples each are required.")
    write_provenance(module_id, task_id, mode, command, "not_executed", "not_executed")
    writeLines(paste(timestamp, "status=blocked", paste0("module_id=", module_id), "deg_group_size_invalid"), file.path(output_dir, "logs", "worker.log"))
    quit(status = 2)
  }
  matrix_values <- as.matrix(expression_values)
  rownames(matrix_values) <- as.character(expression$gene)
  log_matrix <- log2(matrix_values + 1)
  rows <- list()
  for (gene in rownames(log_matrix)) {
    case_values <- as.numeric(log_matrix[gene, case_samples])
    control_values <- as.numeric(log_matrix[gene, control_samples])
    test <- try(t.test(case_values, control_values), silent = TRUE)
    p_value <- if (inherits(test, "try-error")) NA_real_ else test$p.value
    log2_fc <- mean(case_values) - mean(control_values)
    rows[[length(rows) + 1]] <- data.frame(
      feature_id = gene,
      gene_symbol = gene,
      log2_fold_change = log2_fc,
      p_value = p_value,
      method = "base_r_welch_t_test_fixture",
      clinical_conclusion = "not_generated",
      stringsAsFactors = FALSE
    )
  }
  result_table <- do.call(rbind, rows)
  result_table$adjusted_p_value <- p.adjust(result_table$p_value, method = "BH")
  result_table$significance_label <- ifelse(
    !is.na(result_table$adjusted_p_value) & result_table$adjusted_p_value <= 0.05 & result_table$log2_fold_change >= 1,
    "up",
    ifelse(!is.na(result_table$adjusted_p_value) & result_table$adjusted_p_value <= 0.05 & result_table$log2_fold_change <= -1, "down", "not_significant")
  )
  result_table <- result_table[, c("feature_id", "gene_symbol", "log2_fold_change", "p_value", "adjusted_p_value", "significance_label", "method", "clinical_conclusion")]
  write.table(result_table, file = file.path(output_dir, "tables", "lite_deg_result.tsv"), sep = "\t", quote = FALSE, row.names = FALSE)
  writeLines(c(
    "# Lite DEG limitations",
    "",
    "This is a lightweight fixture DEG result for worker and package-contract validation.",
    "It uses base R Welch t-tests on fixed local count fixtures.",
    "It is not a formal DEG result, clinical result, report-ready output, or replacement for limma/DESeq2/edgeR."
  ), file.path(output_dir, "reports", "README_lite.md"))
  write_result(
    module_id,
    task_id,
    mode,
    "passed",
    c(),
    c("lite_result_not_formal_analysis", "base_r_fixture_only_no_heavy_resources", "clinical_conclusion_not_generated"),
    "Lite DEG completed with base R fixture data."
  )
  write_provenance(module_id, task_id, mode, command, R.version.string, "not_required_for_lite_base_r")
  writeLines(paste(timestamp, "status=passed", paste0("module_id=", module_id), "mode=lite", paste0("task_id=", task_id), "clinical_conclusion=not_generated"), file.path(output_dir, "logs", "worker.log"))
  quit(status = 0)
}

km_curve_for_group <- function(data, group_name) {
  group_data <- data[data$group == group_name, , drop = FALSE]
  event_times <- sort(unique(group_data$time[group_data$event == 1]))
  survival <- 1
  rows <- list(data.frame(group = group_name, time = 0, n_risk = nrow(group_data), n_event = 0, survival = survival))
  for (time in event_times) {
    n_risk <- sum(group_data$time >= time)
    n_event <- sum(group_data$time == time & group_data$event == 1)
    if (n_risk > 0) {
      survival <- survival * (1 - n_event / n_risk)
    }
    rows[[length(rows) + 1]] <- data.frame(group = group_name, time = time, n_risk = n_risk, n_event = n_event, survival = survival)
  }
  do.call(rbind, rows)
}

logrank_two_group <- function(data, group_a, group_b) {
  event_times <- sort(unique(data$time[data$event == 1]))
  observed_a <- 0
  expected_a <- 0
  variance_a <- 0
  for (time in event_times) {
    at_risk_a <- sum(data$group == group_a & data$time >= time)
    at_risk_b <- sum(data$group == group_b & data$time >= time)
    events_a <- sum(data$group == group_a & data$time == time & data$event == 1)
    events_b <- sum(data$group == group_b & data$time == time & data$event == 1)
    at_risk_total <- at_risk_a + at_risk_b
    events_total <- events_a + events_b
    if (at_risk_total <= 0 || events_total <= 0) {
      next
    }
    observed_a <- observed_a + events_a
    expected_a <- expected_a + events_total * at_risk_a / at_risk_total
    if (at_risk_total > 1) {
      variance_a <- variance_a + (at_risk_a * at_risk_b * events_total * (at_risk_total - events_total)) / (at_risk_total^2 * (at_risk_total - 1))
    }
  }
  statistic <- if (variance_a > 0) ((observed_a - expected_a)^2 / variance_a) else NA_real_
  pvalue <- if (!is.na(statistic)) pchisq(statistic, df = 1, lower.tail = FALSE) else NA_real_
  data.frame(
    group_a = group_a,
    group_b = group_b,
    observed_events_group_a = observed_a,
    expected_events_group_a = expected_a,
    chi_square = statistic,
    p_value = pvalue,
    method = "base_r_logrank_fixture",
    stringsAsFactors = FALSE
  )
}

run_lite_survival_km_logrank <- function() {
  survival_table_path <- resolve_input_path(read_string_field(input_text, "survival_table_path", ""))
  blockers <- character(0)
  if (survival_table_path == "" || !file.exists(survival_table_path)) {
    blockers <- c(blockers, "lite_survival_table_missing")
  }
  if (length(blockers) > 0) {
    write_result(module_id, task_id, mode, "blocked", blockers, c(), "Lite survival analysis blocked because required fixture input is missing.")
    write_provenance(module_id, task_id, mode, command, "not_executed", "not_executed")
    writeLines(paste(timestamp, "status=blocked", paste0("module_id=", module_id), paste(blockers, collapse = ";")), file.path(output_dir, "logs", "worker.log"))
    quit(status = 2)
  }
  survival_data <- read.delim(survival_table_path, stringsAsFactors = FALSE)
  required_columns <- c("sample_id", "time", "event", "group")
  if (!all(required_columns %in% colnames(survival_data))) {
    write_result(module_id, task_id, mode, "blocked", c("lite_survival_table_schema_invalid"), c(), "Lite survival analysis blocked because survival table columns are invalid.")
    write_provenance(module_id, task_id, mode, command, "not_executed", "not_executed")
    writeLines(paste(timestamp, "status=blocked", paste0("module_id=", module_id), "survival_schema_invalid"), file.path(output_dir, "logs", "worker.log"))
    quit(status = 2)
  }
  survival_data$time <- as.numeric(survival_data$time)
  survival_data$event <- as.integer(survival_data$event)
  survival_data$group <- as.character(survival_data$group)
  if (any(is.na(survival_data$time)) || any(is.na(survival_data$event))) {
    write_result(module_id, task_id, mode, "blocked", c("lite_survival_table_non_numeric_time_or_event"), c(), "Lite survival analysis blocked because time/event values are invalid.")
    write_provenance(module_id, task_id, mode, command, "not_executed", "not_executed")
    writeLines(paste(timestamp, "status=blocked", paste0("module_id=", module_id), "survival_non_numeric"), file.path(output_dir, "logs", "worker.log"))
    quit(status = 2)
  }
  groups <- sort(unique(survival_data$group))
  if (length(groups) != 2) {
    write_result(module_id, task_id, mode, "blocked", c("lite_survival_requires_two_groups"), c(), "Lite survival analysis blocked because exactly two groups are required.")
    write_provenance(module_id, task_id, mode, command, "not_executed", "not_executed")
    writeLines(paste(timestamp, "status=blocked", paste0("module_id=", module_id), "survival_group_count_invalid"), file.path(output_dir, "logs", "worker.log"))
    quit(status = 2)
  }
  km_table <- do.call(rbind, lapply(groups, function(group_name) km_curve_for_group(survival_data, group_name)))
  logrank_table <- logrank_two_group(survival_data, groups[[1]], groups[[2]])
  write.table(km_table, file = file.path(output_dir, "tables", "lite_km_curve.tsv"), sep = "\t", quote = FALSE, row.names = FALSE)
  write.table(logrank_table, file = file.path(output_dir, "tables", "lite_logrank_result.tsv"), sep = "\t", quote = FALSE, row.names = FALSE)
  writeLines(c(
    "# Lite survival limitations",
    "",
    "This is a lightweight fixture KM/log-rank result for worker and package-contract validation.",
    "It is not a clinical prognosis, treatment recommendation, or report-ready survival analysis."
  ), file.path(output_dir, "reports", "README_lite.md"))
  write_result(
    module_id,
    task_id,
    mode,
    "passed",
    c(),
    c("lite_result_not_formal_analysis", "clinical_conclusion_not_generated", "base_r_fixture_only_no_heavy_resources"),
    "Lite survival KM/log-rank completed with base R fixture data."
  )
  write_provenance(module_id, task_id, mode, command, R.version.string, "not_required_for_lite_base_r")
  writeLines(paste(timestamp, "status=passed", paste0("module_id=", module_id), "mode=lite", paste0("task_id=", task_id), "clinical_conclusion=not_generated"), file.path(output_dir, "logs", "worker.log"))
  quit(status = 0)
}

run_lite_univariate_association <- function() {
  clinical_table_path <- resolve_input_path(read_string_field(input_text, "clinical_table_path", ""))
  blockers <- character(0)
  if (clinical_table_path == "" || !file.exists(clinical_table_path)) {
    blockers <- c(blockers, "lite_univariate_clinical_table_missing")
  }
  if (length(blockers) > 0) {
    write_result(module_id, task_id, mode, "blocked", blockers, c(), "Lite univariate association blocked because required fixture input is missing.")
    write_provenance(module_id, task_id, mode, command, "not_executed", "not_executed")
    writeLines(paste(timestamp, "status=blocked", paste0("module_id=", module_id), paste(blockers, collapse = ";")), file.path(output_dir, "logs", "worker.log"))
    quit(status = 2)
  }
  clinical <- read.delim(clinical_table_path, stringsAsFactors = FALSE)
  required_columns <- c("sample_id", "group", "biomarker", "age")
  if (!all(required_columns %in% colnames(clinical))) {
    write_result(module_id, task_id, mode, "blocked", c("lite_univariate_clinical_table_schema_invalid"), c(), "Lite univariate association blocked because clinical table columns are invalid.")
    write_provenance(module_id, task_id, mode, command, "not_executed", "not_executed")
    writeLines(paste(timestamp, "status=blocked", paste0("module_id=", module_id), "univariate_schema_invalid"), file.path(output_dir, "logs", "worker.log"))
    quit(status = 2)
  }
  clinical$biomarker <- as.numeric(clinical$biomarker)
  clinical$age <- as.numeric(clinical$age)
  clinical$group <- as.character(clinical$group)
  if (any(is.na(clinical$biomarker)) || any(is.na(clinical$age))) {
    write_result(module_id, task_id, mode, "blocked", c("lite_univariate_non_numeric_values"), c(), "Lite univariate association blocked because numeric fixture columns are invalid.")
    write_provenance(module_id, task_id, mode, command, "not_executed", "not_executed")
    writeLines(paste(timestamp, "status=blocked", paste0("module_id=", module_id), "univariate_non_numeric"), file.path(output_dir, "logs", "worker.log"))
    quit(status = 2)
  }
  groups <- sort(unique(clinical$group))
  if (length(groups) != 2) {
    write_result(module_id, task_id, mode, "blocked", c("lite_univariate_requires_two_groups"), c(), "Lite univariate association blocked because exactly two groups are required.")
    write_provenance(module_id, task_id, mode, command, "not_executed", "not_executed")
    writeLines(paste(timestamp, "status=blocked", paste0("module_id=", module_id), "univariate_group_count_invalid"), file.path(output_dir, "logs", "worker.log"))
    quit(status = 2)
  }
  group_test <- t.test(biomarker ~ group, data = clinical)
  cor_test <- cor.test(clinical$biomarker, clinical$age, method = "pearson")
  rows <- data.frame(
    variable = c("group", "age"),
    outcome = c("biomarker", "biomarker"),
    test = c("welch_t_test", "pearson_correlation"),
    estimate = c(
      unname(diff(rev(group_test$estimate))),
      unname(cor_test$estimate)
    ),
    statistic = c(
      unname(group_test$statistic),
      unname(cor_test$statistic)
    ),
    p_value = c(group_test$p.value, cor_test$p.value),
    method = c("base_r_t_test_fixture", "base_r_cor_test_fixture"),
    clinical_conclusion = c("not_generated", "not_generated"),
    stringsAsFactors = FALSE
  )
  write.table(rows, file = file.path(output_dir, "tables", "lite_univariate_association.tsv"), sep = "\t", quote = FALSE, row.names = FALSE)
  writeLines(c(
    "# Lite univariate limitations",
    "",
    "This is a lightweight fixture univariate association result for worker and package-contract validation.",
    "It is not a clinical conclusion, diagnosis, prognosis, treatment recommendation, or report-ready clinical analysis."
  ), file.path(output_dir, "reports", "README_lite.md"))
  write_result(
    module_id,
    task_id,
    mode,
    "passed",
    c(),
    c("lite_result_not_formal_analysis", "clinical_conclusion_not_generated", "base_r_fixture_only_no_heavy_resources"),
    "Lite univariate clinical association completed with base R fixture data."
  )
  write_provenance(module_id, task_id, mode, command, R.version.string, "not_required_for_lite_base_r")
  writeLines(paste(timestamp, "status=passed", paste0("module_id=", module_id), "mode=lite", paste0("task_id=", task_id), "clinical_conclusion=not_generated"), file.path(output_dir, "logs", "worker.log"))
  quit(status = 0)
}

run_lite_multivariate_association <- function() {
  clinical_table_path <- resolve_input_path(read_string_field(input_text, "clinical_table_path", ""))
  blockers <- character(0)
  if (clinical_table_path == "" || !file.exists(clinical_table_path)) {
    blockers <- c(blockers, "lite_multivariate_clinical_table_missing")
  }
  if (length(blockers) > 0) {
    write_result(module_id, task_id, mode, "blocked", blockers, c(), "Lite multivariate association blocked because required fixture input is missing.")
    write_provenance(module_id, task_id, mode, command, "not_executed", "not_executed")
    writeLines(paste(timestamp, "status=blocked", paste0("module_id=", module_id), paste(blockers, collapse = ";")), file.path(output_dir, "logs", "worker.log"))
    quit(status = 2)
  }
  clinical <- read.delim(clinical_table_path, stringsAsFactors = FALSE)
  required_columns <- c("sample_id", "group", "biomarker", "age", "batch")
  if (!all(required_columns %in% colnames(clinical))) {
    write_result(module_id, task_id, mode, "blocked", c("lite_multivariate_clinical_table_schema_invalid"), c(), "Lite multivariate association blocked because clinical table columns are invalid.")
    write_provenance(module_id, task_id, mode, command, "not_executed", "not_executed")
    writeLines(paste(timestamp, "status=blocked", paste0("module_id=", module_id), "multivariate_schema_invalid"), file.path(output_dir, "logs", "worker.log"))
    quit(status = 2)
  }
  clinical$biomarker <- as.numeric(clinical$biomarker)
  clinical$age <- as.numeric(clinical$age)
  clinical$group <- factor(clinical$group)
  clinical$batch <- factor(clinical$batch)
  if (any(is.na(clinical$biomarker)) || any(is.na(clinical$age))) {
    write_result(module_id, task_id, mode, "blocked", c("lite_multivariate_non_numeric_values"), c(), "Lite multivariate association blocked because numeric fixture columns are invalid.")
    write_provenance(module_id, task_id, mode, command, "not_executed", "not_executed")
    writeLines(paste(timestamp, "status=blocked", paste0("module_id=", module_id), "multivariate_non_numeric"), file.path(output_dir, "logs", "worker.log"))
    quit(status = 2)
  }
  if (length(unique(clinical$group)) < 2 || length(unique(clinical$batch)) < 2) {
    write_result(module_id, task_id, mode, "blocked", c("lite_multivariate_requires_group_and_batch_variation"), c(), "Lite multivariate association blocked because group and batch variation are required.")
    write_provenance(module_id, task_id, mode, command, "not_executed", "not_executed")
    writeLines(paste(timestamp, "status=blocked", paste0("module_id=", module_id), "multivariate_variation_invalid"), file.path(output_dir, "logs", "worker.log"))
    quit(status = 2)
  }
  fit <- lm(biomarker ~ group + age + batch, data = clinical)
  coefficients <- as.data.frame(summary(fit)$coefficients)
  coefficients$term <- rownames(coefficients)
  rownames(coefficients) <- NULL
  rows <- data.frame(
    term = coefficients$term,
    estimate = coefficients$Estimate,
    std_error = coefficients$`Std. Error`,
    statistic = coefficients$`t value`,
    p_value = coefficients$`Pr(>|t|)`,
    model_formula = "biomarker ~ group + age + batch",
    method = "base_r_lm_fixture",
    clinical_conclusion = "not_generated",
    stringsAsFactors = FALSE
  )
  write.table(rows, file = file.path(output_dir, "tables", "lite_multivariate_association.tsv"), sep = "\t", quote = FALSE, row.names = FALSE)
  writeLines(c(
    "# Lite multivariate limitations",
    "",
    "This is a lightweight fixture multivariate association result for worker and package-contract validation.",
    "It is not a clinical conclusion, diagnosis, prognosis, treatment recommendation, or report-ready clinical analysis."
  ), file.path(output_dir, "reports", "README_lite.md"))
  write_result(
    module_id,
    task_id,
    mode,
    "passed",
    c(),
    c("lite_result_not_formal_analysis", "clinical_conclusion_not_generated", "base_r_fixture_only_no_heavy_resources"),
    "Lite multivariate clinical association completed with base R fixture data."
  )
  write_provenance(module_id, task_id, mode, command, R.version.string, "not_required_for_lite_base_r")
  writeLines(paste(timestamp, "status=passed", paste0("module_id=", module_id), "mode=lite", paste0("task_id=", task_id), "clinical_conclusion=not_generated"), file.path(output_dir, "logs", "worker.log"))
  quit(status = 0)
}

run_lite_immune_infiltration <- function() {
  expression_matrix_path <- resolve_input_path(read_string_field(input_text, "expression_matrix_path", ""))
  signature_table_path <- resolve_input_path(read_string_field(input_text, "signature_table_path", ""))
  blockers <- character(0)
  if (expression_matrix_path == "" || !file.exists(expression_matrix_path)) {
    blockers <- c(blockers, "lite_immune_expression_matrix_missing")
  }
  if (signature_table_path == "" || !file.exists(signature_table_path)) {
    blockers <- c(blockers, "lite_immune_signature_table_missing")
  }
  if (length(blockers) > 0) {
    write_result(module_id, task_id, mode, "blocked", blockers, c(), "Lite immune infiltration blocked because required fixture inputs are missing.")
    write_provenance(module_id, task_id, mode, command, "not_executed", "not_executed")
    writeLines(paste(timestamp, "status=blocked", paste0("module_id=", module_id), paste(blockers, collapse = ";")), file.path(output_dir, "logs", "worker.log"))
    quit(status = 2)
  }
  expression <- read.delim(expression_matrix_path, stringsAsFactors = FALSE, check.names = FALSE)
  signatures <- read.delim(signature_table_path, stringsAsFactors = FALSE)
  if (!("gene" %in% colnames(expression)) || ncol(expression) < 2) {
    write_result(module_id, task_id, mode, "blocked", c("lite_immune_expression_matrix_schema_invalid"), c(), "Lite immune infiltration blocked because expression matrix columns are invalid.")
    write_provenance(module_id, task_id, mode, command, "not_executed", "not_executed")
    writeLines(paste(timestamp, "status=blocked", paste0("module_id=", module_id), "immune_expression_schema_invalid"), file.path(output_dir, "logs", "worker.log"))
    quit(status = 2)
  }
  if (!all(c("signature", "gene") %in% colnames(signatures))) {
    write_result(module_id, task_id, mode, "blocked", c("lite_immune_signature_table_schema_invalid"), c(), "Lite immune infiltration blocked because signature table columns are invalid.")
    write_provenance(module_id, task_id, mode, command, "not_executed", "not_executed")
    writeLines(paste(timestamp, "status=blocked", paste0("module_id=", module_id), "immune_signature_schema_invalid"), file.path(output_dir, "logs", "worker.log"))
    quit(status = 2)
  }
  expression_genes <- as.character(expression$gene)
  expression_values <- as.data.frame(lapply(expression[, setdiff(colnames(expression), "gene"), drop = FALSE], as.numeric), check.names = FALSE)
  if (any(is.na(as.matrix(expression_values)))) {
    write_result(module_id, task_id, mode, "blocked", c("lite_immune_expression_matrix_non_numeric"), c(), "Lite immune infiltration blocked because expression values are not numeric.")
    write_provenance(module_id, task_id, mode, command, "not_executed", "not_executed")
    writeLines(paste(timestamp, "status=blocked", paste0("module_id=", module_id), "immune_non_numeric"), file.path(output_dir, "logs", "worker.log"))
    quit(status = 2)
  }
  expression_matrix <- as.matrix(expression_values)
  rownames(expression_matrix) <- expression_genes
  sample_ids <- colnames(expression_matrix)
  signature_names <- unique(as.character(signatures$signature))
  score_matrix <- matrix(NA_real_, nrow = length(signature_names), ncol = length(sample_ids), dimnames = list(signature_names, sample_ids))
  rows <- list()
  omitted_signatures <- character(0)
  for (signature_name in signature_names) {
    signature_genes <- unique(as.character(signatures$gene[signatures$signature == signature_name]))
    matched_genes <- intersect(signature_genes, rownames(expression_matrix))
    if (length(matched_genes) < 1) {
      omitted_signatures <- c(omitted_signatures, signature_name)
      next
    }
    scores <- colMeans(expression_matrix[matched_genes, , drop = FALSE])
    score_matrix[signature_name, ] <- scores
    for (sample_id in sample_ids) {
      rows[[length(rows) + 1]] <- data.frame(
        signature = signature_name,
        sample_id = sample_id,
        score = unname(scores[[sample_id]]),
        genes_used = paste(matched_genes, collapse = "/"),
        method = "base_r_signature_mean_fixture",
        clinical_conclusion = "not_generated",
        stringsAsFactors = FALSE
      )
    }
  }
  if (length(rows) == 0) {
    write_result(module_id, task_id, mode, "blocked", c("lite_immune_no_signature_gene_overlap"), c(), "Lite immune infiltration blocked because no signature genes overlap the expression matrix.")
    write_provenance(module_id, task_id, mode, command, "not_executed", "not_executed")
    writeLines(paste(timestamp, "status=blocked", paste0("module_id=", module_id), "immune_no_overlap"), file.path(output_dir, "logs", "worker.log"))
    quit(status = 2)
  }
  result_table <- do.call(rbind, rows)
  write.table(result_table, file = file.path(output_dir, "tables", "lite_immune_scores.tsv"), sep = "\t", quote = FALSE, row.names = FALSE)
  score_matrix <- score_matrix[stats::complete.cases(score_matrix), , drop = FALSE]
  plot_path <- file.path(output_dir, "plots", "lite_immune_heatmap.svg")
  palette <- heat.colors(20)
  min_score <- min(score_matrix)
  max_score <- max(score_matrix)
  score_range <- max_score - min_score
  if (score_range == 0) {
    score_range <- 1
  }
  cell_width <- 80
  cell_height <- 32
  left_pad <- 120
  top_pad <- 55
  width <- left_pad + ncol(score_matrix) * cell_width + 30
  height <- top_pad + nrow(score_matrix) * cell_height + 35
  svg_lines <- c(
    paste0('<svg xmlns="http://www.w3.org/2000/svg" width="', width, '" height="', height, '" viewBox="0 0 ', width, ' ', height, '">'),
    '<rect width="100%" height="100%" fill="#ffffff"/>',
    '<text x="16" y="24" font-family="Arial" font-size="16" font-weight="700">Lite immune signature scores</text>'
  )
  for (sample_index in seq_len(ncol(score_matrix))) {
    x <- left_pad + (sample_index - 1) * cell_width + cell_width / 2
    svg_lines <- c(svg_lines, paste0('<text x="', x, '" y="44" text-anchor="middle" font-family="Arial" font-size="11">', colnames(score_matrix)[[sample_index]], '</text>'))
  }
  display_matrix <- score_matrix[nrow(score_matrix):1, , drop = FALSE]
  for (row_index in seq_len(nrow(display_matrix))) {
    y <- top_pad + (row_index - 1) * cell_height
    signature_label <- rownames(display_matrix)[[row_index]]
    svg_lines <- c(svg_lines, paste0('<text x="', left_pad - 8, '" y="', y + 21, '" text-anchor="end" font-family="Arial" font-size="11">', signature_label, '</text>'))
    for (sample_index in seq_len(ncol(display_matrix))) {
      score <- display_matrix[row_index, sample_index]
      palette_index <- max(1, min(length(palette), 1 + floor((score - min_score) / score_range * (length(palette) - 1))))
      x <- left_pad + (sample_index - 1) * cell_width
      svg_lines <- c(svg_lines, paste0('<rect x="', x, '" y="', y, '" width="', cell_width, '" height="', cell_height, '" fill="', palette[[palette_index]], '" stroke="#ffffff"/>'))
      svg_lines <- c(svg_lines, paste0('<text x="', x + cell_width / 2, '" y="', y + 21, '" text-anchor="middle" font-family="Arial" font-size="10" fill="#111111">', format(round(score, 2), nsmall = 2), '</text>'))
    }
  }
  svg_lines <- c(svg_lines, "</svg>")
  writeLines(svg_lines, plot_path)
  warnings <- c("lite_result_not_formal_analysis", "clinical_conclusion_not_generated", "base_r_fixture_only_no_heavy_resources")
  if (length(omitted_signatures) > 0) {
    warnings <- c(warnings, paste0("lite_immune_signatures_without_overlap:", paste(omitted_signatures, collapse = ",")))
  }
  writeLines(c(
    "# Lite immune infiltration limitations",
    "",
    "This is a lightweight fixture immune signature score and heatmap package for worker and package-contract validation.",
    "It is not a clinical immune microenvironment interpretation, diagnosis, prognosis, treatment recommendation, or report-ready analysis."
  ), file.path(output_dir, "reports", "README_lite.md"))
  write_result(
    module_id,
    task_id,
    mode,
    "passed",
    c(),
    warnings,
    "Lite immune infiltration signature scoring completed with base R fixture data."
  )
  write_provenance(module_id, task_id, mode, command, R.version.string, "not_required_for_lite_base_r")
  writeLines(paste(timestamp, "status=passed", paste0("module_id=", module_id), "mode=lite", paste0("task_id=", task_id), "clinical_conclusion=not_generated"), file.path(output_dir, "logs", "worker.log"))
  quit(status = 0)
}

run_lite_docking_adapter_contract <- function() {
  receptor_path <- resolve_input_path(read_string_field(input_text, "receptor_path", ""))
  ligand_path <- resolve_input_path(read_string_field(input_text, "ligand_path", ""))
  config_path <- resolve_input_path(read_string_field(input_text, "config_path", ""))
  blockers <- character(0)
  if (receptor_path == "" || !file.exists(receptor_path)) {
    blockers <- c(blockers, "lite_docking_receptor_missing")
  }
  if (ligand_path == "" || !file.exists(ligand_path)) {
    blockers <- c(blockers, "lite_docking_ligand_missing")
  }
  if (config_path == "" || !file.exists(config_path)) {
    blockers <- c(blockers, "lite_docking_config_missing")
  }
  if (length(blockers) > 0) {
    write_result(module_id, task_id, mode, "blocked", blockers, c(), "Lite docking adapter contract blocked because required fixture inputs are missing.")
    write_provenance(module_id, task_id, mode, command, "not_executed", "not_executed")
    writeLines(paste(timestamp, "status=blocked", paste0("module_id=", module_id), paste(blockers, collapse = ";")), file.path(output_dir, "logs", "worker.log"))
    quit(status = 2)
  }
  command_preview <- paste(
    "vina",
    "--receptor", receptor_path,
    "--ligand", ligand_path,
    "--config", config_path,
    "--out", file.path(output_dir, "tables", "lite_docking_output_not_generated.pdbqt")
  )
  manifest <- data.frame(
    external_tool = "AutoDock Vina",
    execution_status = "not_executed_lite_contract",
    adapter_boundary = "r_chem_full_external_tool_adapter_required_for_full_mode",
    receptor_path = receptor_path,
    receptor_md5 = as.character(tools::md5sum(receptor_path)),
    ligand_path = ligand_path,
    ligand_md5 = as.character(tools::md5sum(ligand_path)),
    config_path = config_path,
    config_md5 = as.character(tools::md5sum(config_path)),
    command_preview = command_preview,
    scientific_result = "not_generated",
    stringsAsFactors = FALSE
  )
  write.table(manifest, file = file.path(output_dir, "tables", "lite_docking_command_manifest.tsv"), sep = "\t", quote = FALSE, row.names = FALSE)
  writeLines(c(
    "# Lite docking adapter limitations",
    "",
    "This is a lightweight external-tool adapter contract package for standard worker and result-package validation.",
    "AutoDock Vina is not executed in lite mode.",
    "No docking score, pose, binding affinity, or scientific docking result is generated.",
    "Full molecular docking must run in the isolated r-chem-full environment with locked tool/resource versions."
  ), file.path(output_dir, "reports", "README_lite.md"))
  write_result(
    module_id,
    task_id,
    mode,
    "passed",
    c(),
    c("lite_result_not_formal_analysis", "external_tool_not_executed_in_lite_mode", "scientific_docking_result_not_generated"),
    "Lite docking adapter contract completed without executing AutoDock Vina."
  )
  write_provenance(
    module_id,
    task_id,
    mode,
    command,
    R.version.string,
    "not_required_for_lite_external_tool_contract",
    '{"AutoDock Vina": "not_executed_lite_contract"}'
  )
  writeLines(paste(timestamp, "status=passed", paste0("module_id=", module_id), "mode=lite", paste0("task_id=", task_id), "external_tool=AutoDock_Vina", "execution=not_executed"), file.path(output_dir, "logs", "worker.log"))
  quit(status = 0)
}

run_lite_molecular_dynamics_adapter_contract <- function() {
  topology_path <- resolve_input_path(read_string_field(input_text, "topology_path", ""))
  coordinate_path <- resolve_input_path(read_string_field(input_text, "coordinate_path", ""))
  mdp_path <- resolve_input_path(read_string_field(input_text, "mdp_path", ""))
  blockers <- character(0)
  if (topology_path == "" || !file.exists(topology_path)) {
    blockers <- c(blockers, "lite_md_topology_missing")
  }
  if (coordinate_path == "" || !file.exists(coordinate_path)) {
    blockers <- c(blockers, "lite_md_coordinates_missing")
  }
  if (mdp_path == "" || !file.exists(mdp_path)) {
    blockers <- c(blockers, "lite_md_mdp_missing")
  }
  if (length(blockers) > 0) {
    write_result(module_id, task_id, mode, "blocked", blockers, c(), "Lite molecular dynamics adapter contract blocked because required fixture inputs are missing.")
    write_provenance(module_id, task_id, mode, command, "not_executed", "not_executed")
    writeLines(paste(timestamp, "status=blocked", paste0("module_id=", module_id), paste(blockers, collapse = ";")), file.path(output_dir, "logs", "worker.log"))
    quit(status = 2)
  }
  tpr_path <- file.path(output_dir, "tables", "lite_md_output_not_generated.tpr")
  trajectory_path <- file.path(output_dir, "tables", "lite_md_trajectory_not_generated.xtc")
  grompp_preview <- paste(
    "gmx", "grompp",
    "-f", mdp_path,
    "-c", coordinate_path,
    "-p", topology_path,
    "-o", tpr_path
  )
  mdrun_preview <- paste(
    "gmx", "mdrun",
    "-s", tpr_path,
    "-x", trajectory_path
  )
  manifest <- data.frame(
    external_tool = "GROMACS",
    execution_status = "not_executed_lite_contract",
    adapter_boundary = "r_chem_gpu_external_tool_adapter_required_for_full_mode",
    topology_path = topology_path,
    topology_md5 = as.character(tools::md5sum(topology_path)),
    coordinate_path = coordinate_path,
    coordinate_md5 = as.character(tools::md5sum(coordinate_path)),
    mdp_path = mdp_path,
    mdp_md5 = as.character(tools::md5sum(mdp_path)),
    grompp_command_preview = grompp_preview,
    mdrun_command_preview = mdrun_preview,
    scientific_result = "not_generated",
    stringsAsFactors = FALSE
  )
  write.table(manifest, file = file.path(output_dir, "tables", "lite_md_command_manifest.tsv"), sep = "\t", quote = FALSE, row.names = FALSE)
  writeLines(c(
    "# Lite molecular dynamics adapter limitations",
    "",
    "This is a lightweight external-tool adapter contract package for standard worker and result-package validation.",
    "GROMACS is not executed in lite mode.",
    "No trajectory, energy table, RMSD, simulation metric, or scientific molecular dynamics result is generated.",
    "Full molecular dynamics must run in the isolated r-chem-gpu environment with locked tool/resource versions."
  ), file.path(output_dir, "reports", "README_lite.md"))
  write_result(
    module_id,
    task_id,
    mode,
    "passed",
    c(),
    c("lite_result_not_formal_analysis", "external_tool_not_executed_in_lite_mode", "scientific_molecular_dynamics_result_not_generated"),
    "Lite molecular dynamics adapter contract completed without executing GROMACS."
  )
  write_provenance(
    module_id,
    task_id,
    mode,
    command,
    R.version.string,
    "not_required_for_lite_external_tool_contract",
    '{"GROMACS": "not_executed_lite_contract"}'
  )
  writeLines(paste(timestamp, "status=passed", paste0("module_id=", module_id), "mode=lite", paste0("task_id=", task_id), "external_tool=GROMACS", "execution=not_executed"), file.path(output_dir, "logs", "worker.log"))
  quit(status = 0)
}

write_provenance <- function(module_id, task_id, mode, command, r_version, bioc_version, external_tool_versions_json = "{}") {
  seed <- read_integer_field(input_text, "random_seed")
  seed_value <- if (is.na(seed)) "null" else as.character(seed)
  input_hash <- as.character(tools::md5sum(input_json))
  parameter_hash <- hash_string(read_object_field_text(input_text, "parameters", "{}"))
  provenance <- paste0(
    "{\n",
    '  "schema_version": "biomedpilot.analysis.provenance.v1",\n',
    '  "module_id": ', json_string(module_id), ",\n",
    '  "mode": ', json_string(mode), ",\n",
    '  "task_id": ', json_string(task_id), ",\n",
    '  "created_at": ', json_string(timestamp), ",\n",
    '  "input_path": ', json_string(input_json), ",\n",
    '  "input_hash": ', json_string(input_hash), ",\n",
    '  "parameter_hash": ', json_string(parameter_hash), ",\n",
    '  "random_seed": ', seed_value, ",\n",
    '  "engine": {"name": "biomedpilot_standard_r_worker", "version": "v1"},\n',
    '  "runtime": {"r_version": ', json_string(r_version), ', "bioconductor_version": ', json_string(bioc_version), ', "package_versions": {}, "external_tool_versions": ', external_tool_versions_json, '},\n',
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

if (mode == "lite" && module_id == "enrichment") {
  run_lite_enrichment_ora()
}

if (mode == "lite" && module_id == "deg") {
  run_lite_deg_two_group()
}

if (mode == "lite" && module_id == "survival") {
  run_lite_survival_km_logrank()
}

if (mode == "lite" && module_id == "univariate") {
  run_lite_univariate_association()
}

if (mode == "lite" && module_id == "multivariate") {
  run_lite_multivariate_association()
}

if (mode == "lite" && module_id == "immune_infiltration") {
  run_lite_immune_infiltration()
}

if (mode == "lite" && module_id == "docking") {
  run_lite_docking_adapter_contract()
}

if (mode == "lite" && module_id == "molecular_dynamics") {
  run_lite_molecular_dynamics_adapter_contract()
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
