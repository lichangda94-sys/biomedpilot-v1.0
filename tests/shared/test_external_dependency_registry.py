from __future__ import annotations

import json
import subprocess
from pathlib import Path

from app.shared.local_engines import (
    CAPABILITY_STATUS_AVAILABLE,
    CAPABILITY_STATUS_BLOCKED,
    CAPABILITY_STATUS_MISSING,
    PYTHON_STATISTICAL_ENGINE_FAMILY,
    R_BIOCONDUCTOR_ENGINE_FAMILY,
    dependency_snapshot_handoff,
    detect_all_external_dependencies,
    detect_python_statistical_dependencies,
    detect_r_bioconductor_dependencies,
    detect_report_renderer_dependencies,
    external_engines_storage_root,
    load_external_engine_registry,
)


def test_missing_rscript_returns_missing_snapshot_without_crashing(tmp_path: Path) -> None:
    snapshot = detect_r_bioconductor_dependencies(
        storage_root=tmp_path,
        command_finder=lambda _name: None,
    )
    registry = load_external_engine_registry(tmp_path)

    assert snapshot["status"] == "missing"
    assert snapshot["runtime_path"] == ""
    assert snapshot["blockers"][0]["code"] == "missing_r_runtime"
    assert registry.get_capability("runtime.r.available")["status"] == CAPABILITY_STATUS_MISSING
    assert registry.get_capability("package.r.deseq2.available")["status"] == CAPABILITY_STATUS_BLOCKED
    assert (external_engines_storage_root(tmp_path) / "r_runtime_snapshot.json").exists()
    assert "DESeq2 已完成" not in json.dumps(snapshot, ensure_ascii=False)


def test_r_package_detector_reports_partial_availability_by_backend(tmp_path: Path) -> None:
    snapshot = detect_r_bioconductor_dependencies(
        storage_root=tmp_path,
        command_finder=lambda name: "/usr/local/bin/Rscript" if name == "Rscript" else None,
        runner=_r_runner(installed={"BiocManager": "1.30.23", "limma": "3.60.1", "survival": "3.7-0"}),
    )
    registry = load_external_engine_registry(tmp_path)

    assert snapshot["status"] == "partially_available"
    assert registry.get_capability("runtime.r.available")["status"] == CAPABILITY_STATUS_AVAILABLE
    assert registry.get_capability("package.r.limma.available")["status"] == CAPABILITY_STATUS_AVAILABLE
    assert registry.query_required_by("deg_limma")[0]["capability_key"] == "package.r.limma.available"
    deseq2 = registry.get_capability("package.r.deseq2.available")
    edger = registry.get_capability("package.r.edger.available")
    assert deseq2["status"] == CAPABILITY_STATUS_MISSING
    assert deseq2["blockers"][0]["required_by"] == ["deg_deseq2"]
    assert edger["blockers"][0]["required_by"] == ["deg_edger"]
    assert "多因素 DEG 已完成" not in json.dumps(snapshot, ensure_ascii=False)


def test_python_registry_and_dependency_handoff_are_stable(tmp_path: Path) -> None:
    snapshot = detect_python_statistical_dependencies(
        storage_root=tmp_path,
        module_checker=lambda import_name: import_name in {"scipy", "statsmodels", "matplotlib"},
        distribution_version_reader=lambda name: {"scipy": "1.13.0", "statsmodels": "0.14.2", "matplotlib": "3.9.0"}.get(name),
    )
    registry = load_external_engine_registry(tmp_path)
    handoff = dependency_snapshot_handoff(
        registry,
        engine_family=PYTHON_STATISTICAL_ENGINE_FAMILY,
        required_capabilities=("package.python.scipy.available", "package.python.lifelines.available"),
    )

    assert snapshot["status"] == "partially_available"
    assert registry.get_capability("package.python.matplotlib.available")["status"] == CAPABILITY_STATUS_AVAILABLE
    assert registry.get_capability("package.python.lifelines.available")["status"] == CAPABILITY_STATUS_MISSING
    assert handoff["snapshot_path"].endswith("python_statistical_snapshot.json")
    assert handoff["all_required_available"] is False
    assert Path(handoff["snapshot_path"]).exists()


def test_renderer_detection_blocks_full_exports_but_not_markdown(tmp_path: Path) -> None:
    snapshot = detect_report_renderer_dependencies(
        storage_root=tmp_path,
        command_finder=lambda name: "/usr/local/bin/pandoc" if name == "pandoc" else None,
        runner=_version_runner,
    )
    registry = load_external_engine_registry(tmp_path)

    assert snapshot["export_capabilities"]["markdown"]["status"] == CAPABILITY_STATUS_AVAILABLE
    assert snapshot["export_capabilities"]["docx"]["status"] == CAPABILITY_STATUS_AVAILABLE
    assert snapshot["export_capabilities"]["pdf"]["status"] == CAPABILITY_STATUS_BLOCKED
    assert registry.get_capability("renderer.pandoc.available")["status"] == CAPABILITY_STATUS_AVAILABLE
    assert registry.get_capability("renderer.latex.available")["status"] == CAPABILITY_STATUS_MISSING


def test_detect_all_writes_registry_and_unknown_key_is_safe(tmp_path: Path) -> None:
    registry = detect_all_external_dependencies(
        storage_root=tmp_path,
        command_finder=lambda _name: None,
        module_checker=lambda _import_name: False,
        distribution_version_reader=lambda _name: None,
        runner=_version_runner,
    )
    unknown = registry.get_capability("package.r.not_a_real_key.available")

    assert unknown["status"] == "unknown"
    assert unknown["blockers"][0]["code"] == "unknown_capability_key"
    assert registry.query_engine_family(R_BIOCONDUCTOR_ENGINE_FAMILY)["status"] == "missing"
    assert (external_engines_storage_root(tmp_path) / "capability_registry_snapshot.json").exists()


def _r_runner(*, installed: dict[str, str]):
    def runner(command, **_kwargs):
        script = command[-1]
        if "R.version.string" in script:
            return subprocess.CompletedProcess(command, 0, stdout="R version 4.4.1\narm64\n", stderr="")
        lines = [f"{name}\t{version}" for name, version in installed.items()]
        return subprocess.CompletedProcess(command, 0, stdout="\n".join(lines) + "\n", stderr="")

    return runner


def _version_runner(command, **_kwargs):
    return subprocess.CompletedProcess(command, 0, stdout=f"{Path(command[0]).name} 1.0.0\n", stderr="")
