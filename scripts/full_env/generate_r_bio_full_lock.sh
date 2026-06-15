#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
IMAGE_TAG=""
PROFILE="survival_minimal_v1"
CRAN_REPO="https://cloud.r-project.org"
EXECUTE="false"
EVIDENCE_ROOT="external_analysis_environments/r-bio-full"
REQUIRED_PACKAGES=(renv survival jsonlite data.table digest ggplot2 broom htmltools)

usage() {
  cat <<'USAGE'
Usage:
  bash scripts/full_env/generate_r_bio_full_lock.sh \
    --image-tag biomedpilot/r-bio-full:manual-20260612 \
    --profile survival_minimal_v1 \
    --cran-repo https://cloud.r-project.org \
    [--dry-run|--execute]

Default mode is --dry-run. Passing --execute installs the survival_minimal_v1
CRAN package set inside the selected r-bio-full Docker image and writes
renv/renv.bio-full.lock only after the generated lock has non-empty Packages
and includes the required profile packages.
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --image-tag) IMAGE_TAG="${2:-}"; shift 2 ;;
    --profile) PROFILE="${2:-}"; shift 2 ;;
    --cran-repo) CRAN_REPO="${2:-}"; shift 2 ;;
    --dry-run) EXECUTE="false"; shift ;;
    --execute) EXECUTE="true"; shift ;;
    --help|-h) usage; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; usage >&2; exit 2 ;;
  esac
done

if [[ -z "$IMAGE_TAG" ]]; then
  echo "--image-tag is required" >&2
  exit 2
fi
if [[ "$PROFILE" != "survival_minimal_v1" ]]; then
  echo "--profile must be survival_minimal_v1" >&2
  exit 2
fi
if [[ -z "$CRAN_REPO" ]]; then
  echo "--cran-repo is required" >&2
  exit 2
fi

EVIDENCE_ABS="$REPO_ROOT/$EVIDENCE_ROOT"
LOG_PATH="$EVIDENCE_ABS/renv_lock_generate.log"
METADATA_PATH="$EVIDENCE_ABS/renv_lock_generate_metadata.json"
GENERATED_LOCK="$EVIDENCE_ABS/renv.bio-full.generated.lock"
FINAL_LOCK="$REPO_ROOT/renv/renv.bio-full.lock"
PACKAGE_LIST_CSV="$(IFS=,; echo "${REQUIRED_PACKAGES[*]}")"

if [[ "$EXECUTE" != "true" ]]; then
  echo "DRY RUN: would generate renv/renv.bio-full.lock in Docker image $IMAGE_TAG"
  echo "DRY RUN: profile=$PROFILE"
  echo "DRY RUN: cran_repo=$CRAN_REPO"
  echo "DRY RUN: packages=$PACKAGE_LIST_CSV"
  echo "DRY RUN: no R package installation, Docker run, or lockfile write was executed."
  exit 0
fi

mkdir -p "$EVIDENCE_ABS"

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker CLI was not found in PATH." >&2
  exit 127
fi
if ! docker image inspect "$IMAGE_TAG" >/dev/null 2>&1; then
  echo "Docker image not found: $IMAGE_TAG" >&2
  exit 2
fi

DOCKER_DAEMON_HTTP_PROXY="$(docker info --format '{{.HTTPProxy}}' 2>/dev/null || true)"
DOCKER_DAEMON_HTTPS_PROXY="$(docker info --format '{{.HTTPSProxy}}' 2>/dev/null || true)"
DOCKER_DAEMON_NO_PROXY="$(docker info --format '{{.NoProxy}}' 2>/dev/null || true)"
DOCKER_RUN_ENV=(-e "CRAN_REPO=$CRAN_REPO" -e "LOCK_PROFILE=$PROFILE" -e "REQUIRED_PACKAGES=$PACKAGE_LIST_CSV" -e "GENERATED_LOCK=$EVIDENCE_ROOT/renv.bio-full.generated.lock")
EFFECTIVE_RUN_HTTP_PROXY="${DOCKER_DAEMON_HTTP_PROXY:-${HTTP_PROXY:-}}"
EFFECTIVE_RUN_HTTPS_PROXY="${DOCKER_DAEMON_HTTPS_PROXY:-${HTTPS_PROXY:-}}"
EFFECTIVE_RUN_NO_PROXY="${DOCKER_DAEMON_NO_PROXY:-${NO_PROXY:-}}"
if [[ -n "$EFFECTIVE_RUN_HTTP_PROXY" ]]; then
  DOCKER_RUN_ENV+=(-e "HTTP_PROXY=$EFFECTIVE_RUN_HTTP_PROXY" -e "http_proxy=$EFFECTIVE_RUN_HTTP_PROXY")
fi
if [[ -n "$EFFECTIVE_RUN_HTTPS_PROXY" ]]; then
  DOCKER_RUN_ENV+=(-e "HTTPS_PROXY=$EFFECTIVE_RUN_HTTPS_PROXY" -e "https_proxy=$EFFECTIVE_RUN_HTTPS_PROXY")
fi
if [[ -n "$EFFECTIVE_RUN_NO_PROXY" ]]; then
  DOCKER_RUN_ENV+=(-e "NO_PROXY=$EFFECTIVE_RUN_NO_PROXY" -e "no_proxy=$EFFECTIVE_RUN_NO_PROXY")
fi

DOCKER_DIGEST="$(docker image inspect "$IMAGE_TAG" --format '{{index .RepoDigests 0}}' 2>/dev/null || true)"
if [[ -z "$DOCKER_DIGEST" || "$DOCKER_DIGEST" == "<no value>" ]]; then
  DOCKER_DIGEST="$(docker image inspect "$IMAGE_TAG" --format 'sha256:{{.Id}}' | sed 's/^sha256:sha256:/sha256:/')"
fi
GENERATED_AT="$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
GENERATED_BY="${USER:-manual-r-bio-full-lock-generator}"
COMMAND="docker run --rm -v $REPO_ROOT:/workspace -w /workspace -e CRAN_REPO=$CRAN_REPO -e LOCK_PROFILE=$PROFILE -e REQUIRED_PACKAGES=$PACKAGE_LIST_CSV $IMAGE_TAG Rscript <survival_minimal_v1_lock_generator>"

rm -f "$GENERATED_LOCK"

docker run --rm -i \
  -v "$REPO_ROOT:/workspace" \
  -w /workspace \
  "${DOCKER_RUN_ENV[@]}" \
  "$IMAGE_TAG" \
  Rscript - <<'RSCRIPT' > "$LOG_PATH" 2>&1
cran <- Sys.getenv("CRAN_REPO", "https://cloud.r-project.org")
profile <- Sys.getenv("LOCK_PROFILE", "survival_minimal_v1")
required <- strsplit(Sys.getenv("REQUIRED_PACKAGES"), ",", fixed = TRUE)[[1]]
output <- Sys.getenv("GENERATED_LOCK")

options(repos = c(CRAN = cran))
options(download.file.method = "libcurl", timeout = 600)
cat("lock_profile=", profile, "\n", sep = "")
cat("cran_repo=", cran, "\n", sep = "")
cat("required_packages=", paste(required, collapse = ","), "\n", sep = "")
cat("output=", output, "\n", sep = "")

if (!requireNamespace("renv", quietly = TRUE)) {
  stop("renv is not available inside the r-bio-full image")
}

work <- tempfile("biomedpilot-r-bio-full-lock-")
dir.create(work, recursive = TRUE)
project_library <- file.path(work, "library")
dir.create(project_library, recursive = TRUE, showWarnings = FALSE)
.libPaths(c(project_library, .libPaths()))
utils::install.packages(required, lib = project_library, dependencies = c("Depends", "Imports", "LinkingTo"))
renv::snapshot(
  project = work,
  library = project_library,
  lockfile = file.path("/workspace", output),
  packages = required,
  prompt = FALSE,
  type = "all",
  force = TRUE
)

lock <- jsonlite::read_json(file.path("/workspace", output), simplifyVector = FALSE)
packages <- lock$Packages
if (!is.list(packages) || length(packages) == 0) {
  stop("generated lock has empty Packages")
}
missing <- setdiff(required, names(packages))
if (length(missing) > 0) {
  stop(sprintf("generated lock missing required packages: %s", paste(missing, collapse = ",")))
}
cat("generated_package_count=", length(packages), "\n", sep = "")
RSCRIPT

python3 - "$GENERATED_LOCK" "$FINAL_LOCK" "$METADATA_PATH" "$PROFILE" "$CRAN_REPO" "$IMAGE_TAG" "$DOCKER_DIGEST" "$GENERATED_AT" "$GENERATED_BY" "$COMMAND" "$PACKAGE_LIST_CSV" "$LOG_PATH" <<'PY'
import hashlib
import json
import shutil
import sys
from pathlib import Path

generated_lock = Path(sys.argv[1])
final_lock = Path(sys.argv[2])
metadata_path = Path(sys.argv[3])
profile = sys.argv[4]
cran_repo = sys.argv[5]
image_tag = sys.argv[6]
docker_digest = sys.argv[7]
generated_at = sys.argv[8]
generated_by = sys.argv[9]
command = sys.argv[10]
required = [item for item in sys.argv[11].split(",") if item]
log_path = sys.argv[12]

if not generated_lock.is_file():
    raise SystemExit("generated lock was not written")
payload = json.loads(generated_lock.read_text(encoding="utf-8"))
packages = payload.get("Packages")
if not isinstance(packages, dict) or not packages:
    raise SystemExit("generated lock has empty Packages")
missing = [item for item in required if item not in packages]
if missing:
    raise SystemExit("generated lock missing required packages: " + ",".join(missing))

payload["BioMedPilotPolicy"] = {
    "schema_version": "biomedpilot.renv_policy.v1",
    "environment": "r-bio-full",
    "status": "restored",
    "lock_profile": profile,
    "lock_profile_version": "v1",
    "required_package_set": required,
    "heavy_analysis_dependencies_allowed": True,
    "runtime_package_install": "forbidden",
    "resource_lock_required": True,
    "notes": (
        "survival_minimal_v1 proves the first r-bio-full formal pre-migration "
        "lock profile only; it is not global full production readiness."
    ),
}
final_lock.parent.mkdir(parents=True, exist_ok=True)
tmp_final = final_lock.with_suffix(final_lock.suffix + ".tmp")
tmp_final.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
final_packages = json.loads(tmp_final.read_text(encoding="utf-8")).get("Packages", {})
if not isinstance(final_packages, dict) or not final_packages:
    tmp_final.unlink(missing_ok=True)
    raise SystemExit("refusing to write empty final lock")
shutil.move(str(tmp_final), str(final_lock))

digest = hashlib.sha256(final_lock.read_bytes()).hexdigest()
metadata = {
    "schema_version": "biomedpilot.analysis.r_bio_full_lock_generate_metadata.v1",
    "environment_id": "r-bio-full",
    "lock_profile": profile,
    "lock_profile_version": "v1",
    "image_tag": image_tag,
    "docker_image_digest": docker_digest,
    "cran_repo": cran_repo,
    "required_package_set": required,
    "renv_lock_path": "renv/renv.bio-full.lock",
    "renv_lock_hash": "sha256:" + digest,
    "renv_lock_package_count": len(final_packages),
    "generated_at": generated_at,
    "generated_by": generated_by,
    "command": command,
    "log_path": log_path,
}
metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
print(f"wrote {final_lock}")
print(f"renv_lock_hash=sha256:{digest}")
print(f"renv_lock_package_count={len(final_packages)}")
PY
