from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from validate_r_bio_full_evidence import DEFAULT_EVIDENCE_ROOT, validate_evidence_root


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = REPO_ROOT / "docs" / "R_BIO_FULL_ENVIRONMENT_EVIDENCE.md"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render r-bio-full evidence validation as Markdown.")
    parser.add_argument("--evidence-root", default=str(DEFAULT_EVIDENCE_ROOT))
    parser.add_argument("--validation-json", default="")
    parser.add_argument("--markdown-output", "--output", dest="markdown_output", default=str(DEFAULT_OUTPUT))
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.validation_json:
        payload = json.loads(Path(args.validation_json).read_text(encoding="utf-8"))
    else:
        payload = validate_evidence_root(Path(args.evidence_root))
    output = Path(args.markdown_output).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_markdown(payload), encoding="utf-8")
    print(str(output))
    return 0


def render_markdown(payload: dict[str, Any]) -> str:
    rows = payload.get("required_files") if isinstance(payload.get("required_files"), list) else []
    lines = [
        "# r-bio-full Environment Evidence",
        "",
        f"- environment_id: `{payload.get('environment_id', 'r-bio-full')}`",
        f"- validation_status: `{payload.get('validation_status') or payload.get('status') or 'missing'}`",
        f"- evidence_source: `{payload.get('evidence_source') or 'docker_hub'}`",
        f"- evidence root: `{payload.get('evidence_root') or ''}`",
        f"- full gate next stage allowed: `{payload.get('full_gate_next_stage_allowed') is True}`",
        f"- lock profile: `{payload.get('lock_profile') or ''}`",
        f"- lock profile version: `{payload.get('lock_profile_version') or ''}`",
        f"- renv lock package count: `{payload.get('renv_lock_package_count') if payload.get('renv_lock_package_count') is not None else ''}`",
        "",
    ]
    lines.extend(
        [
            "Current status:",
            "",
        ]
    )
    if payload.get("status") == "passed":
        lines.extend(
            [
                "- r-bio-full environment evidence has passed validation for the scoped `survival_minimal_v1` lock profile.",
                "- Survival has scoped `survival_minimal_v1` full/formal standard-worker migration evidence.",
                "- This is not global full production activation.",
                "- full activation remains blocked until resource/tool locks and the remaining formal module migrations also pass.",
                "",
            ]
        )
    else:
        lines.extend(
            [
                "- r-bio-full is not restored.",
                "- r-bio-full is not ready.",
                "- full activation remains blocked.",
                "- survival full/formal migration cannot be treated as globally full-ready without validated environment evidence.",
                "",
            ]
        )
    lines.extend(_evidence_source_lines(payload))
    lines.extend(
        [
            "## Required Files",
            "",
            "| File | Status | Path |",
            "| --- | --- | --- |",
        ]
    )
    for row in rows:
        if isinstance(row, dict):
            lines.append(f"| `{row.get('file')}` | `{row.get('status')}` | `{row.get('path')}` |")
    lines.extend(
        [
            "",
            "## Evidence Status",
            "",
            f"- Docker evidence status: `{payload.get('docker_evidence_status')}`",
            f"- renv bootstrap status: `{payload.get('renv_bootstrap_status')}`",
            f"- renv bootstrap version: `{payload.get('renv_bootstrap_version')}`",
            f"- renv bootstrap source: `{payload.get('renv_bootstrap_source')}`",
            f"- renv evidence status: `{payload.get('renv_evidence_status')}`",
            f"- renv restore status: `{payload.get('renv_restore_status')}`",
            f"- lock profile: `{payload.get('lock_profile') or ''}`",
            f"- lock profile version: `{payload.get('lock_profile_version') or ''}`",
            f"- renv lock package count: `{payload.get('renv_lock_package_count') if payload.get('renv_lock_package_count') is not None else ''}`",
            f"- missing required packages: `{', '.join(payload.get('missing_required_packages') or [])}`",
            f"- R session info status: `{payload.get('r_session_info_status')}`",
            f"- package inventory status: `{payload.get('package_inventory_status')}`",
            f"- hash validation status: `{payload.get('hash_validation_status')}`",
            f"- registry preflight status: `{payload.get('registry_preflight_status')}`",
            f"- Docker build status: `{payload.get('docker_build_status')}`",
            f"- Docker load status: `{payload.get('docker_load_status')}`",
            "",
            "## Blockers",
            "",
        ]
    )
    blockers = payload.get("blockers") if isinstance(payload.get("blockers"), list) else []
    if blockers:
        lines.extend(f"- `{blocker}`" for blocker in blockers)
    else:
        lines.append("- none")
    lines.extend(_source_mode_diagnostic_lines(payload))
    lines.extend(_source_attestation_lines(payload))
    lines.extend(_digest_hash_lines(payload))
    lines.extend(_lock_profile_lines(payload))
    lines.extend(_component_diagnostic_lines(payload))
    preflight_lines = _docker_preflight_lines(payload)
    if preflight_lines:
        lines.extend(preflight_lines)
    registry_lines = _registry_preflight_lines(payload)
    if registry_lines:
        lines.extend(registry_lines)
    build_lines = _docker_build_lines(payload)
    if build_lines:
        lines.extend(build_lines)
    lines.extend(
        [
            "",
            "## Policy",
            "",
            "This report is evidence review only. It does not build Docker images, restore renv, install R packages, download resources, or activate full analysis.",
            "",
            "Next acceptable evidence sources:",
            "",
            "1. Restore the full `renv/renv.bio-full.lock` with real package entries in the isolated r-bio-full environment.",
            "2. Keep Docker Hub evidence, internal registry evidence, or local image tar evidence source-backed with digest/hash and attestation where required.",
            "3. Keep full activation blocked until environment evidence, resource evidence, and formal migration evidence all pass.",
            "",
        ]
    )
    return "\n".join(lines)


def _evidence_source_lines(payload: dict[str, Any]) -> list[str]:
    return [
        "## Evidence Source",
        "",
        "| Field | Value |",
        "| --- | --- |",
        f"| evidence_source | `{payload.get('evidence_source') or 'docker_hub'}` |",
        f"| base_image | `{payload.get('base_image') or ''}` |",
        f"| base_image_expected | `{payload.get('base_image_expected') or 'rocker/r-ver:4.4.2'}` |",
        f"| source_registry | `{payload.get('source_registry') or ''}` |",
        f"| source_digest | `{payload.get('source_digest') or ''}` |",
        f"| image_tar_path | `{payload.get('image_tar_path') or ''}` |",
        f"| image_tar_hash | `{payload.get('image_tar_hash') or ''}` |",
        "",
    ]


def _source_mode_diagnostic_lines(payload: dict[str, Any]) -> list[str]:
    return [
        "",
        "## Docker Hub Diagnostic",
        "",
        f"- registry_preflight_status: `{payload.get('registry_preflight_status') or ''}`",
        f"- registry_preflight_error: `{payload.get('registry_preflight_error') or ''}`",
        f"- docker_build_status: `{payload.get('docker_build_status') or ''}`",
        "",
        "## Internal Registry Diagnostic",
        "",
        f"- source_registry: `{payload.get('source_registry') or ''}`",
        f"- source_digest: `{payload.get('source_digest') or ''}`",
        f"- source_attestation_path: `{payload.get('source_attestation_path') or ''}`",
        "",
        "## Local Image Tar Diagnostic",
        "",
        f"- image_tar_path: `{payload.get('image_tar_path') or ''}`",
        f"- image_tar_hash: `{payload.get('image_tar_hash') or ''}`",
        f"- docker_load_status: `{payload.get('docker_load_status') or ''}`",
    ]


def _source_attestation_lines(payload: dict[str, Any]) -> list[str]:
    return [
        "",
        "## Source Attestation",
        "",
        f"- source_attestation_path: `{payload.get('source_attestation_path') or ''}`",
        f"- equivalence_claim: `{payload.get('equivalence_claim') or ''}`",
        f"- equivalence_validation_status: `{payload.get('equivalence_validation_status') or ''}`",
    ]


def _digest_hash_lines(payload: dict[str, Any]) -> list[str]:
    return [
        "",
        "## Digest / Hash Validation",
        "",
        f"- docker_image_digest: `{payload.get('docker_image_digest') or ''}`",
        f"- source_digest: `{payload.get('source_digest') or ''}`",
        f"- image_tar_hash: `{payload.get('image_tar_hash') or ''}`",
        f"- hash_validation_status: `{payload.get('hash_validation_status') or ''}`",
    ]


def _lock_profile_lines(payload: dict[str, Any]) -> list[str]:
    required_packages = payload.get("required_package_set")
    if not isinstance(required_packages, list):
        required_packages = []
    missing_packages = payload.get("missing_required_packages")
    if not isinstance(missing_packages, list):
        missing_packages = []
    return [
        "",
        "## Lock Profile",
        "",
        f"- lock_profile: `{payload.get('lock_profile') or ''}`",
        f"- lock_profile_version: `{payload.get('lock_profile_version') or ''}`",
        f"- renv_lock_package_count: `{payload.get('renv_lock_package_count') if payload.get('renv_lock_package_count') is not None else ''}`",
        f"- required_package_set: `{', '.join(str(item) for item in required_packages)}`",
        f"- missing_required_packages: `{', '.join(str(item) for item in missing_packages)}`",
    ]


def _component_diagnostic_lines(payload: dict[str, Any]) -> list[str]:
    return [
        "",
        "## Docker Load / Docker Inspect",
        "",
        f"- Docker evidence status: `{payload.get('docker_evidence_status') or ''}`",
        f"- Docker build status: `{payload.get('docker_build_status') or ''}`",
        f"- Docker load status: `{payload.get('docker_load_status') or ''}`",
        "",
        "## renv Restore",
        "",
        f"- renv bootstrap status: `{payload.get('renv_bootstrap_status') or ''}`",
        f"- renv bootstrap version: `{payload.get('renv_bootstrap_version') or ''}`",
        f"- renv bootstrap source: `{payload.get('renv_bootstrap_source') or ''}`",
        f"- renv restore status: `{payload.get('renv_restore_status') or ''}`",
        f"- renv evidence status: `{payload.get('renv_evidence_status') or ''}`",
        "",
        "## R Session Info",
        "",
        f"- R session info status: `{payload.get('r_session_info_status') or ''}`",
        "",
        "## Package Inventory",
        "",
        f"- package inventory status: `{payload.get('package_inventory_status') or ''}`",
    ]


def _docker_preflight_lines(payload: dict[str, Any]) -> list[str]:
    evidence_root = payload.get("evidence_root")
    if not isinstance(evidence_root, str) or not evidence_root:
        return []
    preflight_path = Path(evidence_root) / "docker_preflight.log"
    if not preflight_path.is_file():
        return []
    text = preflight_path.read_text(encoding="utf-8", errors="replace").strip()
    if not text:
        return []
    excerpt = "\n".join(text.splitlines()[:40])
    return [
        "",
        "## Docker Preflight Diagnostic",
        "",
        f"- path: `{preflight_path}`",
        "",
        "```text",
        excerpt,
        "```",
    ]


def _docker_build_lines(payload: dict[str, Any]) -> list[str]:
    evidence_root = payload.get("evidence_root")
    if not isinstance(evidence_root, str) or not evidence_root:
        return []
    build_path = Path(evidence_root) / "docker_build.log"
    if not build_path.is_file():
        return []
    text = build_path.read_text(encoding="utf-8", errors="replace").strip()
    if not text:
        return []
    excerpt_lines = text.splitlines()[-80:]
    return [
        "",
        "## Docker Build Diagnostic",
        "",
        f"- path: `{build_path}`",
        "",
        "```text",
        "\n".join(excerpt_lines),
        "```",
    ]


def _registry_preflight_lines(payload: dict[str, Any]) -> list[str]:
    evidence_root = payload.get("evidence_root")
    if not isinstance(evidence_root, str) or not evidence_root:
        return []
    preflight_path = Path(evidence_root) / "registry_preflight.log"
    if not preflight_path.is_file():
        return []
    text = preflight_path.read_text(encoding="utf-8", errors="replace").strip()
    if not text:
        return []
    excerpt = "\n".join(text.splitlines()[:80])
    return [
        "",
        "## Registry Preflight Diagnostic",
        "",
        f"- path: `{preflight_path}`",
        "",
        "```text",
        excerpt,
        "```",
    ]


if __name__ == "__main__":
    raise SystemExit(main())
