from __future__ import annotations

import tempfile
import subprocess
import sys
import textwrap
import unittest
from pathlib import Path
from unittest.mock import Mock, patch


REPO_ROOT = Path(__file__).resolve().parents[1]


class RepoSmokeTests(unittest.TestCase):
    def _read_text(self, relative_path: str) -> str:
        return (REPO_ROOT / relative_path).read_text(encoding="utf-8")

    def test_root_and_gui_requirements_are_layered(self) -> None:
        root_requirements = self._read_text("requirements.txt")
        gui_requirements = self._read_text("geo_tool/requirements.txt")

        self.assertIn("requests", root_requirements)
        self.assertIn("-r ../requirements.txt", gui_requirements)
        self.assertIn("PySide6", gui_requirements)

    def test_launcher_check_runs_from_repo_root(self) -> None:
        result = subprocess.run(
            [sys.executable, "geo_tool/run_geo_tool.py", "--check"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        self.assertIn("repo_root=", result.stdout)
        self.assertIn("gui_available=", result.stdout)
        self.assertIn("GEOparse_available=True", result.stdout)
        self.assertIn("canonical_entrypoint=", result.stdout)
        self.assertIn("repo_venv_python=", result.stdout)

    def test_shell_wrappers_do_not_embed_machine_specific_runtime_hacks(self) -> None:
        bootstrap_script = self._read_text("geo_tool/bootstrap_geo_tool.sh")
        run_script = self._read_text("geo_tool/run_geo_tool.sh")

        self.assertNotIn("python3.12", bootstrap_script)
        self.assertNotIn("brew install", bootstrap_script)
        self.assertNotIn("Desktop/生信分析", bootstrap_script)
        self.assertNotIn("/tmp/geo_tool_qt_runtime", run_script)
        self.assertNotIn("DYLD_FRAMEWORK_PATH", run_script)
        self.assertIn("run_geo_tool.py", run_script)

    def test_shell_wrappers_support_posix_and_windows_virtualenv_layouts(self) -> None:
        bootstrap_script = self._read_text("geo_tool/bootstrap_geo_tool.sh")
        run_script = self._read_text("geo_tool/run_geo_tool.sh")

        for script_text in (bootstrap_script, run_script):
            self.assertIn('REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"', script_text)
            self.assertIn('.venv/bin/python', script_text)
            self.assertIn('.venv/Scripts/python.exe', script_text)

    def test_bootstrap_installs_layered_gui_requirements(self) -> None:
        bootstrap_script = self._read_text("geo_tool/bootstrap_geo_tool.sh")

        self.assertIn("geo_tool/requirements.txt", bootstrap_script)
        self.assertIn("PySide6", bootstrap_script)

    def test_windows_wrappers_exist_and_use_repo_virtualenv(self) -> None:
        bootstrap_bat = REPO_ROOT / "geo_tool" / "bootstrap_geo_tool.bat"
        run_bat = REPO_ROOT / "geo_tool" / "run_geo_tool.bat"

        self.assertTrue(bootstrap_bat.exists())
        self.assertTrue(run_bat.exists())

        bootstrap_text = bootstrap_bat.read_text(encoding="utf-8")
        run_text = run_bat.read_text(encoding="utf-8")

        self.assertIn(r".venv\Scripts\python.exe", bootstrap_text)
        self.assertIn(r"geo_tool\requirements.txt", bootstrap_text)
        self.assertIn(r".venv\Scripts\python.exe", run_text)
        self.assertIn(r"geo_tool\run_geo_tool.py", run_text)
        self.assertIn("%*", run_text)
        self.assertIn('set "SCRIPT_DIR=%~dp0"', bootstrap_text)
        self.assertIn('for %%I in ("%SCRIPT_DIR%..") do set "REPO_ROOT=%%~fI"', bootstrap_text)
        self.assertIn('cd /d "%REPO_ROOT%"', bootstrap_text)
        self.assertIn('set "SCRIPT_DIR=%~dp0"', run_text)
        self.assertIn('for %%I in ("%SCRIPT_DIR%..") do set "REPO_ROOT=%%~fI"', run_text)
        self.assertIn('cd /d "%REPO_ROOT%"', run_text)
        self.assertIn('call "%VENV_PYTHON%" "%REPO_ROOT%\\geo_tool\\run_geo_tool.py" %*', run_text)

    def test_sh_and_bat_wrappers_reference_consistent_requirements_and_entrypoints(self) -> None:
        bootstrap_sh = self._read_text("geo_tool/bootstrap_geo_tool.sh")
        run_sh = self._read_text("geo_tool/run_geo_tool.sh")
        bootstrap_bat = self._read_text("geo_tool/bootstrap_geo_tool.bat")
        run_bat = self._read_text("geo_tool/run_geo_tool.bat")

        self.assertIn("geo_tool/requirements.txt", bootstrap_sh)
        self.assertIn(r"geo_tool\requirements.txt", bootstrap_bat)
        self.assertIn("run_geo_tool.py", run_sh)
        self.assertIn("run_geo_tool.py", run_bat)

    def test_readme_documents_minimal_repro_path(self) -> None:
        readme = self._read_text("README.md")

        self.assertIn("python -m venv .venv", readme)
        self.assertIn("python -m pip install -r geo_tool/requirements.txt", readme)
        self.assertIn("python geo_tool/run_geo_tool.py --check", readme)
        self.assertIn("python geo_tool/run_geo_tool.py", readme)
        self.assertIn("python scripts/run_smoke_tests.py", readme)
        self.assertIn("py -3 -m venv .venv", readme)
        self.assertIn(r"geo_tool\bootstrap_geo_tool.bat", readme)
        self.assertIn(r"geo_tool\run_geo_tool.bat --check", readme)

    def test_smoke_script_covers_minimal_mainline_gate(self) -> None:
        smoke_script = self._read_text("scripts/run_smoke_tests.py")

        self.assertIn("tests.test_repo_smoke", smoke_script)
        self.assertIn("tests.test_geo_detector", smoke_script)
        self.assertIn("tests.test_geo_workflow_integration", smoke_script)
        self.assertIn("tests.test_module4_mainline_bridge", smoke_script)
        self.assertIn('geo_tool/run_geo_tool.py", "--check"', smoke_script)

    def test_readme_freezes_mainline_surface_contract(self) -> None:
        readme = self._read_text("README.md")

        self.assertIn("## Mainline Surface Contract", readme)
        self.assertIn("geo_tool/run_geo_tool.py", readme)
        self.assertIn("geo_tool/main.py", readme)
        self.assertIn("geo_tool/geo_workflow.py", readme)
        self.assertIn("geo_pipeline.download.download_core_geo_records", readme)
        self.assertIn("geo_pipeline.process.process_from_local_family_soft", readme)
        self.assertIn("geo_processing.validate_downloaded_dataset", readme)
        self.assertIn("geo_processing.detect_dataset", readme)
        self.assertIn("geo_processing.load_module1_dataset_context", readme)
        self.assertIn("Wrapper surface:", readme)
        self.assertIn("Legacy surface:", readme)
        self.assertIn("Duplicate surface:", readme)
        self.assertNotIn("tcga_gtex.facade", readme)

    def test_structure_doc_freezes_surface_categories(self) -> None:
        structure_doc = self._read_text("docs/repo_structure_audit.md")

        self.assertIn("## 3.1 主线调用面契约", structure_doc)
        self.assertIn("当前主线正式调用面最小集合固定为", structure_doc)
        self.assertIn("canonical surface", structure_doc)
        self.assertIn("wrapper surface", structure_doc)
        self.assertIn("legacy surface", structure_doc)
        self.assertIn("duplicate surface", structure_doc)
        self.assertIn("geo_pipeline.process.process_from_local_family_soft", structure_doc)
        self.assertNotIn("tcga_gtex.facade", structure_doc)

    def test_module4_main_py_routed_optional_runtime_contract_is_frozen_in_docs(self) -> None:
        readme = self._read_text("README.md")
        structure_doc = self._read_text("docs/repo_structure_audit.md")

        self.assertIn("## Module 4 Main.py Routed Optional Runtime Contract", readme)
        self.assertIn("Module 4 is currently `main.py routed optional runtime path`", readme)
        self.assertIn("The only allowed integration point for Module 4 is `geo_tool/main.py` during", readme)
        self.assertIn("`geo_tool/geo_workflow.py` is a forbidden integration point", readme)
        self.assertIn("search_tcga_gtex", readme)
        self.assertIn("resolve_tcga_gtex_files", readme)
        self.assertIn("GUI as an optional TCGA/GTEx query/result route", readme)
        self.assertIn("download_tcga_gtex_dataset", readme)
        self.assertIn("build_tcga_gtex_bundle", readme)
        self.assertIn("get_tcga_gtex_summary", readme)
        self.assertIn("Missing locators must return a clear failed result", readme)
        self.assertIn("production-grade TCGA/GDC/GTEx downloader", readme)

        self.assertIn("## 3.2 Module 4 main.py routed optional runtime path 契约", structure_doc)
        self.assertIn("当前 Module 4 状态固定为 `main.py routed optional runtime path`", structure_doc)
        self.assertIn("接入位置固定为 `geo_tool/main.py` 的查询 / 结果分流阶段", structure_doc)
        self.assertIn("`geo_tool/geo_workflow.py` 是禁止接入位置", structure_doc)
        self.assertIn("`tcga_gtex/mainline_bridge.py` 是当前可测试 bridge", structure_doc)
        self.assertIn("download_tcga_gtex_dataset", structure_doc)
        self.assertIn("build_tcga_gtex_bundle", structure_doc)
        self.assertIn("get_tcga_gtex_summary", structure_doc)
        self.assertIn("不是 canonical GEO workflow stage", structure_doc)

    def test_stage_acceptance_baseline_docs_freeze_claim_boundaries(self) -> None:
        readme = self._read_text("README.md")
        structure_doc = self._read_text("docs/repo_structure_audit.md")
        stage_doc = self._read_text("docs/mainline_acceptance_baseline.md")

        self.assertIn("docs/mainline_acceptance_baseline.md", readme)
        self.assertIn("## Stage Acceptance Baseline", readme)
        self.assertIn("This is not a final product release.", readme)
        self.assertIn("Module 3 is currently `mainline post-workflow action`", readme)
        self.assertIn("Module 4 is currently `main.py routed optional runtime path`", readme)
        self.assertIn("minimal local", readme)
        self.assertIn("must not be described as", readme)
        self.assertIn("`Module 3` as a canonical workflow stage", readme)
        self.assertIn("`Module 4` as a canonical GEO workflow stage", readme)
        self.assertIn("`Module 4` as a production-grade TCGA/GDC/GTEx downloader", readme)

        self.assertIn("## 3.3 阶段性验收基线", structure_doc)
        self.assertIn("Module 3 当前状态是 `mainline post-workflow action`", structure_doc)
        self.assertIn("Module 4 当前状态是 `main.py routed optional runtime path`", structure_doc)
        self.assertIn("不得把当前仓库描述为最终产品发布版", structure_doc)
        self.assertIn("不得把 Module 4 描述为 canonical GEO workflow stage", structure_doc)

        self.assertIn("## 1. 基线性质", stage_doc)
        self.assertIn("阶段性可用基线", stage_doc)
        self.assertIn("不是最终产品发布版说明", stage_doc)
        self.assertIn("## 2. 当前可以宣称的能力边界", stage_doc)
        self.assertIn("Module 1 已接入主线", stage_doc)
        self.assertIn("Module 3 已进入主线后置动作层", stage_doc)
        self.assertIn("Module 4：", stage_doc)
        self.assertIn("当前状态是 `main.py routed optional runtime path`", stage_doc)
        self.assertIn("禁止接入 `geo_tool/geo_workflow.py`", stage_doc)
        self.assertIn("## 5. 验收最小矩阵", stage_doc)
        self.assertIn("python3 -m unittest tests.test_module4_mainline_bridge", stage_doc)
        self.assertIn("python3 -m unittest tests.test_tcga_gtex_facade", stage_doc)

    def test_canonical_workflow_imports_only_frozen_mainline_surfaces(self) -> None:
        launcher = self._read_text("geo_tool/run_geo_tool.py")
        main_window = self._read_text("geo_tool/main.py")
        workflow = self._read_text("geo_tool/geo_workflow.py")

        self.assertIn("from main import main as gui_main", launcher)
        self.assertIn("from geo_workflow import WorkflowConfig, run_download_and_process_workflow", main_window)
        self.assertIn("from tcga_gtex import resolve_tcga_gtex_files, search_tcga_gtex", main_window)
        self.assertIn("from tcga_gtex.mainline_bridge import", main_window)
        self.assertIn(
            "from geo_pipeline import ProcessConfig, download_core_geo_records, process_from_local_family_soft",
            workflow,
        )
        self.assertIn("validate_downloaded_dataset", workflow)
        self.assertIn("detect_dataset", workflow)
        self.assertIn("load_module1_dataset_context", workflow)

        for text in (launcher, main_window, workflow):
            self.assertNotIn("download_geo_full_only", text)
            self.assertNotIn("process_geo_family_soft", text)
            self.assertNotIn("download_supplement_and_sra", text)
            self.assertNotIn("geo_tool.geo_pipeline", text)

        self.assertNotIn("tcga_gtex", workflow)

    def test_module4_optional_path_is_routed_only_through_main_py_and_bridge(self) -> None:
        main_window = self._read_text("geo_tool/main.py")
        workflow = self._read_text("geo_tool/geo_workflow.py")
        bridge = self._read_text("tcga_gtex/mainline_bridge.py")

        self.assertIn("start_module4_search", main_window)
        self.assertIn("run_module4_runtime_action", main_window)
        self.assertIn("build_mainline_summary", main_window)
        self.assertIn("run_minimal_runtime", main_window)
        self.assertIn("missing_locator", bridge)
        self.assertIn("download_tcga_gtex_dataset", bridge)
        self.assertIn("build_tcga_gtex_bundle", bridge)
        self.assertIn("get_tcga_gtex_summary", bridge)
        self.assertNotIn("tcga_gtex", workflow)

    def test_wrappers_only_delegate_to_canonical_launcher(self) -> None:
        run_sh = self._read_text("geo_tool/run_geo_tool.sh")
        run_bat = self._read_text("geo_tool/run_geo_tool.bat")
        bootstrap_sh = self._read_text("geo_tool/bootstrap_geo_tool.sh")
        bootstrap_bat = self._read_text("geo_tool/bootstrap_geo_tool.bat")

        self.assertIn("geo_tool/run_geo_tool.py", run_sh)
        self.assertIn(r"geo_tool\run_geo_tool.py", run_bat)
        self.assertNotIn("geo_workflow.py", run_sh)
        self.assertNotIn("geo_workflow.py", run_bat)
        self.assertNotIn("download_geo_full_only.py", run_sh)
        self.assertNotIn("download_geo_full_only.py", run_bat)

        self.assertIn("geo_tool/requirements.txt", bootstrap_sh)
        self.assertIn(r"geo_tool\requirements.txt", bootstrap_bat)
        self.assertNotIn("geo_workflow.py", bootstrap_sh)
        self.assertNotIn("geo_workflow.py", bootstrap_bat)

    def test_compatibility_surfaces_are_marked_and_not_promoted_to_mainline(self) -> None:
        legacy_download = self._read_text("download_geo_full_only.py")
        legacy_process = self._read_text("process_geo_family_soft.py")
        legacy_supplement = self._read_text("download_supplement_and_sra.py")
        duplicate_init = self._read_text("geo_tool/geo_pipeline/__init__.py")

        self.assertIn("compatibility-only", legacy_download.lower())
        self.assertIn("compatibility-only", legacy_process.lower())
        self.assertIn("compatibility-only", legacy_supplement.lower())
        self.assertIn("duplicate compatibility surface", duplicate_init.lower())

    def test_canonical_process_surface_writes_run_summary(self) -> None:
        from geo_pipeline.process import ProcessConfig, process_from_local_family_soft

        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "GSE9100_family.soft.gz"
            input_path.write_text("placeholder", encoding="utf-8")
            expected_result = {"status": "success", "accession": "GSE9100"}

            with (
                patch("geo_pipeline.process.load_full_family_soft", return_value=object()) as load_mock,
                patch("geo_pipeline.process.process_from_gse_object", return_value=expected_result) as process_mock,
            ):
                result = process_from_local_family_soft(
                    str(input_path),
                    ProcessConfig(accession="GSE9100", outdir=tmpdir, geo_dir=tmpdir),
                )

            load_mock.assert_called_once_with(str(input_path))
            process_mock.assert_called_once()
            self.assertEqual(result, expected_result)
            self.assertEqual(
                (Path(tmpdir) / "run_summary.json").read_text(encoding="utf-8"),
                '{\n  "status": "success",\n  "accession": "GSE9100"\n}',
            )

    def test_canonical_workflow_surface_invokes_frozen_formal_calls(self) -> None:
        from geo_processing.detector.models import DatasetDetectionResult
        from geo_tool.geo_workflow import WorkflowConfig, run_download_and_process_workflow

        validation_payload = {"status": "ANALYSIS_READY", "next_action": "continue"}
        validation_result = Mock()
        validation_result.to_dict.return_value = validation_payload
        module1_handoff = {
            "dataset_info": {
                "dataset_id": "GSE9101",
                "recommended_strategy": "SERIES_MATRIX_FIRST",
                "value_type_hint": "log2",
            },
            "dataset_manifest_draft": {},
        }
        detection_result = DatasetDetectionResult(
            accession="GSE9101",
            accession_type="GSE",
            scan_root="/tmp/geo",
            has_family_soft=True,
            recommended_strategy="SERIES_MATRIX_FIRST",
            failure_reason=None,
            next_action="continue",
        )
        process_result = {
            "status": "success",
            "metadata_parse_success": True,
            "expression_matrix_success": True,
            "matrix_build_success": True,
            "matrix_build_skipped": False,
            "matrix_build_failed": False,
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            dataset_root = Path(tmpdir) / "GSE9101"
            family_soft_path = dataset_root / "raw_downloads" / "geo_downloads" / "GSE9101_family.soft.gz"
            family_soft_path.parent.mkdir(parents=True, exist_ok=True)
            family_soft_path.write_text("placeholder", encoding="utf-8")
            resolved_dataset_root = dataset_root.resolve()
            resolved_geo_dir = family_soft_path.parent.resolve()

            with (
                patch(
                    "geo_tool.geo_workflow.download_core_geo_records",
                    return_value={
                        "status": "success",
                        "dataset_root": str(resolved_dataset_root),
                        "family_soft_path": str(family_soft_path.resolve()),
                        "download_success": True,
                    },
                ) as download_mock,
                patch("geo_tool.geo_workflow.validate_downloaded_dataset", return_value=validation_result) as validate_mock,
                patch("geo_tool.geo_workflow.load_module1_dataset_context", return_value=module1_handoff) as handoff_mock,
                patch("geo_tool.geo_workflow.detect_dataset", return_value=detection_result) as detect_mock,
                patch("geo_tool.geo_workflow.process_from_local_family_soft", return_value=process_result) as process_mock,
            ):
                result = run_download_and_process_workflow(
                    WorkflowConfig(accession="GSE9101", base_dir=tmpdir)
                )

            download_mock.assert_called_once()
            validate_mock.assert_called_once_with("GSE9101", str(resolved_dataset_root))
            handoff_mock.assert_called_once_with(str(resolved_dataset_root), validation_payload=validation_payload)
            detect_mock.assert_called_once_with("GSE9101", str(resolved_geo_dir))
            process_mock.assert_called_once()
            self.assertEqual(result["status"], "success")
            self.assertEqual(result["module1_handoff"]["dataset_info"]["dataset_id"], "GSE9101")
            self.assertTrue(result["download_success"])

    def test_download_quick_paths_anchor_to_repo_root_outside_repo_cwd(self) -> None:
        code = textwrap.dedent(
            f"""
            import importlib.util
            import os
            import sys
            import types
            from pathlib import Path

            repo_root = Path({str(REPO_ROOT)!r})
            accession = "GSE999999"
            repo_quick = repo_root / f"{{accession}}.txt"
            cwd_quick = Path.cwd() / f"{{accession}}.txt"

            geo_processing_pkg = types.ModuleType("geo_processing")
            geo_processing_pkg.__path__ = [str(repo_root / "geo_processing")]
            sys.modules["geo_processing"] = geo_processing_pkg

            contracts = types.ModuleType("geo_processing.module1_contracts")
            contracts.build_download_plan_payload = lambda *args, **kwargs: {{}}
            contracts.build_download_receipt_payload = lambda *args, **kwargs: {{}}
            contracts.derive_module1_state = lambda *args, **kwargs: {{}}
            sys.modules["geo_processing.module1_contracts"] = contracts

            geo_pipeline_pkg = types.ModuleType("geo_pipeline")
            geo_pipeline_pkg.__path__ = [str(repo_root / "geo_pipeline")]
            sys.modules["geo_pipeline"] = geo_pipeline_pkg

            common_spec = importlib.util.spec_from_file_location(
                "geo_pipeline.common", repo_root / "geo_pipeline" / "common.py"
            )
            common_module = importlib.util.module_from_spec(common_spec)
            sys.modules["geo_pipeline.common"] = common_module
            common_spec.loader.exec_module(common_module)

            download_spec = importlib.util.spec_from_file_location(
                "geo_pipeline.download", repo_root / "geo_pipeline" / "download.py"
            )
            download_module = importlib.util.module_from_spec(download_spec)
            sys.modules["geo_pipeline.download"] = download_module
            download_spec.loader.exec_module(download_module)

            class GSE:
                def __init__(self):
                    self.gsms = {{}}

            captured = []
            download_module.try_get_geo = lambda accession, geo_dir, how, annotate_gpl: captured.append(str(geo_dir)) or GSE()

            repo_quick.write_text("!Series_supplementary_file = https://repo.example/value\\n", encoding="utf-8")
            cwd_quick.write_text("!Series_supplementary_file = https://cwd.example/value\\n", encoding="utf-8")
            try:
                urls = download_module._discover_series_supplementary_urls_from_quick_text(accession)
                if urls != ["https://repo.example/value"]:
                    raise SystemExit(f"unexpected_urls={{urls}}")
                download_module._load_quick_gse(accession)
                if captured != [str(repo_root)]:
                    raise SystemExit(f"unexpected_geo_dir={{captured}}")
            finally:
                if repo_quick.exists():
                    repo_quick.unlink()
                if cwd_quick.exists():
                    cwd_quick.unlink()
            """
        )

        result = subprocess.run(
            [sys.executable, "-c", code],
            cwd="/tmp",
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)


if __name__ == "__main__":
    unittest.main()
