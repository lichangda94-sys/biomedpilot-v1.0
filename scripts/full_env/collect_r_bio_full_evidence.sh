#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
EVIDENCE_ROOT=""
IMAGE_TAG=""
EXECUTE="false"
SOURCE="docker_hub"
BASE_IMAGE="rocker/r-ver:4.4.2"
INTERNAL_IMAGE=""
IMAGE_TAR=""
SOURCE_DIGEST=""
SOURCE_URL=""
SOURCE_ATTESTATION=""
ALLOW_REGISTRY_TIMEOUT="false"

usage() {
  cat <<'USAGE'
Usage:
  bash scripts/full_env/collect_r_bio_full_evidence.sh \
    --evidence-root external_analysis_environments/r-bio-full \
    --image-tag biomedpilot/r-bio-full:local-YYYYMMDD \
    [--source docker_hub|internal_registry|local_image_tar] \
    [--base-image rocker/r-ver:4.4.2] \
    [--internal-image registry.example/r-bio-full:tag] \
    [--image-tar /path/to/r-bio-full.tar] \
    [--source-digest sha256:...] \
    [--source-url https://registry.example/path] \
    [--source-attestation /path/to/attestation.md] \
    [--allow-registry-timeout] \
    [--dry-run|--execute]

Default mode is --dry-run. Docker build, Docker load, renv restore, and
container inspection require --execute.
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --evidence-root) EVIDENCE_ROOT="${2:-}"; shift 2 ;;
    --image-tag) IMAGE_TAG="${2:-}"; shift 2 ;;
    --source) SOURCE="${2:-}"; shift 2 ;;
    --base-image) BASE_IMAGE="${2:-}"; shift 2 ;;
    --internal-image) INTERNAL_IMAGE="${2:-}"; shift 2 ;;
    --image-tar) IMAGE_TAR="${2:-}"; shift 2 ;;
    --source-digest) SOURCE_DIGEST="${2:-}"; shift 2 ;;
    --source-url) SOURCE_URL="${2:-}"; shift 2 ;;
    --source-attestation) SOURCE_ATTESTATION="${2:-}"; shift 2 ;;
    --allow-registry-timeout) ALLOW_REGISTRY_TIMEOUT="true"; shift ;;
    --dry-run) EXECUTE="false"; shift ;;
    --execute) EXECUTE="true"; shift ;;
    --help|-h) usage; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; usage >&2; exit 2 ;;
  esac
done

if [[ -z "$EVIDENCE_ROOT" ]]; then
  echo "--evidence-root is required" >&2
  exit 2
fi
if [[ -z "$IMAGE_TAG" ]]; then
  echo "--image-tag is required" >&2
  exit 2
fi
if [[ "$EVIDENCE_ROOT" != "external_analysis_environments/r-bio-full" ]]; then
  echo "--evidence-root must be external_analysis_environments/r-bio-full" >&2
  exit 2
fi
case "$SOURCE" in
  docker_hub|internal_registry|local_image_tar) ;;
  *) echo "--source must be docker_hub, internal_registry, or local_image_tar" >&2; exit 2 ;;
esac
if [[ "$SOURCE" == "internal_registry" ]]; then
  [[ -n "$INTERNAL_IMAGE" ]] || { echo "--internal-image is required for internal_registry" >&2; exit 2; }
  [[ -n "$SOURCE_DIGEST" ]] || { echo "--source-digest is required for internal_registry" >&2; exit 2; }
  [[ -n "$SOURCE_URL" ]] || { echo "--source-url is required for internal_registry" >&2; exit 2; }
  [[ -n "$SOURCE_ATTESTATION" ]] || { echo "--source-attestation is required for internal_registry" >&2; exit 2; }
fi
if [[ "$SOURCE" == "local_image_tar" ]]; then
  [[ -n "$IMAGE_TAR" ]] || { echo "--image-tar is required for local_image_tar" >&2; exit 2; }
  [[ -n "$SOURCE_DIGEST" ]] || { echo "--source-digest is required for local_image_tar" >&2; exit 2; }
  [[ -n "$SOURCE_ATTESTATION" ]] || { echo "--source-attestation is required for local_image_tar" >&2; exit 2; }
fi

EVIDENCE_ABS="$REPO_ROOT/$EVIDENCE_ROOT"
COMMAND_LOG="$EVIDENCE_ABS/command_manifest.log"
DOCKER_PREFLIGHT_LOG="$EVIDENCE_ABS/docker_preflight.log"
REGISTRY_PREFLIGHT_LOG="$EVIDENCE_ABS/registry_preflight.log"

planned_commands=(
  "source=$SOURCE"
  "base_image=$BASE_IMAGE"
)
if [[ "$SOURCE" == "docker_hub" ]]; then
  planned_commands+=("docker build --build-arg CRAN_REPO=\${CRAN_REPO:-https://cloud.r-project.org} -f docker/Dockerfile.r-bio-full -t $IMAGE_TAG .")
elif [[ "$SOURCE" == "internal_registry" ]]; then
  planned_commands+=("docker image inspect $INTERNAL_IMAGE")
elif [[ "$SOURCE" == "local_image_tar" ]]; then
  planned_commands+=("docker load --input $IMAGE_TAR")
  planned_commands+=("docker image inspect $IMAGE_TAG")
fi
planned_commands+=(
  "docker run --rm <selected-image> Rscript -e requireNamespace('renv', quietly=TRUE); write renv_bootstrap_version.txt and renv_bootstrap_source.txt"
  "docker run --rm -v $REPO_ROOT:/workspace -w /workspace <selected-image> Rscript -e renv::restore(lockfile='renv/renv.bio-full.lock', prompt=FALSE)"
  "docker run --rm -v $REPO_ROOT:/workspace -w /workspace <selected-image> Rscript -e renv::status(lockfile='renv/renv.bio-full.lock') > renv_status.raw.txt; convert raw status to renv_status.json"
  "docker run --rm -v $REPO_ROOT:/workspace -w /workspace <selected-image> Rscript -e sessionInfo"
  "docker run --rm -v $REPO_ROOT:/workspace -w /workspace <selected-image> Rscript -e installed.packages inventory"
)

if [[ "$EXECUTE" != "true" ]]; then
  echo "DRY RUN: r-bio-full evidence collection would run these commands:"
  printf 'DRY RUN: %s\n' "${planned_commands[@]}"
  echo "DRY RUN: no Docker build, Docker load, renv restore, R package install, or resource download was executed."
  exit 0
fi

mkdir -p "$EVIDENCE_ABS"
: > "$COMMAND_LOG"

log_command() {
  printf '%s\n' "$*" >> "$COMMAND_LOG"
}

if ! command -v docker >/dev/null 2>&1; then
  {
    echo "ERROR: Docker CLI was not found in PATH."
    echo "Install/start Docker Desktop or make the docker command available before running --execute."
  } > "$DOCKER_PREFLIGHT_LOG"
  cat "$DOCKER_PREFLIGHT_LOG" >&2
  exit 127
fi

if ! docker info > "$DOCKER_PREFLIGHT_LOG" 2>&1; then
  {
    echo ""
    echo "ERROR: Docker CLI is available, but the Docker daemon is not reachable."
    echo "Start Docker Desktop or Colima and rerun the evidence collection command."
  } >> "$DOCKER_PREFLIGHT_LOG"
  cat "$DOCKER_PREFLIGHT_LOG" >&2
  exit 125
fi
DOCKER_DAEMON_HTTP_PROXY="$(docker info --format '{{.HTTPProxy}}' 2>/dev/null || true)"
DOCKER_DAEMON_HTTPS_PROXY="$(docker info --format '{{.HTTPSProxy}}' 2>/dev/null || true)"
DOCKER_DAEMON_NO_PROXY="$(docker info --format '{{.NoProxy}}' 2>/dev/null || true)"

{
  echo "Registry preflight: HEAD https://registry-1.docker.io/v2/"
  echo "checked_at=$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
  if [[ -n "${HTTP_PROXY:-}${HTTPS_PROXY:-}${http_proxy:-}${https_proxy:-}" ]]; then
    echo "proxy_configured=true"
  else
    echo "proxy_configured=false"
  fi
} > "$REGISTRY_PREFLIGHT_LOG"
if command -v curl >/dev/null 2>&1; then
  curl_status=0
  curl -sS -I --connect-timeout 30 --max-time 45 \
    -w 'status=%{http_code}\n' \
    https://registry-1.docker.io/v2/ >> "$REGISTRY_PREFLIGHT_LOG" 2>&1 || curl_status=$?
  if [[ "$curl_status" -ne 0 ]]; then
    echo "error=curl_exit:$curl_status" >> "$REGISTRY_PREFLIGHT_LOG"
  fi
else
  python3 - "$REGISTRY_PREFLIGHT_LOG" <<'PY'
import sys
import urllib.error
import urllib.request
from pathlib import Path

log_path = Path(sys.argv[1])
lines = []
try:
    request = urllib.request.Request(
        "https://registry-1.docker.io/v2/",
        method="HEAD",
        headers={"User-Agent": "biomedpilot-r-bio-full-evidence/1.0"},
    )
    try:
        response = urllib.request.urlopen(request, timeout=30)
    except urllib.error.HTTPError as exc:
        response = exc
    lines.append(f"status={response.status}")
    lines.append(f"reason={response.reason}")
    for key, value in response.headers.items():
        if key.lower() in {"docker-distribution-api-version", "www-authenticate", "content-type"}:
            lines.append(f"{key}: {value}")
except Exception as exc:
    lines.append(f"error={type(exc).__name__}: {exc}")
with log_path.open("a", encoding="utf-8") as handle:
    handle.write("\n".join(lines) + "\n")
PY
fi

sha256_file() {
  python3 - "$1" <<'PY'
import hashlib
import sys
from pathlib import Path
path = Path(sys.argv[1])
digest = hashlib.sha256()
with path.open("rb") as handle:
    for chunk in iter(lambda: handle.read(1024 * 1024), b""):
        digest.update(chunk)
print("sha256:" + digest.hexdigest())
PY
}

write_evidence_payload() {
  local validation_status="$1"
  local validation_errors="$2"
  local docker_build_status="$3"
  local docker_load_status="$4"
  local image_tar_hash="$5"
  local effective_image="$6"
  python3 - "$REPO_ROOT" "$EVIDENCE_ROOT" "$IMAGE_TAG" "$SOURCE" "$BASE_IMAGE" "$SOURCE_DIGEST" "$SOURCE_URL" "$SOURCE_ATTESTATION" "$IMAGE_TAR" "$validation_status" "$validation_errors" "$docker_build_status" "$docker_load_status" "$image_tar_hash" "$effective_image" <<'PY'
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

repo = Path(sys.argv[1])
evidence_root = Path(sys.argv[2])
image_tag = sys.argv[3]
source = sys.argv[4]
base_image = sys.argv[5]
source_digest = sys.argv[6]
source_url = sys.argv[7]
source_attestation = sys.argv[8]
image_tar = sys.argv[9]
validation_status = sys.argv[10]
validation_errors = [item for item in sys.argv[11].split(",") if item]
docker_build_status = sys.argv[12]
docker_load_status = sys.argv[13]
image_tar_hash = sys.argv[14]
effective_image = sys.argv[15] or image_tag
root = repo / evidence_root
renv_lock = repo / "renv" / "renv.bio-full.lock"

def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()

def read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""

registry_error = ""
for line in read(root / "registry_preflight.log").splitlines():
    if line.startswith("error="):
        registry_error = line.removeprefix("error=")
docker_digest = read(root / "docker_image_digest.txt").strip() or source_digest
source_digest_value = source_digest or docker_digest
renv_hash = file_sha256(renv_lock) if renv_lock.is_file() else ""
renv_lock_policy_status = "required_before_ready"
renv_package_count = 0
if renv_lock.is_file():
    try:
        renv_lock_payload = json.loads(renv_lock.read_text(encoding="utf-8"))
        renv_lock_policy = renv_lock_payload.get("BioMedPilotPolicy", {})
        if isinstance(renv_lock_policy, dict):
            renv_lock_policy_status = str(renv_lock_policy.get("status") or renv_lock_policy_status)
        packages = renv_lock_payload.get("Packages", {})
        if isinstance(packages, dict):
            renv_package_count = len(packages)
    except json.JSONDecodeError:
        pass
evidence_files = [
    str(evidence_root / "docker_build.log"),
    str(evidence_root / "docker_image_digest.txt"),
    str(evidence_root / "docker_inspect.json"),
    str(evidence_root / "renv_lock_generate.log"),
    str(evidence_root / "renv_lock_generate_metadata.json"),
    str(evidence_root / "renv_bootstrap_version.txt"),
    str(evidence_root / "renv_bootstrap_source.txt"),
    str(evidence_root / "renv_restore.log"),
    str(evidence_root / "renv_status.json"),
    str(evidence_root / "r_session_info.txt"),
    str(evidence_root / "installed_packages.tsv"),
    str(evidence_root / "environment_lock_evidence.json"),
    str(evidence_root / "evidence_manifest.json"),
]
renv_bootstrap_version = read(root / "renv_bootstrap_version.txt").strip()
renv_bootstrap_source = read(root / "renv_bootstrap_source.txt").strip()
required_packages = ["renv", "survival", "jsonlite", "data.table", "digest", "ggplot2", "broom", "htmltools"]
lock_profile = ""
lock_profile_version = ""
missing_required_packages = list(required_packages)
metadata_path = root / "renv_lock_generate_metadata.json"
if metadata_path.is_file():
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        lock_profile = str(metadata.get("lock_profile") or "")
        lock_profile_version = str(metadata.get("lock_profile_version") or "")
    except json.JSONDecodeError:
        metadata = {}
else:
    metadata = {}
if renv_lock.is_file():
    try:
        lock_payload = json.loads(renv_lock.read_text(encoding="utf-8"))
        packages = lock_payload.get("Packages", {})
        if isinstance(packages, dict):
            missing_required_packages = [item for item in required_packages if item not in packages]
        policy = lock_payload.get("BioMedPilotPolicy", {})
        if isinstance(policy, dict):
            lock_profile = lock_profile or str(policy.get("lock_profile") or "")
            lock_profile_version = lock_profile_version or str(policy.get("lock_profile_version") or "")
    except json.JSONDecodeError:
        pass

def extract_sha256(value: str) -> str:
    marker = "sha256:"
    if marker in value:
        return value.split(marker, 1)[1].strip().lower()
    return value.removeprefix("sha256:").strip().lower()

docker_digest_hex = extract_sha256(docker_digest)
evidence_hash = "required_before_ready"
manifest = {
    "schema_version": "biomedpilot.analysis.r_bio_full_evidence_manifest.v1",
    "environment_id": "r-bio-full",
    "evidence_root": str(evidence_root),
    "evidence_source": source,
    "image_tag": image_tag,
    "base_image": base_image,
    "source_digest": source_digest_value,
    "source_url": source_url,
    "source_attestation_path": source_attestation,
    "image_tar_path": image_tar,
    "image_tar_hash": image_tar_hash,
    "renv_bootstrap_version": renv_bootstrap_version,
    "renv_bootstrap_source": renv_bootstrap_source,
    "required_files": [Path(path).name for path in evidence_files],
    "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    "collection_mode": "manual_execute",
}
(root / "evidence_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
if validation_status == "passed":
    bundle_hash = hashlib.sha256()
    for path in evidence_files:
        name = Path(path).name
        if name == "environment_lock_evidence.json":
            continue
        full_path = repo / path
        if not full_path.is_file():
            break
        bundle_hash.update(f"{name}\0{file_sha256(full_path).removeprefix('sha256:')}\n".encode("utf-8"))
    else:
        evidence_hash = bundle_hash.hexdigest()
payload = {
    "schema_version": "biomedpilot.analysis.environment_lock_evidence.v1",
    "environment_id": "r-bio-full",
    "environment_class": "full",
    "status": "restored_candidate" if validation_status == "passed" else validation_status,
    "evidence_source": source,
    "base_image": effective_image if source != "docker_hub" else base_image,
    "base_image_expected": "rocker/r-ver:4.4.2",
    "source_registry": source_url,
    "source_digest": source_digest_value,
    "source_attestation_path": source_attestation,
    "image_tar_path": image_tar,
    "image_tar_hash": image_tar_hash,
    "registry_preflight_status": "failed" if registry_error else ("passed" if read(root / "registry_preflight.log") else ""),
    "registry_preflight_error": registry_error,
    "docker_build_status": docker_build_status,
    "docker_load_status": docker_load_status,
    "docker_image_digest": docker_digest,
    "docker_build_log_path": str(evidence_root / "docker_build.log"),
    "docker_inspect_path": str(evidence_root / "docker_inspect.json"),
    "equivalence_claim": "source attestation must prove equivalence to rocker/r-ver:4.4.2 or record the alternative base image",
    "equivalence_validation_status": "pending" if validation_status != "passed" else "passed",
    "r_version": "R 4.4.2",
    "bioconductor_version": "captured_in_r_session_info",
    "package_lock_hash": {"algorithm": "sha256", "value": renv_hash.removeprefix("sha256:")},
    "renv_lock_content": {"policy_status": renv_lock_policy_status, "packages_non_empty": renv_package_count > 0, "package_count": renv_package_count},
    "docker_image": {
        "image_ref": effective_image,
        "digest": {"algorithm": "sha256", "value": docker_digest_hex},
        "architecture": "captured_in_docker_inspect" if (root / "docker_inspect.json").is_file() else "required_before_ready",
        "build_status": "built" if docker_build_status in {"built", "not_required"} else docker_build_status,
        "build_log": str(evidence_root / "docker_build.log"),
    },
    "docker_image_digest": docker_digest,
    "dockerfile": "docker/Dockerfile.r-bio-full",
    "dockerfile_path": "docker/Dockerfile.r-bio-full",
    "renv_lock": "renv/renv.bio-full.lock",
    "renv_lock_path": "renv/renv.bio-full.lock",
    "renv_lock_hash": renv_hash,
    "lock_profile": lock_profile,
    "lock_profile_version": lock_profile_version,
    "renv_lock_package_count": renv_package_count,
    "required_package_set": required_packages,
    "missing_required_packages": missing_required_packages,
    "renv_lock_generate_log_path": str(evidence_root / "renv_lock_generate.log"),
    "renv_lock_generate_metadata_path": str(evidence_root / "renv_lock_generate_metadata.json"),
    "renv_bootstrap_status": "available" if renv_bootstrap_version else "missing",
    "renv_bootstrap_version": renv_bootstrap_version,
    "renv_bootstrap_source": renv_bootstrap_source,
    "renv_bootstrap_version_path": str(evidence_root / "renv_bootstrap_version.txt"),
    "renv_bootstrap_source_path": str(evidence_root / "renv_bootstrap_source.txt"),
    "renv_restore_status": "restored" if validation_status == "passed" else ("failed" if "renv_restore_failed" in validation_errors else "not_run"),
    "renv_restore_log_path": str(evidence_root / "renv_restore.log"),
    "renv_status_path": str(evidence_root / "renv_status.json"),
    "r_session_info_path": str(evidence_root / "r_session_info.txt"),
    "runtime_package_install": "forbidden",
    "runtime_resource_download": "forbidden",
    "allowed_module_ids": ["deg", "survival", "univariate", "multivariate", "enrichment", "immune_infiltration", "correlation"],
    "evidence_files": evidence_files,
    "package_inventory_path": str(evidence_root / "installed_packages.tsv"),
    "created_at": manifest["created_at"],
    "created_by": os.environ.get("USER", "manual-r-bio-full-evidence-collector"),
    "validation_status": validation_status,
    "validation_errors": validation_errors,
    "evidence_hash": evidence_hash,
}
(root / "environment_lock_evidence.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
PY
}

echo "Collecting r-bio-full evidence into $EVIDENCE_ROOT"
log_command "evidence_root=$EVIDENCE_ROOT"
log_command "image_tag=$IMAGE_TAG"
log_command "source=$SOURCE"
log_command "base_image=$BASE_IMAGE"

if [[ "$SOURCE" == "docker_hub" ]] && grep -qiE 'error=|timed out|timeout' "$REGISTRY_PREFLIGHT_LOG" && [[ "$ALLOW_REGISTRY_TIMEOUT" != "true" ]]; then
  {
    echo "Docker Hub registry preflight failed; evidence collection is blocked by registry access."
    cat "$REGISTRY_PREFLIGHT_LOG"
  } > "$EVIDENCE_ABS/docker_build.log"
  write_evidence_payload "partial" "blocked_by_registry_access" "blocked_by_registry_access" "" "" "$IMAGE_TAG"
  exit 1
fi

(
  cd "$REPO_ROOT"
  EFFECTIVE_IMAGE="$IMAGE_TAG"
  IMAGE_TAR_HASH=""
  DOCKER_BUILD_STATUS="built"
  DOCKER_LOAD_STATUS=""
  DOCKER_RUN_ENV=(-e "CRAN_REPO=${CRAN_REPO:-https://cloud.r-project.org}")
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
  if [[ "$SOURCE" == "docker_hub" ]]; then
    DOCKER_BUILD_ARGS=(--build-arg "CRAN_REPO=${CRAN_REPO:-https://cloud.r-project.org}")
    EFFECTIVE_BUILD_HTTP_PROXY="${DOCKER_DAEMON_HTTP_PROXY:-${HTTP_PROXY:-}}"
    EFFECTIVE_BUILD_HTTPS_PROXY="${DOCKER_DAEMON_HTTPS_PROXY:-${HTTPS_PROXY:-}}"
    EFFECTIVE_BUILD_NO_PROXY="${DOCKER_DAEMON_NO_PROXY:-${NO_PROXY:-}}"
    if [[ -n "$EFFECTIVE_BUILD_HTTP_PROXY" ]]; then
      DOCKER_BUILD_ARGS+=(--build-arg "HTTP_PROXY=$EFFECTIVE_BUILD_HTTP_PROXY")
      DOCKER_BUILD_ARGS+=(--build-arg "http_proxy=$EFFECTIVE_BUILD_HTTP_PROXY")
    fi
    if [[ -n "$EFFECTIVE_BUILD_HTTPS_PROXY" ]]; then
      DOCKER_BUILD_ARGS+=(--build-arg "HTTPS_PROXY=$EFFECTIVE_BUILD_HTTPS_PROXY")
      DOCKER_BUILD_ARGS+=(--build-arg "https_proxy=$EFFECTIVE_BUILD_HTTPS_PROXY")
    fi
    if [[ -n "$EFFECTIVE_BUILD_NO_PROXY" ]]; then
      DOCKER_BUILD_ARGS+=(--build-arg "NO_PROXY=$EFFECTIVE_BUILD_NO_PROXY")
      DOCKER_BUILD_ARGS+=(--build-arg "no_proxy=$EFFECTIVE_BUILD_NO_PROXY")
    fi
    log_command "docker build --build-arg CRAN_REPO=${CRAN_REPO:-https://cloud.r-project.org} -f docker/Dockerfile.r-bio-full -t $IMAGE_TAG ."
    docker build "${DOCKER_BUILD_ARGS[@]}" -f docker/Dockerfile.r-bio-full -t "$IMAGE_TAG" . > "$EVIDENCE_ABS/docker_build.log" 2>&1
  elif [[ "$SOURCE" == "internal_registry" ]]; then
    EFFECTIVE_IMAGE="$INTERNAL_IMAGE"
    DOCKER_BUILD_STATUS="not_required"
    echo "Using internal registry image: $INTERNAL_IMAGE" > "$EVIDENCE_ABS/docker_build.log"
  elif [[ "$SOURCE" == "local_image_tar" ]]; then
    IMAGE_TAR_HASH="$(sha256_file "$IMAGE_TAR")"
    DOCKER_BUILD_STATUS="not_required"
    DOCKER_LOAD_STATUS="loaded"
    log_command "docker load --input $IMAGE_TAR"
    docker load --input "$IMAGE_TAR" > "$EVIDENCE_ABS/docker_load.log" 2>&1
    {
      echo "Loaded local image tar: $IMAGE_TAR"
      cat "$EVIDENCE_ABS/docker_load.log"
    } > "$EVIDENCE_ABS/docker_build.log"
  fi

  log_command "docker image inspect $EFFECTIVE_IMAGE"
  docker image inspect "$EFFECTIVE_IMAGE" > "$EVIDENCE_ABS/docker_inspect.json"
  docker image inspect "$EFFECTIVE_IMAGE" --format '{{index .RepoDigests 0}}' > "$EVIDENCE_ABS/docker_image_digest.txt" 2>/dev/null || true
  if [[ ! -s "$EVIDENCE_ABS/docker_image_digest.txt" ]]; then
    docker image inspect "$EFFECTIVE_IMAGE" --format 'sha256:{{.Id}}' | sed 's/^sha256:sha256:/sha256:/' > "$EVIDENCE_ABS/docker_image_digest.txt"
  fi

  log_command "docker run --rm $EFFECTIVE_IMAGE Rscript -e renv bootstrap check"
  RENV_BOOTSTRAP_STATUS=0
  docker run --rm "${DOCKER_RUN_ENV[@]}" "$EFFECTIVE_IMAGE" \
    Rscript -e "if (!requireNamespace('renv', quietly=TRUE)) quit(status=42); cat(as.character(packageVersion('renv')), '\n')" \
    > "$EVIDENCE_ABS/renv_bootstrap_version.txt" 2> "$EVIDENCE_ABS/renv_bootstrap_check.log" || RENV_BOOTSTRAP_STATUS=$?
  docker run --rm "${DOCKER_RUN_ENV[@]}" "$EFFECTIVE_IMAGE" \
    Rscript -e "path <- '/opt/renv_bootstrap_source.txt'; if (file.exists(path)) cat(readLines(path), sep='\n') else cat(Sys.getenv('CRAN_REPO', 'unknown'), '\n')" \
    > "$EVIDENCE_ABS/renv_bootstrap_source.txt" 2>> "$EVIDENCE_ABS/renv_bootstrap_check.log" || true
  if [[ "$RENV_BOOTSTRAP_STATUS" -ne 0 || ! -s "$EVIDENCE_ABS/renv_bootstrap_version.txt" ]]; then
    log_command "renv bootstrap exit_status=$RENV_BOOTSTRAP_STATUS"
    write_evidence_payload "partial" "renv_bootstrap_missing" "$DOCKER_BUILD_STATUS" "$DOCKER_LOAD_STATUS" "$IMAGE_TAR_HASH" "$EFFECTIVE_IMAGE"
    exit 1
  fi

  cat > "$EVIDENCE_ABS/renv_restore_driver.R" <<'RSCRIPT'
options(
  repos = c(CRAN = Sys.getenv("CRAN_REPO", "https://cloud.r-project.org")),
  download.file.method = "libcurl",
  timeout = 600
)
lockfile <- "renv/renv.bio-full.lock"
project <- getwd()
library_path <- renv::paths$library(project = project)
dir.create(library_path, recursive = TRUE, showWarnings = FALSE)
.libPaths(c(library_path, .libPaths()))

lock_lines <- readLines(lockfile, warn = FALSE)
package_start <- grep('^  "Packages": \\{', lock_lines)
policy_start <- grep('^  "BioMedPilotPolicy":', lock_lines)
package_lines <- if (length(package_start) && length(policy_start)) {
  lock_lines[(package_start[[1]] + 1):(policy_start[[1]] - 1)]
} else {
  character()
}
lock_packages <- sub(
  '^    "([^"]+)": \\{.*',
  "\\1",
  grep('^    "[^"]+": \\{', package_lines, value = TRUE)
)
installed <- rownames(installed.packages(lib.loc = .libPaths()))
missing <- setdiff(lock_packages, installed)
cat("lock_package_count=", length(lock_packages), "\n", sep = "")
cat("missing_before_prewarm=", paste(missing, collapse = ","), "\n", sep = "")
if (length(missing)) {
  utils::install.packages(missing, lib = library_path, dependencies = FALSE)
}
renv::restore(project = project, lockfile = lockfile, prompt = FALSE)
RSCRIPT

  log_command "docker run --rm -v $REPO_ROOT:/workspace -w /workspace $EFFECTIVE_IMAGE Rscript $EVIDENCE_ROOT/renv_restore_driver.R"
  RENV_RESTORE_STATUS=0
  docker run --rm "${DOCKER_RUN_ENV[@]}" -v "$REPO_ROOT:/workspace" -w /workspace "$EFFECTIVE_IMAGE" \
    Rscript "$EVIDENCE_ROOT/renv_restore_driver.R" \
    > "$EVIDENCE_ABS/renv_restore.log" 2>&1 || RENV_RESTORE_STATUS=$?
  if [[ "$RENV_RESTORE_STATUS" -ne 0 ]]; then
    log_command "renv restore exit_status=$RENV_RESTORE_STATUS"
    write_evidence_payload "partial" "renv_restore_failed" "$DOCKER_BUILD_STATUS" "$DOCKER_LOAD_STATUS" "$IMAGE_TAR_HASH" "$EFFECTIVE_IMAGE"
    exit 1
  fi

  log_command "docker run --rm -v $REPO_ROOT:/workspace -w /workspace $EFFECTIVE_IMAGE Rscript -e renv::status(lockfile='renv/renv.bio-full.lock')"
  docker run --rm "${DOCKER_RUN_ENV[@]}" -v "$REPO_ROOT:/workspace" -w /workspace "$EFFECTIVE_IMAGE" \
    Rscript -e "status <- capture.output(renv::status(lockfile='renv/renv.bio-full.lock')); writeLines(status)" \
    > "$EVIDENCE_ABS/renv_status.raw.txt" 2>&1
  python3 - "$EVIDENCE_ABS/renv_status.raw.txt" "$EVIDENCE_ABS/renv_status.json" <<'PY'
import json
import sys
from pathlib import Path

raw_path = Path(sys.argv[1])
json_path = Path(sys.argv[2])
lines = raw_path.read_text(encoding="utf-8", errors="replace").splitlines()
json_path.write_text(json.dumps({"source": "renv::status", "status_output": lines}, indent=2), encoding="utf-8")
PY

  log_command "docker run --rm -v $REPO_ROOT:/workspace -w /workspace $EFFECTIVE_IMAGE Rscript -e sessionInfo"
  docker run --rm "${DOCKER_RUN_ENV[@]}" -v "$REPO_ROOT:/workspace" -w /workspace "$EFFECTIVE_IMAGE" \
    Rscript -e "lib <- renv::paths\$library(project=getwd()); if (dir.exists(lib)) .libPaths(c(lib, .libPaths())); writeLines(capture.output(sessionInfo()), '$EVIDENCE_ROOT/r_session_info.txt')" \
    >> "$COMMAND_LOG" 2>&1

  log_command "docker run --rm -v $REPO_ROOT:/workspace -w /workspace $EFFECTIVE_IMAGE Rscript -e installed.packages inventory"
  docker run --rm "${DOCKER_RUN_ENV[@]}" -v "$REPO_ROOT:/workspace" -w /workspace "$EFFECTIVE_IMAGE" \
    Rscript -e "lib <- renv::paths\$library(project=getwd()); if (dir.exists(lib)) .libPaths(c(lib, .libPaths())); write.table(as.data.frame(installed.packages()[,c('Package','Version','LibPath')]), '$EVIDENCE_ROOT/installed_packages.tsv', sep='\t', row.names=FALSE, quote=FALSE)" \
    >> "$COMMAND_LOG" 2>&1

  write_evidence_payload "passed" "" "$DOCKER_BUILD_STATUS" "$DOCKER_LOAD_STATUS" "$IMAGE_TAR_HASH" "$EFFECTIVE_IMAGE"
)

if ! python3 "$REPO_ROOT/scripts/full_env/validate_r_bio_full_evidence.py" \
    --evidence-root "$EVIDENCE_ROOT" \
    --json-output "$EVIDENCE_ABS/evidence_validation.json" \
    --pretty; then
  python3 - "$EVIDENCE_ABS/environment_lock_evidence.json" "$EVIDENCE_ABS/evidence_validation.json" <<'PY'
import json
import sys
from pathlib import Path

evidence_path = Path(sys.argv[1])
validation_path = Path(sys.argv[2])
evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
validation = json.loads(validation_path.read_text(encoding="utf-8")) if validation_path.is_file() else {}
evidence["validation_status"] = "partial"
evidence["validation_errors"] = list(validation.get("blockers") or ["validation_failed"])
evidence_path.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
PY
  exit 1
fi
