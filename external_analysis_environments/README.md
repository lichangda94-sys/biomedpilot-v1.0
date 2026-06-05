# External Analysis Environments Handoff

This directory is the handoff area for restored full-analysis environment evidence.

It is not part of the default app-dev runtime. Do not place R package libraries,
Docker image layers, downloaded Bioconductor databases, or generated build caches
in this repository.

Allowed tracked files here are small evidence manifests and logs that prove an
external full-analysis environment was built outside the default app-dev
environment. A restored environment is not active until:

- `analysis/registry/environment_lock_evidence.json` references the evidence.
- The evidence payload passes `analysis/schemas/output/environment_lock_evidence.schema.json`.
- `validate_analysis_environment_registry()` reports full readiness.

Expected evidence files should record the environment id, Dockerfile, renv lock,
R version, Bioconductor version, package lock hash, allowed modules, evidence
files, and explicit `runtime_package_install=forbidden` plus
`runtime_resource_download=forbidden` policy.

Current status: no full environment evidence is registered; full mode remains
blocked.
