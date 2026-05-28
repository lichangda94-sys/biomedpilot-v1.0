from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from app.shared.local_engines import (
    CAPABILITY_STATUS_AVAILABLE,
    CAPABILITY_STATUS_BLOCKED,
    CAPABILITY_STATUS_MISSING,
    R_ENRICHMENT_BACKEND_DETECTION_FILENAME,
    R_ENRICHMENT_BACKEND_DETECTION_SCHEMA_VERSION,
    R_ENRICHMENT_GSEA_FIXTURE_FILENAME,
    R_ENRICHMENT_ORA_FIXTURE_FILENAME,
    PYTHON_STATISTICAL_ENGINE_FAMILY,
    R_BIOCONDUCTOR_ENGINE_FAMILY,
    dependency_snapshot_handoff,
    detect_all_external_dependencies,
    detect_external_enrichment_r_backend,
    detect_python_statistical_dependencies,
    detect_r_bioconductor_dependencies,
    detect_report_renderer_dependencies,
    external_engines_storage_root,
    load_external_engine_registry,
    run_external_enrichment_r_backend_validation,
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


def test_external_enrichment_r_backend_missing_rscript_blocks_without_traceback(tmp_path: Path) -> None:
    detection = detect_external_enrichment_r_backend(storage_root=tmp_path, command_finder=lambda _name: None)

    assert detection["schema_version"] == R_ENRICHMENT_BACKEND_DETECTION_SCHEMA_VERSION
    assert detection["status"] == "blocked"
    assert detection["rscript"]["available"] is False
    assert detection["rscript"]["architecture"] == "unknown"
    assert detection["packages"]["clusterProfiler"]["available"] is False
    assert detection["packages"]["ReactomePA"]["importable"] is False
    assert detection["packages"]["msigdbr"]["missing_reason"] == "Rscript is not available"
    assert detection["capabilities"]["ora_enricher"] is False
    assert detection["install_action"] == "none_detect_first_only"
    assert detection["packaging_policy"] == "external_runtime_not_bundled"
    assert (external_engines_storage_root(tmp_path) / R_ENRICHMENT_BACKEND_DETECTION_FILENAME).exists()
    assert "Traceback" not in json.dumps(detection)


def test_external_enrichment_r_backend_reports_package_specific_blockers(tmp_path: Path) -> None:
    detection = detect_external_enrichment_r_backend(
        storage_root=tmp_path,
        command_finder=lambda name: "/usr/local/bin/Rscript" if name == "Rscript" else None,
        runner=_r_enrichment_runner(
            installed={
                "clusterProfiler": "4.14.6",
                "fgsea": "1.32.4",
                "DOSE": "4.0.1",
                "enrichplot": "1.26.6",
                "ggplot2": "3.5.2",
                "AnnotationDbi": "1.68.0",
                "org.Hs.eg.db": "3.20.0",
                "GO.db": "3.20.0",
                "KEGGREST": "1.46.0",
            }
        ),
    )

    assert detection["status"] == "blocked"
    assert detection["rscript"]["version"] == "R version 4.4.2 (2024-10-31)"
    assert detection["rscript"]["architecture"] == "arm64"
    assert detection["rscript"]["library_paths"] == ["/Library/Frameworks/R.framework/Versions/4.4-arm64/Resources/library"]
    assert detection["packages"]["clusterProfiler"]["version"] == "4.14.6"
    assert detection["packages"]["ReactomePA"]["missing_reason"] == "package_not_installed_or_not_on_libpaths:ReactomePA"
    assert detection["packages"]["msigdbr"]["missing_reason"] == "package_not_installed_or_not_on_libpaths:msigdbr"
    assert {blocker["package"] for blocker in detection["blockers"]} == {"ReactomePA", "msigdbr"}
    assert detection["capabilities"]["ora_enricher"] is True
    assert detection["capabilities"]["ora_reactome"] is False
    assert detection["capabilities"]["gsea_preranked_fgsea"] is True
    assert detection["capabilities"]["enrichment_plot_barplot"] is True


def test_external_enrichment_validation_writes_mocked_fixture_outputs(tmp_path: Path) -> None:
    detection = run_external_enrichment_r_backend_validation(
        storage_root=tmp_path,
        command_finder=lambda name: "/usr/local/bin/Rscript" if name == "Rscript" else None,
        runner=_r_enrichment_runner(
            installed={
                "clusterProfiler": "4.14.6",
                "fgsea": "1.32.4",
                "DOSE": "4.0.1",
                "enrichplot": "1.26.6",
                "ggplot2": "3.5.2",
                "AnnotationDbi": "1.68.0",
                "org.Hs.eg.db": "3.20.0",
                "ReactomePA": "1.50.0",
                "msigdbr": "24.1.0",
                "GO.db": "3.20.0",
                "KEGGREST": "1.46.0",
            },
            write_fixtures=True,
        ),
    )
    output_root = external_engines_storage_root(tmp_path)

    assert detection["status"] == "passed"
    assert Path(detection["fixture_outputs"]["ora_fixture_tsv"]).name == R_ENRICHMENT_ORA_FIXTURE_FILENAME
    assert Path(detection["fixture_outputs"]["gsea_fixture_tsv"]).name == R_ENRICHMENT_GSEA_FIXTURE_FILENAME
    assert (output_root / R_ENRICHMENT_BACKEND_DETECTION_FILENAME).exists()
    assert (output_root / R_ENRICHMENT_ORA_FIXTURE_FILENAME).read_text(encoding="utf-8").startswith("ID\tDescription\tGeneRatio")
    assert (output_root / R_ENRICHMENT_GSEA_FIXTURE_FILENAME).read_text(encoding="utf-8").startswith("pathway\tES\tNES")
    assert detection["fixture_validation"]["ora"]["status"] == "passed"
    assert detection["fixture_validation"]["gsea"]["status"] == "passed"
    plot_checks = {row["check"]: row for row in detection["plot_smoke"]}
    assert plot_checks["ora_barplot"]["ok"] is True
    assert plot_checks["gsea_curve"]["class"] == "gglist/list"


def test_external_enrichment_validation_blocks_bad_fixture_columns(tmp_path: Path) -> None:
    detection = run_external_enrichment_r_backend_validation(
        storage_root=tmp_path,
        command_finder=lambda name: "/usr/local/bin/Rscript" if name == "Rscript" else None,
        runner=_r_enrichment_runner(
            installed={name: "1.0.0" for name in ("clusterProfiler", "fgsea", "DOSE", "enrichplot", "ggplot2", "AnnotationDbi", "org.Hs.eg.db", "ReactomePA", "msigdbr")},
            write_fixtures=True,
            bad_fixture_columns=True,
        ),
    )

    assert detection["status"] == "blocked"
    assert any(blocker["code"] == "fixture_output_missing_columns" for blocker in detection["blockers"])


def test_real_external_enrichment_r_backend_detection_reports_current_runtime(tmp_path: Path) -> None:
    detection = detect_external_enrichment_r_backend(storage_root=tmp_path, write_snapshot=False)
    if not detection["rscript"]["available"]:
        pytest.skip("Rscript is not available in this environment")

    assert detection["schema_version"] == R_ENRICHMENT_BACKEND_DETECTION_SCHEMA_VERSION
    assert detection["rscript"]["path"]
    assert detection["rscript"]["version"].startswith("R version")
    assert detection["rscript"]["architecture"] in {"arm64", "x86_64", "unknown"}
    assert detection["install_action"] == "none_detect_first_only"
    assert detection["packaging_policy"] == "external_runtime_not_bundled"
    if detection["status"] == "blocked":
        missing = {blocker.get("package") for blocker in detection["blockers"]}
        assert missing
    else:
        validation = run_external_enrichment_r_backend_validation(storage_root=tmp_path)
        assert validation["status"] in {"passed", "blocked"}


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


def _r_enrichment_runner(*, installed: dict[str, str], write_fixtures: bool = False, bad_fixture_columns: bool = False):
    def runner(command, **_kwargs):
        script = command[-1] if command[-1] not in {str(command[0])} else ""
        if len(command) >= 4 and "--vanilla" in command and write_fixtures:
            ora_path = Path(command[-2])
            gsea_path = Path(command[-1])
            ora_path.parent.mkdir(parents=True, exist_ok=True)
            gsea_path.parent.mkdir(parents=True, exist_ok=True)
            if bad_fixture_columns:
                ora_path.write_text("ID\tDescription\nPathway_A\tPathway_A\n", encoding="utf-8")
            else:
                ora_path.write_text(
                    "ID\tDescription\tGeneRatio\tBgRatio\tpvalue\tp.adjust\tqvalue\tgeneID\tCount\n"
                    "Pathway_A\tPathway_A\t3/3\t5/12\t0.045\t0.091\t0.048\tG1/G2/G3\t3\n",
                    encoding="utf-8",
                )
            gsea_path.write_text(
                "pathway\tES\tNES\tpval\tpadj\tleadingEdge\tsize\n"
                "Pathway_A\t1.0\t1.77\t0.007\t0.022\tG1/G2/G3/G4\t4\n",
                encoding="utf-8",
            )
            stdout = (
                "PLOT_SMOKE_BEGIN\n"
                "check\tok\tclass\terror\n"
                "ora_dotplot\tTRUE\tenrichplotDot/gg/ggplot\t\n"
                "ora_barplot\tTRUE\tgg/ggplot\t\n"
                "gsea_curve\tTRUE\tgglist/list\t\n"
                "PLOT_SMOKE_END\n"
            )
            return subprocess.CompletedProcess(command, 0, stdout=stdout, stderr="")
        if "R.version.string" in script:
            return subprocess.CompletedProcess(
                command,
                0,
                stdout="R version 4.4.2 (2024-10-31)\naarch64\n/Library/Frameworks/R.framework/Versions/4.4-arm64/Resources/library\n",
                stderr="",
            )
        if "requireNamespace" in script:
            names = (
                "clusterProfiler",
                "fgsea",
                "DOSE",
                "enrichplot",
                "ggplot2",
                "AnnotationDbi",
                "org.Hs.eg.db",
                "ReactomePA",
                "msigdbr",
                "pathview",
                "GO.db",
                "KEGGREST",
            )
            lines = ["package\tavailable\tversion\timportable\tmissing_reason"]
            for name in names:
                if name in installed:
                    lines.append(f"{name}\tTRUE\t{installed[name]}\tTRUE\t")
                else:
                    lines.append(f"{name}\tFALSE\t\tFALSE\tpackage_not_installed_or_not_on_libpaths:{name}")
            return subprocess.CompletedProcess(command, 0, stdout="\n".join(lines) + "\n", stderr="")
        return subprocess.CompletedProcess(command, 1, stdout="", stderr="unexpected R command")

    return runner
