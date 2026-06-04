from __future__ import annotations

import json
import shutil
import subprocess
from copy import deepcopy
from pathlib import Path

import pytest

from app.analysis_runtime.resources import full_mode_resource_blockers, validate_analysis_resource_manifest


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_MODULES = {
    "deg",
    "survival",
    "univariate",
    "multivariate",
    "enrichment",
    "immune_infiltration",
    "spatial_transcriptomics",
    "docking",
    "molecular_dynamics",
}


def read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def rscript_path() -> str:
    path = shutil.which("Rscript")
    if path is None:
        pytest.skip("Rscript is not available in this environment")
    return path


def test_analysis_registry_declares_standard_modules_modes_and_package_contract() -> None:
    registry = read_json(ROOT / "analysis" / "registry" / "analysis_modules.json")

    assert registry["schema_version"] == "biomedpilot.analysis_modules.v1"
    assert registry["standard_entrypoint"] == "analysis/runners/run_module.R"
    assert registry["standard_result_package"] == {
        "required_files": ["result.json", "provenance.json"],
        "required_directories": ["tables", "plots", "reports", "logs"],
    }
    modules = {item["module_id"]: item for item in registry["modules"]}  # type: ignore[index]
    assert REQUIRED_MODULES <= set(modules)
    for module_id, module in modules.items():
        modes = module["modes"]
        assert modes["mock"]["supported"] is True
        assert (ROOT / modes["mock"]["fixture_input"]).is_file()
        assert (ROOT / modes["mock"]["fixture_output_package"]).is_dir()
        assert "lite" in modes
        assert "full" in modes
        assert module["result_package_contract"] == "analysis/schemas/output/result_package.schema.json"
        assert module["analysis_environment"]
        assert (ROOT / module["module_manifest"]).exists()


def test_registered_module_manifests_declare_worker_environment_and_package_contract() -> None:
    registry = read_json(ROOT / "analysis" / "registry" / "analysis_modules.json")
    modules = {item["module_id"]: item for item in registry["modules"]}  # type: ignore[index]

    for module_id, module in modules.items():
        manifest_path = ROOT / module["module_manifest"]
        manifest = read_json(manifest_path)
        modes = manifest["modes"]
        environment = manifest["environment"]
        dependency_policy = manifest["dependency_policy"]

        assert manifest["schema_version"] == "biomedpilot.analysis_module_manifest.v1"
        assert manifest["module_id"] == module_id
        assert manifest["standard_entrypoint"] == registry["standard_entrypoint"]
        assert manifest["input_schema"] == "analysis/schemas/input/module_input.schema.json"
        assert manifest["output_schema"] == "analysis/schemas/output/result_package.schema.json"
        assert manifest["result_package_contract"] == "analysis/schemas/output/result_package.schema.json"
        assert manifest["result_package_required"] == ["result.json", "provenance.json", "tables", "plots", "reports", "logs"]
        assert modes["mock"]["supported"] is True
        assert (ROOT / modes["mock"]["fixture_input"]).is_file()
        assert (ROOT / modes["mock"]["fixture_output_package"]).is_dir()
        if module_id in {"deg", "enrichment", "survival", "univariate", "multivariate", "immune_infiltration", "docking"}:
            assert modes["lite"]["supported"] is True
            assert modes["lite"]["worker_backend"] == "rscript"
            assert (ROOT / modes["lite"]["fixture_input"]).is_file()
        else:
            assert modes["lite"]["supported"] is False
        assert modes["full"]["supported"] is False
        assert environment["app_dev"] == "docker/Dockerfile.app-dev"
        assert (ROOT / manifest["dockerfile"]).exists()
        assert (ROOT / manifest["environment_lock"]).exists()
        assert dependency_policy == {
            "detection": "detect_first",
            "runtime_install": "forbidden",
            "default_app_dependency": False,
        }


def test_per_module_mock_fixtures_are_standard_result_packages() -> None:
    registry = read_json(ROOT / "analysis" / "registry" / "analysis_modules.json")

    for module in registry["modules"]:  # type: ignore[index]
        module_id = module["module_id"]
        mode_policy = module["modes"]["mock"]
        fixture_input = read_json(ROOT / mode_policy["fixture_input"])
        fixture_package = ROOT / mode_policy["fixture_output_package"]
        result = read_json(fixture_package / "result.json")
        provenance = read_json(fixture_package / "provenance.json")

        assert fixture_input["schema_version"] == "biomedpilot.analysis.module_input.v1"
        assert fixture_input["module_id"] == module_id
        assert fixture_input["mode"] == "mock"
        assert result["module_id"] == module_id
        assert result["mode"] == "mock"
        assert result["status"] == "passed"
        assert result["result_semantics"] == "testing_level"
        assert "mock_result_not_scientific_output" in result["warnings"]
        assert provenance["module_id"] == module_id
        assert provenance["runtime"]["r_version"] == "not_required_for_mock"
        for dirname in ("tables", "plots", "reports", "logs"):
            assert (fixture_package / dirname).is_dir()


def test_analysis_environment_split_scaffold_exists_without_claiming_full_readiness() -> None:
    dockerfiles = {
        "docker/Dockerfile.app-dev",
        "docker/Dockerfile.r-bio-core",
        "docker/Dockerfile.r-bio-full",
        "docker/Dockerfile.r-spatial-full",
        "docker/Dockerfile.r-chem-full",
        "docker/Dockerfile.r-chem-gpu",
    }
    locks = {
        "renv/renv.app.lock",
        "renv/renv.bio-core.lock",
        "renv/renv.bio-full.lock",
        "renv/renv.spatial-full.lock",
        "renv/renv.chem-full.lock",
    }

    for relative in dockerfiles:
        text = (ROOT / relative).read_text(encoding="utf-8")
        assert "runtime-package-install=\"forbidden\"" in text
        assert (ROOT / relative).exists()
    for relative in locks:
        lock = read_json(ROOT / relative)
        assert lock["Packages"] == {}
        assert lock["BioMedPilotPolicy"]["status"] == "scaffold_only_not_restored"  # type: ignore[index]
        assert lock["BioMedPilotPolicy"]["runtime_package_install"] == "forbidden"  # type: ignore[index]


def test_spatial_and_chem_modules_are_isolated_from_app_dev_and_bio_core() -> None:
    spatial = read_json(ROOT / "analysis" / "modules" / "spatial_transcriptomics" / "module.json")
    docking = read_json(ROOT / "analysis" / "modules" / "docking" / "module.json")
    molecular_dynamics = read_json(ROOT / "analysis" / "modules" / "molecular_dynamics" / "module.json")

    assert spatial["dockerfile"] == "docker/Dockerfile.r-spatial-full"
    assert spatial["environment_lock"] == "renv/renv.spatial-full.lock"
    assert docking["dockerfile"] == "docker/Dockerfile.r-chem-full"
    assert molecular_dynamics["dockerfile"] == "docker/Dockerfile.r-chem-gpu"
    assert "external_tool_policy" in docking
    assert "external_tool_policy" in molecular_dynamics


def test_standard_schemas_and_mock_result_package_exist_without_r_dependency() -> None:
    input_schema = read_json(ROOT / "analysis" / "schemas" / "input" / "module_input.schema.json")
    output_schema = read_json(ROOT / "analysis" / "schemas" / "output" / "result_package.schema.json")
    result = read_json(ROOT / "analysis" / "fixtures" / "outputs" / "mock_result_package" / "result.json")
    provenance = read_json(ROOT / "analysis" / "fixtures" / "outputs" / "mock_result_package" / "provenance.json")

    assert "module_id" in input_schema["required"]
    assert "result_json" in output_schema["required"]
    assert "provenance_json" in output_schema["required"]
    assert result["mode"] == "mock"
    assert result["status"] == "passed"
    assert provenance["mode"] == "mock"
    for dirname in ("tables", "plots", "reports", "logs"):
        assert (ROOT / "analysis" / "fixtures" / "outputs" / "mock_result_package" / dirname).exists()


def test_default_source_tree_does_not_install_r_packages_in_request_flow() -> None:
    forbidden = (
        "install.packages",
        "BiocManager::install",
        "pak::pkg_install",
        "remotes::install_github",
    )
    searched_roots = [ROOT / "app", ROOT / "scripts", ROOT / "analysis", ROOT / "docker"]
    offenders: list[str] = []
    for root in searched_roots:
        for path in root.rglob("*"):
            is_dockerfile = path.name.startswith("Dockerfile")
            if not path.is_file() or (path.suffix.lower() not in {".py", ".r", ".rscript", ".sh"} and not is_dockerfile):
                continue
            if "__pycache__" in path.parts or "legacy" in path.parts:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            for needle in forbidden:
                if needle in text:
                    offenders.append(f"{path.relative_to(ROOT)}:{needle}")
    assert offenders == []


def test_standard_r_runner_has_no_runtime_package_installer_or_library_imports() -> None:
    runner = (ROOT / "analysis" / "runners" / "run_module.R").read_text(encoding="utf-8")

    assert "install.packages" not in runner
    assert "BiocManager::install" not in runner
    assert "pak::pkg_install" not in runner
    assert "remotes::install_github" not in runner
    assert "library(" not in runner
    assert "require(" not in runner
    assert "run_module.R <input_json> <output_dir> <mode>" in runner
    assert "result.json" in runner
    assert "provenance.json" in runner


def test_active_bioinformatics_r_subprocess_invocation_is_centralized_in_analysis_runtime() -> None:
    offenders: list[str] = []
    for path in (ROOT / "app" / "bioinformatics").rglob("*.py"):
        if "__pycache__" in path.parts or "legacy" in path.parts:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if "subprocess.run(" in text and ("--vanilla" in text or "Rscript" in text or "library(" in text):
            offenders.append(str(path.relative_to(ROOT)))

    assert offenders == []


def test_standard_r_runner_mock_mode_copies_module_fixture_package(tmp_path: Path) -> None:
    rscript = rscript_path()
    output_dir = tmp_path / "r-runner-output"
    input_json = ROOT / "analysis" / "fixtures" / "inputs" / "enrichment" / "module_input.json"

    completed = subprocess.run(
        [rscript, str(ROOT / "analysis" / "runners" / "run_module.R"), str(input_json), str(output_dir), "mock"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    result = read_json(output_dir / "result.json")
    provenance = read_json(output_dir / "provenance.json")
    assert result["module_id"] == "enrichment"
    assert result["task_id"] == "enrichment-mock-fixture"
    assert result["status"] == "passed"
    assert result["result_semantics"] == "testing_level"
    assert "mock_result_not_scientific_output" in result["warnings"]
    assert (output_dir / "tables" / "mock_summary.tsv").is_file()
    assert (output_dir / "reports" / "README_mock.md").is_file()
    assert (output_dir / "logs" / "worker.log").is_file()
    assert provenance["module_id"] == "enrichment"
    assert provenance["task_id"] == "enrichment-mock-fixture"
    assert provenance["runtime"]["r_version"] != "not_required_for_mock"  # type: ignore[index]
    assert provenance["runtime"]["r_version"] != "not_executed"  # type: ignore[index]
    assert provenance["input_hash"] != "fixture"
    assert provenance["parameter_hash"] != "fixture"
    assert provenance["parameter_hash"] != provenance["input_hash"]
    assert "analysis/runners/run_module.R" in provenance["command"]


def test_standard_r_runner_lite_full_modes_write_blocked_standard_package(tmp_path: Path) -> None:
    rscript = rscript_path()
    output_dir = tmp_path / "r-runner-full-output"
    payload = read_json(ROOT / "analysis" / "fixtures" / "inputs" / "enrichment" / "module_input.json")
    payload["mode"] = "full"
    input_json = tmp_path / "full_input.json"
    input_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    completed = subprocess.run(
        [rscript, str(ROOT / "analysis" / "runners" / "run_module.R"), str(input_json), str(output_dir), "full"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 2
    result = read_json(output_dir / "result.json")
    provenance = read_json(output_dir / "provenance.json")
    assert result["module_id"] == "enrichment"
    assert result["mode"] == "full"
    assert result["status"] == "blocked"
    assert "standard_worker_mode_not_enabled:full" in result["blockers"]
    assert provenance["runtime"]["r_version"] == "not_executed"  # type: ignore[index]
    assert provenance["parameter_hash"] != provenance["input_hash"]
    assert (output_dir / "logs" / "worker.log").is_file()


def test_standard_r_runner_enrichment_lite_mode_writes_real_fixture_ora_package(tmp_path: Path) -> None:
    rscript = rscript_path()
    output_dir = tmp_path / "r-runner-lite-output"
    input_json = ROOT / "analysis" / "fixtures" / "inputs" / "enrichment" / "module_input_lite.json"

    completed = subprocess.run(
        [rscript, str(ROOT / "analysis" / "runners" / "run_module.R"), str(input_json), str(output_dir), "lite"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    result = read_json(output_dir / "result.json")
    provenance = read_json(output_dir / "provenance.json")
    table = (output_dir / "tables" / "lite_ora_result.tsv").read_text(encoding="utf-8")
    assert result["module_id"] == "enrichment"
    assert result["mode"] == "lite"
    assert result["status"] == "passed"
    assert result["result_semantics"] == "testing_level"
    assert "lite_result_not_formal_analysis" in result["warnings"]
    assert "lite_enrichment_ora_result_table" in str(result["tables"])
    assert "DNA_DAMAGE" in table
    assert "p.adjust" in table.splitlines()[0]
    assert provenance["runtime"]["r_version"] != "not_executed"  # type: ignore[index]
    assert provenance["runtime"]["bioconductor_version"] == "not_required_for_lite_base_r"  # type: ignore[index]
    assert provenance["parameter_hash"] != provenance["input_hash"]
    assert (output_dir / "reports" / "README_lite.md").is_file()


def test_standard_r_runner_survival_lite_mode_writes_real_fixture_km_logrank_package(tmp_path: Path) -> None:
    rscript = rscript_path()
    output_dir = tmp_path / "r-runner-survival-lite-output"
    input_json = ROOT / "analysis" / "fixtures" / "inputs" / "survival" / "module_input_lite.json"

    completed = subprocess.run(
        [rscript, str(ROOT / "analysis" / "runners" / "run_module.R"), str(input_json), str(output_dir), "lite"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    result = read_json(output_dir / "result.json")
    provenance = read_json(output_dir / "provenance.json")
    km_table = (output_dir / "tables" / "lite_km_curve.tsv").read_text(encoding="utf-8")
    logrank_table = (output_dir / "tables" / "lite_logrank_result.tsv").read_text(encoding="utf-8")
    assert result["module_id"] == "survival"
    assert result["mode"] == "lite"
    assert result["status"] == "passed"
    assert result["result_semantics"] == "testing_level"
    assert "clinical_conclusion_not_generated" in result["warnings"]
    assert "lite_survival_km_curve_table" in str(result["tables"])
    assert "lite_survival_logrank_result_table" in str(result["tables"])
    assert "survival" in km_table.splitlines()[0]
    assert "p_value" in logrank_table.splitlines()[0]
    assert provenance["runtime"]["r_version"] != "not_executed"  # type: ignore[index]
    assert provenance["runtime"]["bioconductor_version"] == "not_required_for_lite_base_r"  # type: ignore[index]
    assert (output_dir / "reports" / "README_lite.md").is_file()


def test_standard_r_runner_univariate_lite_mode_writes_real_fixture_association_package(tmp_path: Path) -> None:
    rscript = rscript_path()
    output_dir = tmp_path / "r-runner-univariate-lite-output"
    input_json = ROOT / "analysis" / "fixtures" / "inputs" / "univariate" / "module_input_lite.json"

    completed = subprocess.run(
        [rscript, str(ROOT / "analysis" / "runners" / "run_module.R"), str(input_json), str(output_dir), "lite"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    result = read_json(output_dir / "result.json")
    provenance = read_json(output_dir / "provenance.json")
    table = (output_dir / "tables" / "lite_univariate_association.tsv").read_text(encoding="utf-8")
    assert result["module_id"] == "univariate"
    assert result["mode"] == "lite"
    assert result["status"] == "passed"
    assert result["result_semantics"] == "testing_level"
    assert "clinical_conclusion_not_generated" in result["warnings"]
    assert "lite_univariate_clinical_association_table" in str(result["tables"])
    assert "p_value" in table.splitlines()[0]
    assert "not_generated" in table
    assert provenance["runtime"]["r_version"] != "not_executed"  # type: ignore[index]
    assert provenance["runtime"]["bioconductor_version"] == "not_required_for_lite_base_r"  # type: ignore[index]
    assert (output_dir / "reports" / "README_lite.md").is_file()


def test_standard_r_runner_multivariate_lite_mode_writes_real_fixture_association_package(tmp_path: Path) -> None:
    rscript = rscript_path()
    output_dir = tmp_path / "r-runner-multivariate-lite-output"
    input_json = ROOT / "analysis" / "fixtures" / "inputs" / "multivariate" / "module_input_lite.json"

    completed = subprocess.run(
        [rscript, str(ROOT / "analysis" / "runners" / "run_module.R"), str(input_json), str(output_dir), "lite"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    result = read_json(output_dir / "result.json")
    provenance = read_json(output_dir / "provenance.json")
    table = (output_dir / "tables" / "lite_multivariate_association.tsv").read_text(encoding="utf-8")
    assert result["module_id"] == "multivariate"
    assert result["mode"] == "lite"
    assert result["status"] == "passed"
    assert result["result_semantics"] == "testing_level"
    assert "clinical_conclusion_not_generated" in result["warnings"]
    assert "lite_multivariate_clinical_association_table" in str(result["tables"])
    assert "model_formula" in table.splitlines()[0]
    assert "p_value" in table.splitlines()[0]
    assert "not_generated" in table
    assert provenance["runtime"]["r_version"] != "not_executed"  # type: ignore[index]
    assert provenance["runtime"]["bioconductor_version"] == "not_required_for_lite_base_r"  # type: ignore[index]
    assert (output_dir / "reports" / "README_lite.md").is_file()


def test_standard_r_runner_immune_lite_mode_writes_real_fixture_heatmap_package(tmp_path: Path) -> None:
    rscript = rscript_path()
    output_dir = tmp_path / "r-runner-immune-lite-output"
    input_json = ROOT / "analysis" / "fixtures" / "inputs" / "immune_infiltration" / "module_input_lite.json"

    completed = subprocess.run(
        [rscript, str(ROOT / "analysis" / "runners" / "run_module.R"), str(input_json), str(output_dir), "lite"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    result = read_json(output_dir / "result.json")
    provenance = read_json(output_dir / "provenance.json")
    table = (output_dir / "tables" / "lite_immune_scores.tsv").read_text(encoding="utf-8")
    plot = output_dir / "plots" / "lite_immune_heatmap.svg"
    assert result["module_id"] == "immune_infiltration"
    assert result["mode"] == "lite"
    assert result["status"] == "passed"
    assert result["result_semantics"] == "testing_level"
    assert "clinical_conclusion_not_generated" in result["warnings"]
    assert "lite_immune_infiltration_heatmap_svg" in str(result["plots"])
    assert "signature" in table.splitlines()[0]
    assert "score" in table.splitlines()[0]
    assert "not_generated" in table
    assert plot.is_file()
    assert "<svg" in plot.read_text(encoding="utf-8", errors="ignore")
    assert provenance["runtime"]["r_version"] != "not_executed"  # type: ignore[index]
    assert provenance["runtime"]["bioconductor_version"] == "not_required_for_lite_base_r"  # type: ignore[index]
    assert (output_dir / "reports" / "README_lite.md").is_file()


def test_standard_r_runner_blocks_input_manifest_mode_mismatch(tmp_path: Path) -> None:
    rscript = rscript_path()
    output_dir = tmp_path / "r-runner-mismatch-output"
    input_json = ROOT / "analysis" / "fixtures" / "inputs" / "enrichment" / "module_input.json"

    completed = subprocess.run(
        [rscript, str(ROOT / "analysis" / "runners" / "run_module.R"), str(input_json), str(output_dir), "full"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 2
    result = read_json(output_dir / "result.json")
    assert result["status"] == "blocked"
    assert "module_input_mode_arg_mismatch:input=mock,arg=full" in result["blockers"]


def test_analysis_resource_manifest_declares_full_mode_resource_locks_without_downloads() -> None:
    manifest = read_json(ROOT / "analysis" / "resources" / "manifest.json")
    validation = validate_analysis_resource_manifest(manifest)
    resources = {item["resource_id"]: item for item in manifest["resources"]}  # type: ignore[index]

    assert validation["status"] == "passed"
    assert validation["full_mode_ready"] is False
    assert resources["mock_fixture_builtin_v1"]["status"] == "locked"
    required_resource_ids = {
        "reactome_full",
        "msigdb_full",
        "go_full",
        "kegg_full",
        "orgdb_human_full",
        "spatial_reference_full",
        "cellchatdb_full",
        "autodock_vina_tool",
        "docking_template_bundle",
        "gromacs_tool",
        "md_forcefield_template_bundle",
    }
    assert required_resource_ids <= set(resources)
    for resource_id in required_resource_ids:
        resource = resources[resource_id]
        assert resource["runtime_download_allowed"] is False
        assert resource["version"] == "required_before_full_mode"
        assert resource["hash"] == "required_before_full_mode"
        assert resource["license"] == "required_before_full_mode"
        assert resource["cache_path"].startswith("external_analysis_resources/")
        assert resource["status"].startswith("blocked_until_")


def test_full_mode_resource_blockers_are_module_specific() -> None:
    enrichment_blockers = full_mode_resource_blockers("enrichment")
    spatial_blockers = full_mode_resource_blockers("spatial_transcriptomics")
    docking_blockers = full_mode_resource_blockers("docking")
    md_blockers = full_mode_resource_blockers("molecular_dynamics")

    assert "analysis_resource_not_locked:reactome_full" in enrichment_blockers
    assert "analysis_resource_not_locked:msigdb_full" in enrichment_blockers
    assert "analysis_resource_not_locked:spatial_reference_full" in spatial_blockers
    assert "analysis_resource_not_locked:autodock_vina_tool" in docking_blockers
    assert "analysis_resource_not_locked:gromacs_tool" in md_blockers
    assert "analysis_resource_not_locked:gromacs_tool" not in enrichment_blockers


def test_locked_resource_with_placeholder_fields_blocks_full_mode() -> None:
    manifest = deepcopy(read_json(ROOT / "analysis" / "resources" / "manifest.json"))
    resources = {item["resource_id"]: item for item in manifest["resources"]}  # type: ignore[index]
    reactome = resources["reactome_full"]
    reactome["status"] = "locked"
    reactome["version"] = "Reactome-2026-04"
    reactome["source"] = "Reactome release archive"
    reactome["hash"] = "required_before_full_mode"
    reactome["license"] = "Reactome Content Service License"
    reactome["cache_path"] = "external_analysis_resources/reactome/Reactome-2026-04"

    validation = validate_analysis_resource_manifest(manifest)
    blockers = validation["blockers"]

    assert validation["status"] == "blocked"
    assert (
        "analysis_resource_locked_with_placeholder_fields:reactome_full:hash"
        in blockers
    )
    assert validation["full_mode_ready"] is False
    assert "analysis_resource_locked_with_placeholder_fields:reactome_full:hash" in full_mode_resource_blockers(
        "enrichment", manifest
    )


def test_blocked_resource_with_partial_final_lock_warns_but_still_blocks_module_full_mode() -> None:
    manifest = deepcopy(read_json(ROOT / "analysis" / "resources" / "manifest.json"))
    resources = {item["resource_id"]: item for item in manifest["resources"]}  # type: ignore[index]
    reactome = resources["reactome_full"]
    reactome["version"] = "Reactome-2026-04"
    reactome["hash"] = "sha256:0123456789abcdef"

    validation = validate_analysis_resource_manifest(manifest)

    assert validation["status"] == "passed"
    assert "blocked_resource_has_partial_final_lock:reactome_full" in validation["warnings"]
    blockers = full_mode_resource_blockers("enrichment", manifest)
    assert "analysis_resource_not_locked:reactome_full" in blockers


def test_app_dev_dockerfile_excludes_heavy_analysis_dependency_names() -> None:
    app_dev = (ROOT / "docker" / "Dockerfile.app-dev").read_text(encoding="utf-8")
    heavy_dependency_names = (
        "ReactomePA",
        "reactome.db",
        "Seurat",
        "CellChat",
        "GSVA",
        "AutoDock",
        "GROMACS",
        "survminer",
        "clusterProfiler",
    )

    offenders = [name for name in heavy_dependency_names if name in app_dev]
    assert offenders == []
