from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
COLLECT_SCRIPT = ROOT / "scripts" / "full_env" / "collect_r_bio_full_evidence.sh"
VALIDATE_SCRIPT = ROOT / "scripts" / "full_env" / "validate_r_bio_full_evidence.py"
RENDER_SCRIPT = ROOT / "scripts" / "full_env" / "render_r_bio_full_evidence_report.py"
GATE_SCRIPT = ROOT / "scripts" / "analysis_architecture_gate.py"
GENERATE_LOCK_SCRIPT = ROOT / "scripts" / "full_env" / "generate_r_bio_full_lock.sh"
SURVIVAL_MINIMAL_PACKAGES = [
    "renv",
    "survival",
    "jsonlite",
    "data.table",
    "digest",
    "ggplot2",
    "broom",
    "htmltools",
]
VALIDATOR_SPEC = importlib.util.spec_from_file_location("validate_r_bio_full_evidence", VALIDATE_SCRIPT)
assert VALIDATOR_SPEC is not None
VALIDATOR_MODULE = importlib.util.module_from_spec(VALIDATOR_SPEC)
assert VALIDATOR_SPEC.loader is not None
VALIDATOR_SPEC.loader.exec_module(VALIDATOR_MODULE)


def read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_collect_r_bio_full_evidence_default_dry_run_does_not_execute_docker_build() -> None:
    completed = subprocess.run(
        [
            "bash",
            str(COLLECT_SCRIPT),
            "--evidence-root",
            "external_analysis_environments/r-bio-full",
            "--image-tag",
            "biomedpilot/r-bio-full:local-test",
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    assert completed.returncode == 0
    assert "DRY RUN" in completed.stdout
    assert "no Docker build, Docker load, renv restore, R package install, or resource download was executed" in completed.stdout
    assert "docker build --build-arg CRAN_REPO=" in completed.stdout
    assert "-f docker/Dockerfile.r-bio-full" in completed.stdout


def test_generate_r_bio_full_lock_default_dry_run_does_not_write_lock() -> None:
    before = (ROOT / "renv" / "renv.bio-full.lock").read_text(encoding="utf-8")
    completed = subprocess.run(
        [
            "bash",
            str(GENERATE_LOCK_SCRIPT),
            "--image-tag",
            "biomedpilot/r-bio-full:local-test",
            "--profile",
            "survival_minimal_v1",
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    after = (ROOT / "renv" / "renv.bio-full.lock").read_text(encoding="utf-8")

    assert completed.returncode == 0
    assert "DRY RUN" in completed.stdout
    assert "survival_minimal_v1" in completed.stdout
    assert "no R package installation, Docker run, or lockfile write was executed" in completed.stdout
    assert after == before


def test_collect_r_bio_full_evidence_dry_run_does_not_execute_renv_restore() -> None:
    completed = subprocess.run(
        [
            "bash",
            str(COLLECT_SCRIPT),
            "--evidence-root",
            "external_analysis_environments/r-bio-full",
            "--image-tag",
            "biomedpilot/r-bio-full:local-test",
            "--dry-run",
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    assert completed.returncode == 0
    assert "renv::restore" in completed.stdout
    assert "no Docker build, Docker load, renv restore, R package install, or resource download was executed" in completed.stdout


def test_collect_r_bio_full_local_image_tar_dry_run_does_not_require_existing_tar() -> None:
    completed = subprocess.run(
        [
            "bash",
            str(COLLECT_SCRIPT),
            "--evidence-root",
            "external_analysis_environments/r-bio-full",
            "--image-tag",
            "biomedpilot/r-bio-full:local-test",
            "--source",
            "local_image_tar",
            "--image-tar",
            "/tmp/nonexistent-r-bio-full.tar",
            "--source-digest",
            "sha256:" + "a" * 64,
            "--source-attestation",
            "/tmp/nonexistent-attestation.md",
            "--dry-run",
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    assert completed.returncode == 0
    assert "DRY RUN: docker load --input /tmp/nonexistent-r-bio-full.tar" in completed.stdout
    assert "no Docker build, Docker load, renv restore" in completed.stdout


def test_validate_r_bio_full_evidence_missing_root_returns_missing(tmp_path: Path) -> None:
    output = tmp_path / "missing.json"
    completed = subprocess.run(
        [
            sys.executable,
            str(VALIDATE_SCRIPT),
            "--evidence-root",
            str(tmp_path / "missing-root"),
            "--json-output",
            str(output),
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    payload = read_json(output)
    assert completed.returncode == 1
    assert payload["status"] == "missing"
    assert payload["environment_id"] == "r-bio-full"


def test_docker_hub_timeout_records_blocked_by_registry_access(tmp_path: Path) -> None:
    evidence_root = tmp_path / "r-bio-full"
    evidence_root.mkdir(parents=True)
    (evidence_root / "docker_build.log").write_text(
        'failed to resolve reference "docker.io/rocker/r-ver:4.4.2": '
        'Head "https://registry-1.docker.io/v2/rocker/r-ver/manifests/4.4.2": i/o timeout\n',
        encoding="utf-8",
    )
    (evidence_root / "registry_preflight.log").write_text(
        "Registry preflight: HEAD https://registry-1.docker.io/v2/\nerror=TimeoutError: timed out\n",
        encoding="utf-8",
    )

    payload = run_validator(evidence_root, tmp_path)

    assert payload["status"] == "blocked_by_registry_access"
    assert payload["registry_preflight_status"] == "failed"
    assert payload["docker_build_status"] == "blocked_by_registry_access"
    assert "blocked_by_registry_access" in payload["blockers"]


def test_render_r_bio_full_evidence_report_includes_docker_build_diagnostic(tmp_path: Path) -> None:
    evidence_root = tmp_path / "r-bio-full"
    evidence_root.mkdir(parents=True)
    (evidence_root / "docker_build.log").write_text(
        "\n".join(
            [
                "Step 1/7 : FROM rocker/r-ver:4.4.2",
                'failed to resolve reference "docker.io/rocker/r-ver:4.4.2"',
                'Head "https://registry-1.docker.io/v2/rocker/r-ver/manifests/4.4.2": i/o timeout',
            ]
        ),
        encoding="utf-8",
    )
    (evidence_root / "registry_preflight.log").write_text(
        "Registry preflight: HEAD https://registry-1.docker.io/v2/\n"
        "curl: (28) Failed to connect to registry-1.docker.io port 443 after 15001 ms: Timeout was reached\n",
        encoding="utf-8",
    )
    output = tmp_path / "report.md"

    completed = subprocess.run(
        [
            sys.executable,
            str(RENDER_SCRIPT),
            "--evidence-root",
            str(evidence_root),
            "--output",
            str(output),
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    report = output.read_text(encoding="utf-8")
    assert completed.returncode == 0
    assert "validation_status: `blocked_by_registry_access`" in report
    assert "## Docker Hub Diagnostic" in report
    assert "## Internal Registry Diagnostic" in report
    assert "## Local Image Tar Diagnostic" in report
    assert "## Registry Preflight Diagnostic" in report
    assert "## Docker Build Diagnostic" in report
    assert "registry-1.docker.io" in report
    assert "full gate next stage allowed: `False`" in report


def test_r_bio_full_real_evidence_passes_only_with_required_files(tmp_path: Path) -> None:
    evidence_root = write_valid_evidence_root(tmp_path)

    payload = run_validator(evidence_root, tmp_path)

    assert payload["status"] == "passed"
    assert payload["missing_files"] == []
    assert payload["hash_validation_status"] == "passed"
    assert payload["full_gate_next_stage_allowed"] is True


def test_r_bio_full_rejects_placeholder_digest(tmp_path: Path) -> None:
    evidence_root = write_valid_evidence_root(tmp_path)
    (evidence_root / "docker_image_digest.txt").write_text("pending_validation\n", encoding="utf-8")
    evidence_path = evidence_root / "environment_lock_evidence.json"
    evidence = read_json(evidence_path)
    evidence["docker_image_digest"] = "pending_validation"
    evidence_path.write_text(json.dumps(evidence, indent=2), encoding="utf-8")

    payload = run_validator(evidence_root, tmp_path)

    assert payload["status"] == "invalid"
    assert "docker_image_digest_placeholder" in payload["invalid_blockers"]
    assert "environment_lock_evidence_docker_image_digest_placeholder" in payload["invalid_blockers"]


def test_internal_registry_missing_source_attestation_cannot_pass(tmp_path: Path) -> None:
    evidence_root = write_valid_evidence_root(tmp_path, evidence_source="internal_registry")
    evidence_path = evidence_root / "environment_lock_evidence.json"
    evidence = read_json(evidence_path)
    evidence["source_attestation_path"] = ""
    evidence_path.write_text(json.dumps(evidence, indent=2), encoding="utf-8")

    payload = run_validator(evidence_root, tmp_path)

    assert payload["status"] == "partial"
    assert "source_attestation_missing" in payload["partial_blockers"]


def test_internal_registry_placeholder_digest_cannot_pass(tmp_path: Path) -> None:
    evidence_root = write_valid_evidence_root(tmp_path, evidence_source="internal_registry")
    evidence_path = evidence_root / "environment_lock_evidence.json"
    evidence = read_json(evidence_path)
    evidence["source_digest"] = "pending_validation"
    evidence_path.write_text(json.dumps(evidence, indent=2), encoding="utf-8")

    payload = run_validator(evidence_root, tmp_path)

    assert payload["status"] == "invalid"
    assert "environment_lock_evidence_source_digest_placeholder" in payload["invalid_blockers"]


def test_local_image_tar_missing_tar_hash_cannot_pass(tmp_path: Path) -> None:
    evidence_root = write_valid_evidence_root(tmp_path, evidence_source="local_image_tar")
    evidence_path = evidence_root / "environment_lock_evidence.json"
    evidence = read_json(evidence_path)
    evidence["image_tar_hash"] = ""
    evidence_path.write_text(json.dumps(evidence, indent=2), encoding="utf-8")

    payload = run_validator(evidence_root, tmp_path)

    assert payload["status"] == "partial"
    assert "image_tar_hash_missing" in payload["partial_blockers"]


def test_local_image_tar_missing_source_attestation_cannot_pass(tmp_path: Path) -> None:
    evidence_root = write_valid_evidence_root(tmp_path, evidence_source="local_image_tar")
    evidence_path = evidence_root / "environment_lock_evidence.json"
    evidence = read_json(evidence_path)
    evidence["source_attestation_path"] = ""
    evidence_path.write_text(json.dumps(evidence, indent=2), encoding="utf-8")

    payload = run_validator(evidence_root, tmp_path)

    assert payload["status"] == "partial"
    assert "source_attestation_missing" in payload["partial_blockers"]


def test_source_digest_mismatch_with_docker_inspect_is_invalid(tmp_path: Path) -> None:
    evidence_root = write_valid_evidence_root(tmp_path, evidence_source="internal_registry")
    evidence_path = evidence_root / "environment_lock_evidence.json"
    evidence = read_json(evidence_path)
    evidence["source_digest"] = "sha256:" + "b" * 64
    evidence_path.write_text(json.dumps(evidence, indent=2), encoding="utf-8")

    payload = run_validator(evidence_root, tmp_path)

    assert payload["status"] == "invalid"
    assert "environment_lock_evidence_source_digest_mismatch" in payload["invalid_blockers"]


def test_r_bio_full_rejects_placeholder_hash(tmp_path: Path) -> None:
    evidence_root = write_valid_evidence_root(tmp_path)
    evidence_path = evidence_root / "environment_lock_evidence.json"
    evidence = read_json(evidence_path)
    evidence["evidence_hash"] = "pending_validation"
    evidence_path.write_text(json.dumps(evidence, indent=2), encoding="utf-8")

    payload = run_validator(evidence_root, tmp_path)

    assert payload["status"] == "invalid"
    assert "environment_lock_evidence_hash_placeholder" in payload["invalid_blockers"]


def test_r_bio_full_rejects_missing_renv_restore_log(tmp_path: Path) -> None:
    evidence_root = write_valid_evidence_root(tmp_path)
    (evidence_root / "renv_restore.log").unlink()

    payload = run_validator(evidence_root, tmp_path)

    assert payload["status"] == "partial"
    assert "renv_restore.log" in payload["missing_files"]


def test_r_bio_full_rejects_missing_renv_bootstrap_version(tmp_path: Path) -> None:
    evidence_root = write_valid_evidence_root(tmp_path)
    (evidence_root / "renv_bootstrap_version.txt").unlink()

    payload = run_validator(evidence_root, tmp_path)

    assert payload["status"] == "partial"
    assert "renv_bootstrap_version.txt" in payload["missing_files"]


def test_r_bio_full_rejects_renv_restore_failure_log(tmp_path: Path) -> None:
    evidence_root = write_valid_evidence_root(tmp_path)
    (evidence_root / "renv_restore.log").write_text(
        "Error in loadNamespace(x) : there is no package called 'renv'\nExecution halted\n",
        encoding="utf-8",
    )
    evidence_path = evidence_root / "environment_lock_evidence.json"
    evidence = read_json(evidence_path)
    evidence["evidence_hash"] = VALIDATOR_MODULE.compute_evidence_hash(evidence_root)
    evidence_path.write_text(json.dumps(evidence, indent=2), encoding="utf-8")

    payload = run_validator(evidence_root, tmp_path)

    assert payload["status"] == "partial"
    assert "renv_restore_log_contains_failure" in payload["partial_blockers"]


def test_r_bio_full_rejects_missing_survival_minimal_installed_package(tmp_path: Path) -> None:
    evidence_root = write_valid_evidence_root(tmp_path)
    (evidence_root / "installed_packages.tsv").write_text(
        "Package\tVersion\tLibPath\nsurvival\t3.7-0\t/usr/local/lib/R/site-library\n",
        encoding="utf-8",
    )
    evidence_path = evidence_root / "environment_lock_evidence.json"
    evidence = read_json(evidence_path)
    evidence["evidence_hash"] = VALIDATOR_MODULE.compute_evidence_hash(evidence_root)
    evidence_path.write_text(json.dumps(evidence, indent=2), encoding="utf-8")

    payload = run_validator(evidence_root, tmp_path)

    assert payload["status"] == "partial"
    assert any(
        str(blocker).startswith("installed_packages_missing_required_packages:")
        for blocker in payload["partial_blockers"]  # type: ignore[index]
    )


def test_r_bio_full_rejects_missing_required_package_set_field(tmp_path: Path) -> None:
    evidence_root = write_valid_evidence_root(tmp_path)
    evidence_path = evidence_root / "environment_lock_evidence.json"
    evidence = read_json(evidence_path)
    evidence["required_package_set"] = ["survival"]
    evidence_path.write_text(json.dumps(evidence, indent=2), encoding="utf-8")

    payload = run_validator(evidence_root, tmp_path)

    assert payload["status"] == "partial"
    assert "environment_lock_evidence_required_package_set_invalid" in payload["partial_blockers"]


def test_r_bio_full_rejects_missing_docker_inspect(tmp_path: Path) -> None:
    evidence_root = write_valid_evidence_root(tmp_path)
    (evidence_root / "docker_inspect.json").unlink()

    payload = run_validator(evidence_root, tmp_path)

    assert payload["status"] == "partial"
    assert "docker_inspect.json" in payload["missing_files"]


def test_r_bio_full_rejects_missing_package_inventory(tmp_path: Path) -> None:
    evidence_root = write_valid_evidence_root(tmp_path)
    (evidence_root / "installed_packages.tsv").unlink()

    payload = run_validator(evidence_root, tmp_path)

    assert payload["status"] == "partial"
    assert "installed_packages.tsv" in payload["missing_files"]


def test_validate_r_bio_full_evidence_missing_docker_digest_is_partial(tmp_path: Path) -> None:
    evidence_root = write_valid_evidence_root(tmp_path)
    (evidence_root / "docker_image_digest.txt").unlink()

    payload = run_validator(evidence_root, tmp_path)

    assert payload["status"] == "partial"
    assert "docker_image_digest.txt" in payload["missing_files"]


def test_validate_r_bio_full_evidence_missing_renv_lock_hash_is_partial(tmp_path: Path) -> None:
    evidence_root = write_valid_evidence_root(tmp_path)
    evidence_path = evidence_root / "environment_lock_evidence.json"
    evidence = read_json(evidence_path)
    evidence.pop("renv_lock_hash")
    evidence_path.write_text(json.dumps(evidence, indent=2), encoding="utf-8")

    payload = run_validator(evidence_root, tmp_path)

    assert payload["status"] == "partial"
    assert "environment_lock_evidence_field_missing:renv_lock_hash" in payload["partial_blockers"]


def test_validate_r_bio_full_evidence_missing_r_session_info_is_partial(tmp_path: Path) -> None:
    evidence_root = write_valid_evidence_root(tmp_path)
    (evidence_root / "r_session_info.txt").unlink()

    payload = run_validator(evidence_root, tmp_path)

    assert payload["status"] == "partial"
    assert "r_session_info.txt" in payload["missing_files"]


def test_validate_r_bio_full_evidence_missing_installed_packages_is_partial(tmp_path: Path) -> None:
    evidence_root = write_valid_evidence_root(tmp_path)
    (evidence_root / "installed_packages.tsv").unlink()

    payload = run_validator(evidence_root, tmp_path)

    assert payload["status"] == "partial"
    assert "installed_packages.tsv" in payload["missing_files"]


def test_environment_lock_evidence_incomplete_cannot_pass(tmp_path: Path) -> None:
    evidence_root = write_valid_evidence_root(tmp_path)
    evidence_path = evidence_root / "environment_lock_evidence.json"
    evidence = read_json(evidence_path)
    evidence.pop("docker_image_digest")
    evidence.pop("docker_inspect_path")
    evidence_path.write_text(json.dumps(evidence, indent=2), encoding="utf-8")

    payload = run_validator(evidence_root, tmp_path)

    assert payload["status"] == "partial"
    assert "environment_lock_evidence_field_missing:docker_image_digest" in payload["partial_blockers"]
    assert "environment_lock_evidence_field_missing:docker_inspect_path" in payload["partial_blockers"]


def test_architecture_gate_default_passes_without_full_activation_ready(tmp_path: Path) -> None:
    output = tmp_path / "gate.json"
    completed = subprocess.run(
        [sys.executable, str(GATE_SCRIPT), "--json-output", str(output), "--pretty"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    payload = read_json(output)

    assert completed.returncode == 0
    assert payload["status"] == "passed"
    assert payload["architecture_status"] == "partial_with_p1_gaps"
    assert payload["r_bio_full_environment_evidence"]["status"] in {"missing", "partial", "blocked_by_registry_access", "passed"}
    assert payload["full_analysis_activation_gate"]["status"] == "blocked"


def test_default_gate_passes_after_r_bio_full_evidence_restore(tmp_path: Path) -> None:
    output = tmp_path / "gate.json"
    completed = subprocess.run(
        [sys.executable, str(GATE_SCRIPT), "--json-output", str(output), "--pretty"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    payload = read_json(output)

    assert completed.returncode == 0
    assert payload["status"] == "passed"
    assert payload["architecture_status"] == "partial_with_p1_gaps"


def test_architecture_gate_require_full_ready_blocks_with_missing_r_bio_full_evidence(tmp_path: Path) -> None:
    output = tmp_path / "gate-full.json"
    completed = subprocess.run(
        [sys.executable, str(GATE_SCRIPT), "--json-output", str(output), "--require-full-ready", "--pretty"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    payload = read_json(output)

    assert completed.returncode == 1
    assert "full_analysis_activation_gate_not_ready" in payload["blockers"]
    assert payload["full_analysis_activation_gate"]["status"] == "blocked"


def test_r_bio_full_passed_does_not_unblock_require_full_ready(tmp_path: Path) -> None:
    evidence_root = write_valid_evidence_root(tmp_path)
    payload = run_validator(evidence_root, tmp_path)
    assert payload["status"] == "passed"

    output = tmp_path / "gate-full.json"
    completed = subprocess.run(
        [sys.executable, str(GATE_SCRIPT), "--json-output", str(output), "--require-full-ready", "--pretty"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    gate_payload = read_json(output)

    assert completed.returncode == 1
    assert gate_payload["full_analysis_activation_gate"]["status"] == "blocked"
    assert "full_analysis_activation_gate_not_ready" in gate_payload["blockers"]


def test_require_full_ready_still_blocks_without_resource_and_migration_evidence(tmp_path: Path) -> None:
    output = tmp_path / "gate-full.json"
    completed = subprocess.run(
        [sys.executable, str(GATE_SCRIPT), "--json-output", str(output), "--require-full-ready", "--pretty"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    payload = read_json(output)

    assert completed.returncode == 1
    assert payload["resource_artifact_matrix"]["status"] in {"partial", "blocked"}
    assert payload["standard_worker_migration_matrix"]["status"] in {"partial", "blocked"}


def test_app_dev_dependencies_do_not_gain_full_analysis_packages() -> None:
    app_lock = (ROOT / "renv" / "renv.app.lock").read_text(encoding="utf-8")
    app_dockerfile = (ROOT / "docker" / "Dockerfile.app-dev").read_text(encoding="utf-8")
    combined = f"{app_lock}\n{app_dockerfile}"

    for forbidden in ("ReactomePA", "reactome.db", "Seurat", "CellChat", "AutoDock Vina", "GROMACS"):
        assert forbidden not in combined


def test_no_runtime_install_or_download_patterns_added() -> None:
    scan_roots = [ROOT / "app", ROOT / "analysis", ROOT / "scripts", ROOT / "config"]
    forbidden = ("install.packages", "BiocManager::install", "pak::pkg_install", "remotes::install_github")
    hits: list[str] = []
    for root in scan_roots:
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix not in {".py", ".R", ".sh", ".json", ".yml", ".yaml", ".md"}:
                continue
            if path.relative_to(ROOT).parts[:2] == ("scripts", "full_env"):
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            hits.extend(f"{path.relative_to(ROOT)}:{item}" for item in forbidden if item in text)

    assert hits == []


def test_survival_scoped_migration_evidence_does_not_unblock_global_full_ready(tmp_path: Path) -> None:
    output = tmp_path / "gate.json"
    subprocess.run(
        [sys.executable, str(GATE_SCRIPT), "--json-output", str(output), "--pretty"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    payload = read_json(output)
    migration_rows = {row["module_id"]: row for row in payload["standard_worker_migration_rows"]}

    assert payload["full_analysis_activation_gate"]["status"] == "blocked"
    assert migration_rows["survival"]["formal_worker_status"] == "migrated_to_isolated_standard_worker"
    assert migration_rows["survival"]["migration_evidence_status"] == "passed"
    assert migration_rows["survival"]["migration_next_action"] == "no_action_migration_evidence_passed"
    assert payload["standard_worker_migration_matrix"]["formal_pending_count"] == 9


def test_r_bio_full_passed_does_not_unblock_global_full_ready(tmp_path: Path) -> None:
    evidence_root = write_valid_evidence_root(tmp_path)
    validation_payload = run_validator(evidence_root, tmp_path)
    assert validation_payload["status"] == "passed"

    output = tmp_path / "gate.json"
    subprocess.run(
        [sys.executable, str(GATE_SCRIPT), "--json-output", str(output), "--pretty"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    payload = read_json(output)
    migration_rows = {row["module_id"]: row for row in payload["standard_worker_migration_rows"]}

    assert payload["full_analysis_activation_gate"]["status"] == "blocked"
    assert migration_rows["survival"]["formal_worker_status"] == "migrated_to_isolated_standard_worker"
    assert migration_rows["survival"]["migration_evidence_status"] == "passed"
    assert payload["full_activation_module_matrix"]["eligible_module_count"] == 1
    assert payload["full_activation_module_matrix"]["blocked_module_count"] == 9


def run_validator(evidence_root: Path, tmp_path: Path) -> dict[str, object]:
    output = tmp_path / "validation.json"
    subprocess.run(
        [sys.executable, str(VALIDATE_SCRIPT), "--evidence-root", str(evidence_root), "--json-output", str(output)],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    return read_json(output)


def write_valid_evidence_root(tmp_path: Path, *, evidence_source: str = "docker_hub") -> Path:
    evidence_root = tmp_path / "r-bio-full"
    evidence_root.mkdir(parents=True)
    renv_hash = sha256_file(ROOT / "renv" / "renv.bio-full.lock")
    lock_payload = read_json(ROOT / "renv" / "renv.bio-full.lock")
    renv_package_count = len(lock_payload.get("Packages", {})) if isinstance(lock_payload.get("Packages"), dict) else 1
    docker_digest = "sha256:" + "a" * 64
    attestation = tmp_path / "source_attestation.md"
    attestation.write_text(
        "This source image is equivalent to rocker/r-ver:4.4.2 for r-bio-full evidence testing.\n",
        encoding="utf-8",
    )
    image_tar = tmp_path / "r-bio-full.tar"
    image_tar.write_text("fake image tar bytes for hash validation\n", encoding="utf-8")
    image_tar_hash = "sha256:" + sha256_file(image_tar)
    files = {
        "docker_build.log": "docker build completed\n",
        "docker_image_digest.txt": docker_digest + "\n",
        "docker_inspect.json": json.dumps([{"Id": docker_digest}]),
        "renv_lock_generate.log": "generated_package_count=8\n",
        "renv_lock_generate_metadata.json": json.dumps(
            {
                "schema_version": "biomedpilot.analysis.r_bio_full_lock_generate_metadata.v1",
                "environment_id": "r-bio-full",
                "lock_profile": "survival_minimal_v1",
                "lock_profile_version": "v1",
                "image_tag": "biomedpilot/r-bio-full:local-test",
                "docker_image_digest": docker_digest,
                "cran_repo": "https://cloud.r-project.org",
                "required_package_set": SURVIVAL_MINIMAL_PACKAGES,
                "renv_lock_path": "renv/renv.bio-full.lock",
                "renv_lock_hash": "sha256:" + renv_hash,
                "renv_lock_package_count": renv_package_count,
                "generated_at": "2026-06-12T00:00:00Z",
                "generated_by": "test",
                "command": "docker run r-bio-full generate lock",
            }
        ),
        "renv_bootstrap_version.txt": "1.0.11\n",
        "renv_bootstrap_source.txt": "https://cloud.r-project.org\n",
        "renv_restore.log": "renv restore completed\n",
        "renv_status.json": "{}\n",
        "r_session_info.txt": "R version 4.4.2\n",
        "installed_packages.tsv": "Package\tVersion\tLibPath\n"
        + "\n".join(
            f"{package}\t1.0.0\t/usr/local/lib/R/site-library"
            for package in SURVIVAL_MINIMAL_PACKAGES
        )
        + "\n",
        "evidence_manifest.json": json.dumps(
            {
                "schema_version": "biomedpilot.analysis.r_bio_full_evidence_manifest.v1",
                "environment_id": "r-bio-full",
                "evidence_source": evidence_source,
                "base_image": "rocker/r-ver:4.4.2",
                "source_digest": docker_digest,
                "source_attestation_path": str(attestation),
                "image_tar_path": str(image_tar) if evidence_source == "local_image_tar" else "",
                "image_tar_hash": image_tar_hash if evidence_source == "local_image_tar" else "",
                "required_files": [
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
                ],
            }
        ),
    }
    for name, content in files.items():
        (evidence_root / name).write_text(content, encoding="utf-8")
    evidence = {
        "schema_version": "biomedpilot.analysis.environment_lock_evidence.v1",
        "environment_id": "r-bio-full",
        "environment_class": "full",
        "status": "restored",
        "evidence_source": evidence_source,
        "base_image": "rocker/r-ver:4.4.2" if evidence_source == "docker_hub" else "internal.example/r-bio-full:4.4.2",
        "base_image_expected": "rocker/r-ver:4.4.2",
        "source_registry": "https://internal.example/r-bio-full" if evidence_source == "internal_registry" else "",
        "source_digest": docker_digest,
        "source_attestation_path": str(attestation) if evidence_source != "docker_hub" else "",
        "image_tar_path": str(image_tar) if evidence_source == "local_image_tar" else "",
        "image_tar_hash": image_tar_hash if evidence_source == "local_image_tar" else "",
        "registry_preflight_status": "passed",
        "registry_preflight_error": "",
        "docker_build_status": "built" if evidence_source == "docker_hub" else "not_required",
        "docker_load_status": "loaded" if evidence_source == "local_image_tar" else "",
        "equivalence_claim": "equivalent to rocker/r-ver:4.4.2",
        "equivalence_validation_status": "passed",
        "r_version": "R 4.4.2",
        "bioconductor_version": "3.20",
        "package_lock_hash": {"algorithm": "sha256", "value": renv_hash},
        "renv_lock_content": {"policy_status": "restored", "packages_non_empty": True, "package_count": renv_package_count},
        "docker_image": {
            "image_ref": "biomedpilot/r-bio-full:local-test",
            "digest": {"algorithm": "sha256", "value": "a" * 64},
            "architecture": "linux/arm64",
            "build_status": "built",
            "build_log": str(evidence_root / "docker_build.log"),
        },
        "docker_image_digest": docker_digest,
        "docker_build_log_path": str(evidence_root / "docker_build.log"),
        "docker_inspect_path": str(evidence_root / "docker_inspect.json"),
        "dockerfile": "docker/Dockerfile.r-bio-full",
        "dockerfile_path": "docker/Dockerfile.r-bio-full",
        "renv_lock": "renv/renv.bio-full.lock",
        "renv_lock_path": "renv/renv.bio-full.lock",
        "renv_lock_hash": "sha256:" + renv_hash,
        "lock_profile": "survival_minimal_v1",
        "lock_profile_version": "v1",
        "renv_lock_package_count": renv_package_count,
        "required_package_set": SURVIVAL_MINIMAL_PACKAGES,
        "missing_required_packages": [],
        "renv_lock_generate_log_path": str(evidence_root / "renv_lock_generate.log"),
        "renv_lock_generate_metadata_path": str(evidence_root / "renv_lock_generate_metadata.json"),
        "renv_bootstrap_status": "available",
        "renv_bootstrap_version": "1.0.11",
        "renv_bootstrap_source": "https://cloud.r-project.org",
        "renv_bootstrap_version_path": str(evidence_root / "renv_bootstrap_version.txt"),
        "renv_bootstrap_source_path": str(evidence_root / "renv_bootstrap_source.txt"),
        "renv_restore_status": "restored",
        "renv_restore_log_path": str(evidence_root / "renv_restore.log"),
        "renv_status_path": str(evidence_root / "renv_status.json"),
        "r_session_info_path": str(evidence_root / "r_session_info.txt"),
        "runtime_package_install": "forbidden",
        "runtime_resource_download": "forbidden",
        "allowed_module_ids": ["deg", "survival", "univariate", "multivariate", "enrichment", "immune_infiltration", "correlation"],
        "evidence_files": [str(evidence_root / name) for name in files],
        "package_inventory_path": str(evidence_root / "installed_packages.tsv"),
        "created_at": "2026-06-12T00:00:00Z",
        "created_by": "test",
        "validation_status": "passed",
        "validation_errors": [],
        "evidence_hash": VALIDATOR_MODULE.compute_evidence_hash(evidence_root),
    }
    (evidence_root / "environment_lock_evidence.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    return evidence_root


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
