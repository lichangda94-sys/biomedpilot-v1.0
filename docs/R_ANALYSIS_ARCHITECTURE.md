# R Analysis Architecture

Date: 2026-06-04

## Boundary

BioMedPilot analysis modules use this target pattern:

```text
Frontend
  -> task submission / progress / result display
Main backend
  -> task creation / queue / status / files / result index
Dedicated analysis worker
  -> R packages, Bioconductor packages, databases, and external scientific tools
Standard result package
  -> result.json / provenance.json / tables / plots / reports / logs
```

R and external tools are not default frontend or main-backend runtime dependencies.

## Modes

| Mode | Purpose | Dependency policy |
| --- | --- | --- |
| `mock` | Frontend, API, task-flow, and result-display development | No heavy R packages; fixed fixture input/output. |
| `lite` | Lightweight real analysis during daily development | Lightweight packages/resources only; no large downloads. |
| `full` | Formal analysis and full integration testing | Dedicated analysis container, renv lock, or isolated analysis environment. |

## Repository Contract

The initial contract is declared under:

```text
analysis/
  registry/analysis_modules.json
  schemas/input/module_input.schema.json
  schemas/output/result_package.schema.json
  runners/run_module.R
  fixtures/
  resources/manifest.json
```

`analysis/runners/run_module.R` is a base R mock-mode boundary runner. It does not install packages and does not enable full analysis. Existing Bioinformatics algorithms still need staged migration into this contract.

## Result Package

Every module must eventually write:

```text
result.json
provenance.json
tables/
plots/
reports/
logs/
```

`provenance.json` must record engine version, R version, package versions, external tool versions, input hash, parameter hash, random seed, and command.

