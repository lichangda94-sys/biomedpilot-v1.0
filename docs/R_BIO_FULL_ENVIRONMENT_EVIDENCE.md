# r-bio-full Environment Evidence

- environment_id: `r-bio-full`
- validation_status: `passed`
- evidence_source: `docker_hub`
- evidence root: `/Users/changdali/Developer/biomedpilot v1.0/Bioinformatics/external_analysis_environments/r-bio-full`
- full gate next stage allowed: `True`
- lock profile: `survival_minimal_v1`
- lock profile version: `v1`
- renv lock package count: `39`

Current status:

- r-bio-full environment evidence has passed validation for the scoped `survival_minimal_v1` lock profile.
- Survival has scoped `survival_minimal_v1` full/formal standard-worker migration evidence.
- This is not global full production activation.
- full activation remains blocked until resource/tool locks and the remaining formal module migrations also pass.

## Evidence Source

| Field | Value |
| --- | --- |
| evidence_source | `docker_hub` |
| base_image | `rocker/r-ver:4.4.2` |
| base_image_expected | `rocker/r-ver:4.4.2` |
| source_registry | `` |
| source_digest | `biomedpilot/r-bio-full@sha256:727167df40a7f1800aea800e8bbb89d7ffd4d9f11c74db5bd2e5f3f30811d2a3` |
| image_tar_path | `` |
| image_tar_hash | `` |

## Required Files

| File | Status | Path |
| --- | --- | --- |
| `docker_build.log` | `present` | `/Users/changdali/Developer/biomedpilot v1.0/Bioinformatics/external_analysis_environments/r-bio-full/docker_build.log` |
| `docker_image_digest.txt` | `present` | `/Users/changdali/Developer/biomedpilot v1.0/Bioinformatics/external_analysis_environments/r-bio-full/docker_image_digest.txt` |
| `docker_inspect.json` | `present` | `/Users/changdali/Developer/biomedpilot v1.0/Bioinformatics/external_analysis_environments/r-bio-full/docker_inspect.json` |
| `renv_lock_generate.log` | `present` | `/Users/changdali/Developer/biomedpilot v1.0/Bioinformatics/external_analysis_environments/r-bio-full/renv_lock_generate.log` |
| `renv_lock_generate_metadata.json` | `present` | `/Users/changdali/Developer/biomedpilot v1.0/Bioinformatics/external_analysis_environments/r-bio-full/renv_lock_generate_metadata.json` |
| `renv_bootstrap_version.txt` | `present` | `/Users/changdali/Developer/biomedpilot v1.0/Bioinformatics/external_analysis_environments/r-bio-full/renv_bootstrap_version.txt` |
| `renv_bootstrap_source.txt` | `present` | `/Users/changdali/Developer/biomedpilot v1.0/Bioinformatics/external_analysis_environments/r-bio-full/renv_bootstrap_source.txt` |
| `renv_restore.log` | `present` | `/Users/changdali/Developer/biomedpilot v1.0/Bioinformatics/external_analysis_environments/r-bio-full/renv_restore.log` |
| `renv_status.json` | `present` | `/Users/changdali/Developer/biomedpilot v1.0/Bioinformatics/external_analysis_environments/r-bio-full/renv_status.json` |
| `r_session_info.txt` | `present` | `/Users/changdali/Developer/biomedpilot v1.0/Bioinformatics/external_analysis_environments/r-bio-full/r_session_info.txt` |
| `installed_packages.tsv` | `present` | `/Users/changdali/Developer/biomedpilot v1.0/Bioinformatics/external_analysis_environments/r-bio-full/installed_packages.tsv` |
| `environment_lock_evidence.json` | `present` | `/Users/changdali/Developer/biomedpilot v1.0/Bioinformatics/external_analysis_environments/r-bio-full/environment_lock_evidence.json` |
| `evidence_manifest.json` | `present` | `/Users/changdali/Developer/biomedpilot v1.0/Bioinformatics/external_analysis_environments/r-bio-full/evidence_manifest.json` |

## Evidence Status

- Docker evidence status: `present`
- renv bootstrap status: `available`
- renv bootstrap version: `1.2.3`
- renv bootstrap source: `https://cloud.r-project.org`
- renv evidence status: `present`
- renv restore status: `restored`
- lock profile: `survival_minimal_v1`
- lock profile version: `v1`
- renv lock package count: `39`
- missing required packages: ``
- R session info status: `present`
- package inventory status: `present`
- hash validation status: `passed`
- registry preflight status: `passed`
- Docker build status: `built`
- Docker load status: ``

## Blockers

- none

## Docker Hub Diagnostic

- registry_preflight_status: `passed`
- registry_preflight_error: ``
- docker_build_status: `built`

## Internal Registry Diagnostic

- source_registry: ``
- source_digest: `biomedpilot/r-bio-full@sha256:727167df40a7f1800aea800e8bbb89d7ffd4d9f11c74db5bd2e5f3f30811d2a3`
- source_attestation_path: ``

## Local Image Tar Diagnostic

- image_tar_path: ``
- image_tar_hash: ``
- docker_load_status: ``

## Source Attestation

- source_attestation_path: ``
- equivalence_claim: `source attestation must prove equivalence to rocker/r-ver:4.4.2 or record the alternative base image`
- equivalence_validation_status: `passed`

## Digest / Hash Validation

- docker_image_digest: `biomedpilot/r-bio-full@sha256:727167df40a7f1800aea800e8bbb89d7ffd4d9f11c74db5bd2e5f3f30811d2a3`
- source_digest: `biomedpilot/r-bio-full@sha256:727167df40a7f1800aea800e8bbb89d7ffd4d9f11c74db5bd2e5f3f30811d2a3`
- image_tar_hash: ``
- hash_validation_status: `passed`

## Lock Profile

- lock_profile: `survival_minimal_v1`
- lock_profile_version: `v1`
- renv_lock_package_count: `39`
- required_package_set: `renv, survival, jsonlite, data.table, digest, ggplot2, broom, htmltools`
- missing_required_packages: ``

## Docker Load / Docker Inspect

- Docker evidence status: `present`
- Docker build status: `built`
- Docker load status: ``

## renv Restore

- renv bootstrap status: `available`
- renv bootstrap version: `1.2.3`
- renv bootstrap source: `https://cloud.r-project.org`
- renv restore status: `restored`
- renv evidence status: `present`

## R Session Info

- R session info status: `present`

## Package Inventory

- package inventory status: `present`

## Docker Preflight Diagnostic

- path: `/Users/changdali/Developer/biomedpilot v1.0/Bioinformatics/external_analysis_environments/r-bio-full/docker_preflight.log`

```text
Client: Docker Engine - Community
 Version:    29.5.3
 Context:    colima
 Debug Mode: false

Server:
 Containers: 3
  Running: 0
  Paused: 0
  Stopped: 3
 Images: 36
 Server Version: 29.5.2
 Storage Driver: overlayfs
  driver-type: io.containerd.snapshotter.v1
 Logging Driver: json-file
 Cgroup Driver: cgroupfs
 Cgroup Version: 2
 Plugins:
  Volume: local
  Network: bridge host ipvlan macvlan null overlay
  Log: awslogs fluentd gcplogs gelf journald json-file local splunk syslog
 CDI spec directories:
  /etc/cdi
  /var/run/cdi
 Swarm: inactive
 Runtimes: io.containerd.runc.v2 runc
 Default Runtime: runc
 Init Binary: docker-init
 containerd version: 193637f7ee8ae5f5aa5248f49e7baa3e6164966e
 runc version: v1.3.5-0-g488fc13e
 init version: de40ad0
 Security Options:
  apparmor
  seccomp
   Profile: builtin
  cgroupns
 Kernel Version: 6.8.0-117-generic
 Operating System: Ubuntu 24.04.4 LTS
 OSType: linux
 Architecture: aarch64
```

## Registry Preflight Diagnostic

- path: `/Users/changdali/Developer/biomedpilot v1.0/Bioinformatics/external_analysis_environments/r-bio-full/registry_preflight.log`

```text
Registry preflight: HEAD https://registry-1.docker.io/v2/
checked_at=2026-06-14T12:42:07Z
proxy_configured=true
HTTP/1.1 200 Connection established

HTTP/2 401
date: Sun, 14 Jun 2026 12:42:08 GMT
content-type: application/json
content-length: 87
docker-distribution-api-version: registry/2.0
www-authenticate: Bearer realm="https://auth.docker.io/token",service="registry.docker.io"
strict-transport-security: max-age=31536000

status=401
```

## Docker Build Diagnostic

- path: `/Users/changdali/Developer/biomedpilot v1.0/Bioinformatics/external_analysis_environments/r-bio-full/docker_build.log`

```text
DEPRECATED: The legacy builder is deprecated and will be removed in a future release.
            Install the buildx component to build images with BuildKit:
            https://docs.docker.com/go/buildx/

Sending build context to Docker daemon  436.1MB

Step 1/17 : FROM rocker/r-ver:4.4.2
 ---> df26749182af
Step 2/17 : ARG CRAN_REPO=https://cloud.r-project.org
 ---> Using cache
 ---> f6132f400a8d
Step 3/17 : ARG HTTP_PROXY
 ---> Using cache
 ---> 38583b2dc63c
Step 4/17 : ARG HTTPS_PROXY
 ---> Using cache
 ---> 064b58543dcd
Step 5/17 : ARG NO_PROXY
 ---> Using cache
 ---> 2ed085722ee5
Step 6/17 : ARG http_proxy
 ---> Using cache
 ---> 1b47635776be
Step 7/17 : ARG https_proxy
 ---> Using cache
 ---> 4727b9a8b54e
Step 8/17 : ARG no_proxy
 ---> Using cache
 ---> da91101a7afd
Step 9/17 : LABEL org.biomedpilot.environment="r-bio-full"
 ---> Using cache
 ---> 6ab70ef0fbdd
Step 10/17 : LABEL org.biomedpilot.analysis-boundary="full-r-worker"
 ---> Using cache
 ---> df38f6b7a0fb
Step 11/17 : LABEL org.biomedpilot.resource-lock-required="true"
 ---> Using cache
 ---> b3b675c51c01
Step 12/17 : LABEL org.biomedpilot.runtime-package-install="forbidden"
 ---> Using cache
 ---> 057e649b5960
Step 13/17 : LABEL org.biomedpilot.renv-bootstrap-source="${CRAN_REPO}"
 ---> Using cache
 ---> e2fcd0813b67
Step 14/17 : WORKDIR /analysis
 ---> Using cache
 ---> 8d93e2b8399c
Step 15/17 : RUN apt-get update     && apt-get install -y --no-install-recommends         ca-certificates         curl         libicu-dev     && rm -rf /var/lib/apt/lists/*
 ---> Using cache
 ---> eb579669d54c
Step 16/17 : RUN Rscript -e 'cran <- Sys.getenv("CRAN_REPO", "https://cloud.r-project.org"); options(repos = c(CRAN = cran)); if (!requireNamespace("renv", quietly = TRUE)) install.packages("renv"); cat(as.character(packageVersion("renv")), "\n", file = "/opt/renv_bootstrap_version.txt"); cat(cran, "\n", file = "/opt/renv_bootstrap_source.txt")'
 ---> Using cache
 ---> 8d89bfe5f374
Step 17/17 : CMD ["Rscript", "/analysis/runners/run_module.R"]
 ---> Using cache
 ---> 727167df40a7
Successfully built 727167df40a7
Successfully tagged biomedpilot/r-bio-full:manual-20260612
```

## Policy

This report is evidence review only. It does not build Docker images, restore renv, install R packages, download resources, or activate full analysis.

Next acceptable evidence sources:

1. Restore the full `renv/renv.bio-full.lock` with real package entries in the isolated r-bio-full environment.
2. Keep Docker Hub evidence, internal registry evidence, or local image tar evidence source-backed with digest/hash and attestation where required.
3. Keep full activation blocked until environment evidence, resource evidence, and formal migration evidence all pass.
