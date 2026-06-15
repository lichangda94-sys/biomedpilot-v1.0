from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
ENVIRONMENT_ID = "r-bio-full"
DEFAULT_EVIDENCE_ROOT = Path("external_analysis_environments") / ENVIRONMENT_ID
LOCK_PROFILE = "survival_minimal_v1"
LOCK_PROFILE_VERSION = "v1"
REQUIRED_PROFILE_PACKAGES = [
    "renv",
    "survival",
    "jsonlite",
    "data.table",
    "digest",
    "ggplot2",
    "broom",
    "htmltools",
]
REQUIRED_FILES = [
    "docker_build.log",
    "docker_image_digest.txt",
    "docker_inspect.json",
    "renv_lock_generate.log",
    "renv_lock_generate_metadata.json",
    "renv_bootstrap_version.txt",
    "renv_bootstrap_source.txt",
    "renv_restore.log",
    "renv_status.json",
    "r_session_info.txt",
    "installed_packages.tsv",
    "environment_lock_evidence.json",
    "evidence_manifest.json",
]
EVIDENCE_SOURCES = {"docker_hub", "internal_registry", "local_image_tar"}
SOURCE_FIELDS = [
    "evidence_source",
    "base_image",
    "base_image_expected",
    "source_registry",
    "source_digest",
    "source_attestation_path",
    "image_tar_path",
    "image_tar_hash",
    "registry_preflight_status",
    "registry_preflight_error",
    "docker_build_status",
    "docker_load_status",
    "equivalence_claim",
    "equivalence_validation_status",
]
REQUIRED_LOCK_FIELDS = [
    "environment_id",
    "environment_class",
    "dockerfile_path",
    "docker_image",
    "docker_image_digest",
    "docker_build_log_path",
    "docker_inspect_path",
    "renv_lock_path",
    "renv_lock_hash",
    "lock_profile",
    "lock_profile_version",
    "renv_lock_package_count",
    "required_package_set",
    "missing_required_packages",
    "renv_lock_generate_log_path",
    "renv_lock_generate_metadata_path",
    "renv_bootstrap_status",
    "renv_bootstrap_version",
    "renv_bootstrap_source",
    "renv_bootstrap_version_path",
    "renv_bootstrap_source_path",
    "renv_restore_status",
    "renv_restore_log_path",
    "renv_status_path",
    "r_session_info_path",
    "r_version",
    "bioconductor_version",
    "package_inventory_path",
    "created_at",
    "created_by",
    "validation_status",
    "validation_errors",
    "evidence_hash",
]
OPTIONAL_BY_SOURCE = {
    "docker_hub": {"source_registry", "source_attestation_path", "image_tar_path", "image_tar_hash", "registry_preflight_error", "docker_load_status"},
    "internal_registry": {"image_tar_path", "image_tar_hash", "registry_preflight_error", "docker_load_status"},
    "local_image_tar": {"source_registry", "registry_preflight_error", "docker_build_status"},
}
SHA256_PATTERN = re.compile(r"sha256:([0-9a-fA-F]{64})")
HEX_PATTERN = re.compile(r"^[0-9a-fA-F]{64}$")
PLACEHOLDER_VALUES = {
    "",
    "<pending>",
    "<required>",
    "pending",
    "pending_validation",
    "placeholder",
    "required_before_ready",
    "required_before_full_mode",
    "required_before_full_ready",
    "scaffold",
    "tbd",
    "todo",
}
SELF_REFERENTIAL_EVIDENCE_FILES = {"environment_lock_evidence.json"}
RESTORED_LOCK_STATUSES = {"restored", "locked", "active"}
RENV_RESTORE_FAILURE_PATTERNS = (
    "there is no package called ‘renv’",
    "there is no package called 'renv'",
    "error in loadnamespace",
    "execution halted",
    "renv::restore failed",
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate external r-bio-full environment evidence.")
    parser.add_argument("--evidence-root", default=str(DEFAULT_EVIDENCE_ROOT))
    parser.add_argument("--json-output", default="")
    parser.add_argument("--pretty", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    payload = validate_evidence_root(Path(args.evidence_root))
    text = json.dumps(payload, ensure_ascii=False, indent=2 if args.pretty else None, sort_keys=bool(args.pretty))
    if args.json_output:
        output = Path(args.json_output).expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(text)
    return 0 if payload["status"] == "passed" else 1


def validate_evidence_root(evidence_root: str | Path) -> dict[str, Any]:
    root = _resolve_repo_path(evidence_root)
    required = {name: root / name for name in REQUIRED_FILES}
    required_rows: list[dict[str, Any]] = []
    missing_files: list[str] = []
    partial_blockers: list[str] = []
    invalid_blockers: list[str] = []

    if not root.exists():
        return _payload(
            root,
            status="missing",
            required_rows=[
                _required_row(name, path, exists=False, readable=False)
                for name, path in required.items()
            ],
            missing_files=REQUIRED_FILES,
            partial_blockers=[],
            invalid_blockers=[],
            evidence={},
            evidence_source="docker_hub",
        )
    if not root.is_dir():
        return _payload(
            root,
            status="invalid",
            required_rows=[],
            missing_files=[],
            partial_blockers=[],
            invalid_blockers=["evidence_root_not_directory"],
            evidence={},
            evidence_source="docker_hub",
        )

    for name, path in required.items():
        exists = path.is_file()
        readable = exists and _is_readable(path)
        required_rows.append(_required_row(name, path, exists=exists, readable=readable))
        if not exists:
            missing_files.append(name)
        elif not readable:
            partial_blockers.append(f"required_file_not_readable:{name}")

    evidence = _read_json(required["environment_lock_evidence.json"])
    if not evidence:
        partial_blockers.append("environment_lock_evidence_missing_or_invalid_json")
    else:
        partial_blockers.extend(_field_blockers(evidence))
        partial_blockers.extend(_path_blockers(evidence))
        invalid_blockers.extend(_semantic_blockers(evidence, root))

    evidence_manifest = _read_json(required["evidence_manifest.json"])
    if required["evidence_manifest.json"].is_file() and not evidence_manifest:
        invalid_blockers.append("evidence_manifest_invalid_json")
    elif evidence_manifest:
        partial_blockers.extend(_manifest_blockers(evidence_manifest))

    if required["docker_image_digest.txt"].is_file():
        digest_text = required["docker_image_digest.txt"].read_text(encoding="utf-8", errors="replace").strip()
        if not digest_text:
            partial_blockers.append("docker_image_digest_empty")
        elif _is_placeholder(digest_text):
            invalid_blockers.append("docker_image_digest_placeholder")
        elif not _has_sha256_digest(digest_text):
            invalid_blockers.append("docker_image_digest_invalid")

    if required["docker_build.log"].is_file() and _file_is_empty(required["docker_build.log"]):
        partial_blockers.append("docker_build_log_empty")

    if required["docker_inspect.json"].is_file():
        docker_inspect = _read_json_or_list(required["docker_inspect.json"])
        if docker_inspect is None:
            invalid_blockers.append("docker_inspect_invalid_json")
        elif not _docker_inspect_digests(docker_inspect):
            invalid_blockers.append("docker_inspect_missing_sha256_digest")

    if required["renv_bootstrap_version.txt"].is_file():
        bootstrap_version = required["renv_bootstrap_version.txt"].read_text(encoding="utf-8", errors="replace").strip()
        if not bootstrap_version:
            partial_blockers.append("renv_bootstrap_version_empty")

    if required["renv_bootstrap_source.txt"].is_file():
        bootstrap_source = required["renv_bootstrap_source.txt"].read_text(encoding="utf-8", errors="replace").strip()
        if not bootstrap_source:
            partial_blockers.append("renv_bootstrap_source_empty")

    if required["renv_restore.log"].is_file() and _file_is_empty(required["renv_restore.log"]):
        partial_blockers.append("renv_restore_log_empty")
    elif required["renv_restore.log"].is_file():
        restore_log = required["renv_restore.log"].read_text(encoding="utf-8", errors="replace").lower()
        for pattern in RENV_RESTORE_FAILURE_PATTERNS:
            if pattern.lower() in restore_log:
                partial_blockers.append("renv_restore_log_contains_failure")
                break

    if required["renv_status.json"].is_file():
        renv_status = _read_json_or_list(required["renv_status.json"])
        if renv_status is None:
            partial_blockers.append("renv_status_invalid_json")

    if required["installed_packages.tsv"].is_file():
        content = required["installed_packages.tsv"].read_text(encoding="utf-8", errors="replace").strip()
        if not content:
            partial_blockers.append("installed_packages_empty")
        elif "\t" not in content.splitlines()[0]:
            partial_blockers.append("installed_packages_header_not_tsv")
        else:
            header = content.splitlines()[0].split("\t")
            for required_column in ("Package", "Version"):
                if required_column not in header:
                    partial_blockers.append(f"installed_packages_missing_column:{required_column}")
            partial_blockers.extend(_installed_package_blockers(content))

    if required["r_session_info.txt"].is_file():
        session_info = required["r_session_info.txt"].read_text(encoding="utf-8", errors="replace").strip()
        if not session_info:
            partial_blockers.append("r_session_info_empty")
        elif "R version" not in session_info and "R Under development" not in session_info:
            partial_blockers.append("r_session_info_missing_r_version")

    source = _evidence_source(evidence)
    if evidence:
        partial_blockers.extend(_source_partial_blockers(evidence, root))
        invalid_blockers.extend(_source_invalid_blockers(evidence, root))
        partial_blockers.extend(_renv_lock_content_blockers(evidence))
        partial_blockers.extend(_renv_lock_profile_blockers(evidence))
    timeout_blockers = _registry_timeout_blockers(evidence, root)
    partial_blockers.extend(timeout_blockers)
    status = _status(missing_files, partial_blockers, invalid_blockers)
    if timeout_blockers and status == "partial":
        status = "blocked_by_registry_access"
    return _payload(
        root,
        status=status,
        required_rows=required_rows,
        missing_files=missing_files,
        partial_blockers=partial_blockers,
        invalid_blockers=invalid_blockers,
        evidence=evidence,
        evidence_source=source,
    )


def _field_blockers(evidence: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    source = _evidence_source(evidence)
    empty_allowed = {"validation_errors", "missing_required_packages"}
    for field in REQUIRED_LOCK_FIELDS:
        if field not in evidence or (field not in empty_allowed and _is_empty(evidence.get(field))):
            blockers.append(f"environment_lock_evidence_field_missing:{field}")
        elif field not in empty_allowed and _contains_placeholder(evidence.get(field)):
            blockers.append(f"environment_lock_evidence_field_placeholder:{field}")
    optional = OPTIONAL_BY_SOURCE.get(source, set())
    for field in SOURCE_FIELDS:
        if field in optional:
            continue
        if field not in evidence or _is_empty(evidence.get(field)):
            blockers.append(f"environment_lock_evidence_field_missing:{field}")
        elif _contains_placeholder(evidence.get(field)):
            blockers.append(f"environment_lock_evidence_field_placeholder:{field}")
    if source not in EVIDENCE_SOURCES:
        blockers.append("environment_lock_evidence_source_invalid")
    if evidence.get("environment_id") != ENVIRONMENT_ID:
        blockers.append("environment_lock_evidence_environment_id_invalid")
    if evidence.get("environment_class") != "full":
        blockers.append("environment_lock_evidence_environment_class_invalid")
    if evidence.get("dockerfile_path") != "docker/Dockerfile.r-bio-full":
        blockers.append("environment_lock_evidence_dockerfile_path_invalid")
    if evidence.get("renv_lock_path") != "renv/renv.bio-full.lock":
        blockers.append("environment_lock_evidence_renv_lock_path_invalid")
    if evidence.get("validation_status") == "passed" and evidence.get("validation_errors"):
        blockers.append("environment_lock_evidence_passed_with_validation_errors")
    if evidence.get("validation_status") != "passed":
        blockers.append("environment_lock_evidence_validation_status_not_passed")
    if evidence.get("lock_profile") != LOCK_PROFILE:
        blockers.append("environment_lock_evidence_lock_profile_invalid")
    if evidence.get("lock_profile_version") != LOCK_PROFILE_VERSION:
        blockers.append("environment_lock_evidence_lock_profile_version_invalid")
    required_set = evidence.get("required_package_set")
    if not isinstance(required_set, list) or set(str(item) for item in required_set) != set(REQUIRED_PROFILE_PACKAGES):
        blockers.append("environment_lock_evidence_required_package_set_invalid")
    missing = evidence.get("missing_required_packages")
    if not isinstance(missing, list):
        blockers.append("environment_lock_evidence_missing_required_packages_invalid")
    elif missing:
        blockers.append("environment_lock_evidence_required_packages_missing")
    return blockers


def _semantic_blockers(evidence: dict[str, Any], root: Path) -> list[str]:
    blockers: list[str] = []
    digest = str(evidence.get("docker_image_digest") or "")
    canonical_digest = _extract_sha256_digest(digest)
    if digest and _is_placeholder(digest):
        blockers.append("environment_lock_evidence_docker_image_digest_placeholder")
    elif digest and not canonical_digest:
        blockers.append("environment_lock_evidence_docker_image_digest_invalid")
    docker_digest_file = root / "docker_image_digest.txt"
    if digest and docker_digest_file.is_file():
        file_digest = docker_digest_file.read_text(encoding="utf-8", errors="replace").strip()
        canonical_file_digest = _extract_sha256_digest(file_digest)
        if file_digest and canonical_digest and canonical_file_digest and canonical_digest != canonical_file_digest:
            blockers.append("environment_lock_evidence_docker_digest_mismatch")

    docker_inspect = _read_json_or_list(root / "docker_inspect.json")
    if canonical_digest and docker_inspect is not None:
        inspect_digests = _docker_inspect_digests(docker_inspect)
        if inspect_digests and canonical_digest not in inspect_digests:
            blockers.append("environment_lock_evidence_docker_inspect_digest_mismatch")

    source_digest = str(evidence.get("source_digest") or "")
    canonical_source_digest = _extract_sha256_digest(source_digest)
    if source_digest and _is_placeholder(source_digest):
        blockers.append("environment_lock_evidence_source_digest_placeholder")
    elif source_digest and not canonical_source_digest:
        blockers.append("environment_lock_evidence_source_digest_invalid")
    elif canonical_source_digest and canonical_digest and canonical_source_digest != canonical_digest:
        blockers.append("environment_lock_evidence_source_digest_mismatch")

    renv_hash = str(evidence.get("renv_lock_hash") or "")
    canonical_renv_hash = _extract_sha256_digest(renv_hash)
    if renv_hash and _is_placeholder(renv_hash):
        blockers.append("environment_lock_evidence_renv_lock_hash_placeholder")
    elif renv_hash and not canonical_renv_hash:
        blockers.append("environment_lock_evidence_renv_lock_hash_invalid")
    renv_lock = REPO_ROOT / "renv" / "renv.bio-full.lock"
    if canonical_renv_hash and renv_lock.is_file():
        expected = _sha256_file(renv_lock)
        if canonical_renv_hash != expected:
            blockers.append("environment_lock_evidence_renv_lock_hash_mismatch")

    evidence_hash = str(evidence.get("evidence_hash") or "")
    canonical_evidence_hash = _extract_sha256_digest(evidence_hash)
    hash_required_now = evidence.get("validation_status") == "passed" or evidence.get("status") == "restored"
    if evidence_hash and _is_placeholder(evidence_hash):
        if hash_required_now:
            blockers.append("environment_lock_evidence_hash_placeholder")
    elif evidence_hash and not canonical_evidence_hash:
        blockers.append("environment_lock_evidence_hash_invalid")
    elif canonical_evidence_hash and all((root / name).is_file() for name in REQUIRED_FILES if name not in SELF_REFERENTIAL_EVIDENCE_FILES):
        expected_evidence_hash = compute_evidence_hash(root)
        if canonical_evidence_hash != expected_evidence_hash:
            blockers.append("environment_lock_evidence_hash_mismatch")

    return blockers


def _source_partial_blockers(evidence: dict[str, Any], root: Path) -> list[str]:
    blockers: list[str] = []
    source = _evidence_source(evidence)
    if source == "docker_hub":
        if evidence.get("registry_preflight_status") == "failed":
            blockers.append("docker_hub_registry_preflight_failed")
        if evidence.get("docker_build_status") == "blocked_by_registry_access":
            blockers.append("docker_build_blocked_by_registry_access")
        return blockers

    attestation = str(evidence.get("source_attestation_path") or "")
    if not attestation:
        blockers.append("source_attestation_missing")
    elif not _resolve_repo_path(attestation).is_file():
        blockers.append("source_attestation_not_found")
    elif not _attestation_mentions_base_image(_resolve_repo_path(attestation)):
        blockers.append("source_attestation_equivalence_claim_missing")

    if source == "internal_registry":
        if not str(evidence.get("source_registry") or ""):
            blockers.append("internal_registry_source_registry_missing")
        if not _resolve_repo_path(str(evidence.get("docker_inspect_path") or "")).is_file():
            blockers.append("internal_registry_docker_inspect_missing")
    elif source == "local_image_tar":
        image_tar = str(evidence.get("image_tar_path") or "")
        if not image_tar:
            blockers.append("image_tar_path_missing")
        else:
            tar_path = _resolve_repo_path(image_tar)
            if not tar_path.is_file():
                blockers.append("image_tar_not_found")
            elif not str(evidence.get("image_tar_hash") or ""):
                blockers.append("image_tar_hash_missing")
        if evidence.get("docker_load_status") not in {"loaded", "skipped_dry_run"}:
            blockers.append("docker_load_status_missing_or_incomplete")
    return blockers


def _source_invalid_blockers(evidence: dict[str, Any], root: Path) -> list[str]:
    blockers: list[str] = []
    source = _evidence_source(evidence)
    image_tar_hash = str(evidence.get("image_tar_hash") or "")
    if image_tar_hash and _is_placeholder(image_tar_hash):
        blockers.append("image_tar_hash_placeholder")
    elif image_tar_hash and not _extract_sha256_digest(image_tar_hash):
        blockers.append("image_tar_hash_invalid")
    if source == "local_image_tar":
        image_tar = str(evidence.get("image_tar_path") or "")
        canonical_tar_hash = _extract_sha256_digest(image_tar_hash)
        tar_path = _resolve_repo_path(image_tar) if image_tar else None
        if canonical_tar_hash and tar_path is not None and tar_path.is_file():
            actual = _sha256_file(tar_path)
            if canonical_tar_hash != actual:
                blockers.append("image_tar_hash_mismatch")
    if str(evidence.get("equivalence_validation_status") or "") == "failed":
        blockers.append("equivalence_validation_failed")
    return blockers


def _renv_lock_content_blockers(evidence: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    if evidence.get("renv_bootstrap_status") != "available":
        blockers.append("renv_bootstrap_status_not_available")
    if not str(evidence.get("renv_bootstrap_version") or "").strip():
        blockers.append("renv_bootstrap_version_missing")
    if not str(evidence.get("renv_bootstrap_source") or "").strip():
        blockers.append("renv_bootstrap_source_missing")
    if evidence.get("renv_restore_status") != "restored":
        blockers.append("renv_restore_status_not_restored")

    lock_content = evidence.get("renv_lock_content")
    if not isinstance(lock_content, dict):
        blockers.append("renv_lock_content_invalid")
        return blockers
    policy_status = str(lock_content.get("policy_status") or "")
    if policy_status not in RESTORED_LOCK_STATUSES:
        blockers.append(f"renv_lock_not_restored:{policy_status or 'missing'}")
    if lock_content.get("packages_non_empty") is not True:
        blockers.append("renv_lock_packages_empty")
    package_count = lock_content.get("package_count")
    if not isinstance(package_count, int) or isinstance(package_count, bool) or package_count < 1:
        blockers.append("renv_lock_package_count_invalid")
    return blockers


def _renv_lock_profile_blockers(evidence: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    lock_path = REPO_ROOT / "renv" / "renv.bio-full.lock"
    if not lock_path.is_file():
        return ["renv_lock_missing"]
    lock_payload = _read_json(lock_path)
    if not lock_payload:
        return ["renv_lock_invalid_json"]
    packages = lock_payload.get("Packages")
    if not isinstance(packages, dict) or not packages:
        return ["renv_lock_packages_empty"]
    package_names = {str(name) for name in packages}
    missing = [item for item in REQUIRED_PROFILE_PACKAGES if item not in package_names]
    if missing:
        blockers.append("renv_lock_missing_required_packages:" + ",".join(missing))
    policy = lock_payload.get("BioMedPilotPolicy")
    if not isinstance(policy, dict):
        blockers.append("renv_lock_policy_missing")
    else:
        if policy.get("status") != "restored":
            blockers.append(f"renv_lock_not_restored:{policy.get('status') or 'missing'}")
        if policy.get("lock_profile") != LOCK_PROFILE:
            blockers.append("renv_lock_profile_invalid")
        if policy.get("lock_profile_version") != LOCK_PROFILE_VERSION:
            blockers.append("renv_lock_profile_version_invalid")
    if evidence.get("renv_lock_package_count") != len(packages):
        blockers.append("renv_lock_package_count_mismatch")
    required_set = evidence.get("required_package_set")
    if isinstance(required_set, list):
        missing_from_evidence = [item for item in REQUIRED_PROFILE_PACKAGES if item not in {str(value) for value in required_set}]
        if missing_from_evidence:
            blockers.append("environment_lock_evidence_required_package_set_missing:" + ",".join(missing_from_evidence))
    return blockers


def _installed_package_blockers(content: str) -> list[str]:
    blockers: list[str] = []
    lines = [line for line in content.splitlines() if line.strip()]
    if not lines:
        return ["installed_packages_empty"]
    header = lines[0].split("\t")
    if "Package" not in header or "Version" not in header:
        return []
    package_index = header.index("Package")
    packages: set[str] = set()
    for line in lines[1:]:
        parts = line.split("\t")
        if len(parts) > package_index:
            packages.add(parts[package_index].strip().strip('"'))
    missing = [item for item in REQUIRED_PROFILE_PACKAGES if item not in packages]
    if missing:
        blockers.append("installed_packages_missing_required_packages:" + ",".join(missing))
    return blockers


def _registry_timeout_blockers(evidence: dict[str, Any], root: Path) -> list[str]:
    preflight_text = _read_text(root / "registry_preflight.log")
    build_text = _read_text(root / "docker_build.log")
    status = str(evidence.get("registry_preflight_status") or "").lower() if evidence else ""
    build_status = str(evidence.get("docker_build_status") or "").lower() if evidence else ""
    has_timeout = any(
        token in f"{preflight_text}\n{build_text}".lower()
        for token in ("timeouterror", "timed out", "i/o timeout")
    )
    if status == "failed" or build_status == "blocked_by_registry_access" or has_timeout:
        return ["blocked_by_registry_access"]
    return []


def _manifest_blockers(manifest: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    if manifest.get("environment_id") != ENVIRONMENT_ID:
        blockers.append("evidence_manifest_environment_id_invalid")
    required_files = manifest.get("required_files")
    if not isinstance(required_files, list):
        blockers.append("evidence_manifest_required_files_missing")
        return blockers
    missing = [name for name in REQUIRED_FILES if name not in {str(item) for item in required_files}]
    blockers.extend(f"evidence_manifest_missing_required_file:{name}" for name in missing)
    source = str(manifest.get("evidence_source") or "")
    if source and source not in EVIDENCE_SOURCES:
        blockers.append("evidence_manifest_source_invalid")
    if source == "local_image_tar":
        image_tar_hash = str(manifest.get("image_tar_hash") or "")
        if not image_tar_hash:
            blockers.append("evidence_manifest_image_tar_hash_missing")
        elif not _extract_sha256_digest(image_tar_hash):
            blockers.append("evidence_manifest_image_tar_hash_invalid")
    return blockers


def _path_blockers(evidence: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    for field in (
        "docker_build_log_path",
        "docker_inspect_path",
        "renv_lock_generate_log_path",
        "renv_lock_generate_metadata_path",
        "renv_bootstrap_version_path",
        "renv_bootstrap_source_path",
        "renv_restore_log_path",
        "renv_status_path",
        "r_session_info_path",
        "package_inventory_path",
    ):
        value = str(evidence.get(field) or "")
        if value and not _resolve_repo_path(value).is_file():
            blockers.append(f"environment_lock_evidence_path_not_found:{field}")
    return blockers


def _payload(
    root: Path,
    *,
    status: str,
    required_rows: list[dict[str, Any]],
    missing_files: list[str],
    partial_blockers: list[str],
    invalid_blockers: list[str],
    evidence: dict[str, Any],
    evidence_source: str,
) -> dict[str, Any]:
    blockers = [*missing_files, *partial_blockers, *invalid_blockers]
    return {
        "schema_version": "biomedpilot.analysis.r_bio_full_environment_evidence_validation.v1",
        "environment_id": ENVIRONMENT_ID,
        "status": status,
        "validation_status": status,
        "evidence_root": str(root),
        "evidence_source": evidence_source,
        "base_image": str(evidence.get("base_image") or ""),
        "base_image_expected": str(evidence.get("base_image_expected") or "rocker/r-ver:4.4.2"),
        "source_registry": str(evidence.get("source_registry") or ""),
        "source_digest": str(evidence.get("source_digest") or ""),
        "source_attestation_path": str(evidence.get("source_attestation_path") or ""),
        "image_tar_path": str(evidence.get("image_tar_path") or ""),
        "image_tar_hash": str(evidence.get("image_tar_hash") or ""),
        "docker_image_digest": str(evidence.get("docker_image_digest") or _read_text(root / "docker_image_digest.txt").strip()),
        "lock_profile": str(evidence.get("lock_profile") or ""),
        "lock_profile_version": str(evidence.get("lock_profile_version") or ""),
        "renv_lock_package_count": evidence.get("renv_lock_package_count"),
        "required_package_set": evidence.get("required_package_set") or [],
        "missing_required_packages": evidence.get("missing_required_packages") or [],
        "renv_bootstrap_status": str(evidence.get("renv_bootstrap_status") or ""),
        "renv_bootstrap_version": str(evidence.get("renv_bootstrap_version") or _read_text(root / "renv_bootstrap_version.txt").strip()),
        "renv_bootstrap_source": str(evidence.get("renv_bootstrap_source") or _read_text(root / "renv_bootstrap_source.txt").strip()),
        "renv_restore_status": str(evidence.get("renv_restore_status") or ""),
        "registry_preflight_status": str(evidence.get("registry_preflight_status") or _registry_preflight_status(root)),
        "registry_preflight_error": str(evidence.get("registry_preflight_error") or _registry_preflight_error(root)),
        "docker_build_status": str(evidence.get("docker_build_status") or _docker_build_status(root)),
        "docker_load_status": str(evidence.get("docker_load_status") or ""),
        "equivalence_claim": str(evidence.get("equivalence_claim") or ""),
        "equivalence_validation_status": str(evidence.get("equivalence_validation_status") or ""),
        "required_files": required_rows,
        "missing_files": missing_files,
        "partial_blockers": list(dict.fromkeys(partial_blockers)),
        "invalid_blockers": list(dict.fromkeys(invalid_blockers)),
        "blockers": list(dict.fromkeys(blockers)),
        "docker_evidence_status": _component_status(required_rows, ["docker_build.log", "docker_image_digest.txt", "docker_inspect.json"]),
        "renv_evidence_status": _component_status(required_rows, ["renv_restore.log", "renv_status.json"]),
        "r_session_info_status": _component_status(required_rows, ["r_session_info.txt"]),
        "package_inventory_status": _component_status(required_rows, ["installed_packages.tsv"]),
        "hash_validation_status": "invalid" if invalid_blockers else ("partial" if partial_blockers or missing_files else "passed"),
        "full_gate_next_stage_allowed": status == "passed",
        "environment_lock_validation_status": str(evidence.get("validation_status") or ""),
        "notes": [
            "This validator is read-only.",
            "It does not build Docker images, restore renv, install R packages, or download resources.",
        ],
    }


def _evidence_source(evidence: dict[str, Any]) -> str:
    source = str(evidence.get("evidence_source") or "")
    return source if source else "docker_hub"


def _registry_preflight_status(root: Path) -> str:
    text = _read_text(root / "registry_preflight.log").lower()
    if not text:
        return ""
    if "error=" in text or "timed out" in text or "timeout" in text:
        return "failed"
    if "status=" in text:
        return "passed"
    return "unknown"


def _registry_preflight_error(root: Path) -> str:
    for line in _read_text(root / "registry_preflight.log").splitlines():
        if line.startswith("error="):
            return line.removeprefix("error=")
    return ""


def _docker_build_status(root: Path) -> str:
    text = _read_text(root / "docker_build.log").lower()
    if not text:
        return ""
    if "registry-1.docker.io" in text and ("timeout" in text or "timed out" in text):
        return "blocked_by_registry_access"
    if "successfully built" in text or "writing image sha256" in text:
        return "built"
    return "present"


def _attestation_mentions_base_image(path: Path) -> bool:
    text = _read_text(path).lower()
    return bool(text) and (
        "rocker/r-ver:4.4.2" in text
        or "equivalent" in text
        or "alternative base image" in text
        or "替代基础镜像" in text
        or "等价" in text
    )


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _required_row(name: str, path: Path, *, exists: bool, readable: bool) -> dict[str, Any]:
    return {
        "file": name,
        "path": str(path),
        "exists": exists,
        "readable": readable,
        "status": "present" if exists and readable else ("unreadable" if exists else "missing"),
    }


def _component_status(rows: list[dict[str, Any]], names: list[str]) -> str:
    if not rows:
        return "missing"
    by_name = {str(row.get("file")): row for row in rows}
    statuses = [str(by_name.get(name, {}).get("status") or "missing") for name in names]
    if all(status == "present" for status in statuses):
        return "present"
    if any(status == "present" for status in statuses):
        return "partial"
    return "missing"


def _status(missing_files: list[str], partial_blockers: list[str], invalid_blockers: list[str]) -> str:
    if invalid_blockers:
        return "invalid"
    if missing_files:
        return "partial"
    if partial_blockers:
        return "partial"
    return "passed"


def _resolve_repo_path(value: str | Path) -> Path:
    path = Path(value).expanduser()
    return path.resolve() if path.is_absolute() else (REPO_ROOT / path).resolve()


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def _read_json_or_list(path: Path) -> Any | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _is_readable(path: Path) -> bool:
    try:
        path.open("rb").close()
    except OSError:
        return False
    return True


def _is_empty(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, list | dict):
        return len(value) == 0
    return False


def _has_sha256_digest(value: str) -> bool:
    return _extract_sha256_digest(value) is not None


def _strip_sha256_prefix(value: str) -> str:
    digest = _extract_sha256_digest(value)
    return digest or value.removeprefix("sha256:").lower()


def _extract_sha256_digest(value: str) -> str | None:
    stripped = value.strip()
    match = SHA256_PATTERN.search(stripped)
    if match:
        return match.group(1).lower()
    if HEX_PATTERN.match(stripped):
        return stripped.lower()
    return None


def _is_placeholder(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized in PLACEHOLDER_VALUES:
        return True
    return normalized.startswith("<") and normalized.endswith(">")


def _contains_placeholder(value: Any) -> bool:
    if isinstance(value, str):
        return _is_placeholder(value)
    if isinstance(value, dict):
        return any(_contains_placeholder(item) for item in value.values())
    if isinstance(value, list):
        return any(_contains_placeholder(item) for item in value)
    return False


def _file_is_empty(path: Path) -> bool:
    return not path.read_text(encoding="utf-8", errors="replace").strip()


def _docker_inspect_digests(value: Any) -> set[str]:
    candidates: list[str] = []
    inspect_rows = value if isinstance(value, list) else [value]
    for row in inspect_rows:
        if not isinstance(row, dict):
            continue
        for key in ("Id", "Digest"):
            item = row.get(key)
            if isinstance(item, str):
                candidates.append(item)
        repo_digests = row.get("RepoDigests")
        if isinstance(repo_digests, list):
            candidates.extend(str(item) for item in repo_digests)
    return {digest for item in candidates if (digest := _extract_sha256_digest(item))}


def compute_evidence_hash(root: str | Path) -> str:
    evidence_root = _resolve_repo_path(root)
    digest = hashlib.sha256()
    for name in REQUIRED_FILES:
        if name in SELF_REFERENTIAL_EVIDENCE_FILES:
            continue
        path = evidence_root / name
        file_hash = _sha256_file(path)
        digest.update(f"{name}\0{file_hash}\n".encode("utf-8"))
    return digest.hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
