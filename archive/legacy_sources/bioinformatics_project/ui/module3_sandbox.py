"""Standalone Module 3 sandbox window for GEO download validation and detector debugging."""

from __future__ import annotations

import json
import re
import sys
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import (
        QApplication,
        QFileDialog,
        QFrame,
        QGridLayout,
        QLabel,
        QLineEdit,
        QListWidget,
        QListWidgetItem,
        QMainWindow,
        QMessageBox,
        QPlainTextEdit,
        QPushButton,
        QSplitter,
        QVBoxLayout,
        QWidget,
    )
except ModuleNotFoundError:
    class _QtUnavailable:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            raise ModuleNotFoundError("PySide6 is required to use Module 3 sandbox UI.")

    class _QtFallback:
        Horizontal = 1
        Vertical = 2
        UserRole = 32

    Qt = _QtFallback()
    QApplication = QFileDialog = QFrame = QGridLayout = QLabel = QLineEdit = QListWidget = QListWidgetItem = QMessageBox = QPlainTextEdit = QPushButton = QSplitter = QVBoxLayout = _QtUnavailable

    class QWidget:  # type: ignore[no-redef]
        pass

    class QMainWindow:  # type: ignore[no-redef]
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            raise ModuleNotFoundError("PySide6 is required to use Module 3 sandbox UI.")

from geo_processing import detect_dataset
from geo_processing import load_module1_dataset_context
from geo_processing.download_models import DownloadValidationResult
from geo_processing.download_validator import (
    export_download_validation_report,
    inspect_download_file,
    validate_downloaded_dataset,
)
from ui.module3_sandbox_formatters import (
    build_detection_summary_text,
    build_file_detail_text,
    build_module3_asset_summary_text,
    build_validation_summary_text,
)


STANDARD_ASSET_KEYS = (
    "expression_gene",
    "sample_annotation",
    "feature_annotation",
    "dataset_manifest",
)


def workflow_result_dataset_dir(workflow_result: dict[str, Any] | None) -> str | None:
    """Resolve the dataset directory that should be opened in Module 3 after workflow completion."""
    if not isinstance(workflow_result, dict):
        return None

    download_result = workflow_result.get("download_result")
    if isinstance(download_result, dict):
        dataset_root = download_result.get("dataset_root")
        if dataset_root:
            return str(Path(dataset_root).expanduser().resolve())

    family_soft_path = workflow_result.get("family_soft_path")
    if family_soft_path:
        return str(Path(family_soft_path).expanduser().resolve().parent.parent.parent)

    return None


def _sandbox_stylesheet() -> str:
    return """
        QMainWindow, QWidget {
            background: #f3f6fb;
            color: #243041;
            font-size: 14px;
            font-family: "SF Pro Text", "PingFang SC", "Microsoft YaHei", sans-serif;
        }
        QFrame#card {
            background: #ffffff;
            border: 1px solid #d9e2f0;
            border-radius: 14px;
        }
        QLabel#title {
            font-size: 24px;
            font-weight: 700;
            color: #111827;
        }
        QLabel#muted {
            color: #6b7280;
        }
        QLabel#sectionTitle {
            font-size: 18px;
            font-weight: 700;
            color: #1f2937;
        }
        QLineEdit, QPlainTextEdit, QListWidget {
            background: #ffffff;
            border: 1px solid #d7dfeb;
            border-radius: 10px;
            padding: 7px 9px;
        }
        QPushButton {
            background: #edf2f7;
            color: #243041;
            border: 1px solid #d5e0ec;
            border-radius: 10px;
            padding: 8px 12px;
            font-weight: 600;
        }
        QPushButton#primary {
            background: #315f9e;
            color: #ffffff;
            border: 1px solid #315f9e;
        }
        QPushButton#danger {
            background: #9f3a35;
            color: #ffffff;
            border: 1px solid #9f3a35;
        }
        QListWidget::item:selected {
            background: #dbe7f7;
            color: #111827;
        }
    """


def guess_gse_id(selected_dir: str) -> str:
    """Guess GSE accession from input path."""
    match = re.search(r"(GSE\d+)", selected_dir, flags=re.IGNORECASE)
    return match.group(1).upper() if match else Path(selected_dir).name


def _build_handoff_asset_reason_codes(module1_context: dict[str, Any] | None) -> dict[str, Any]:
    standard_assets = module1_context.get("standard_assets", {}) if isinstance(module1_context, dict) else {}
    if not isinstance(standard_assets, dict):
        standard_assets = {}
    return {
        asset_key: (
            standard_assets.get(asset_key, {}).get("reason_code")
            if isinstance(standard_assets.get(asset_key), dict)
            else None
        )
        for asset_key in STANDARD_ASSET_KEYS
    }


def build_sandbox_summary(
    *,
    gse_id: str,
    selected_dir: str,
    validation_result: DownloadValidationResult | None,
    detection_result: Any = None,
    module1_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    handoff_standard_assets = module1_context.get("standard_assets") if module1_context else {}
    return {
        "gse_id": gse_id,
        "selected_dir": str(Path(selected_dir).expanduser().resolve()),
        "validation_status": validation_result.status if validation_result else None,
        "validation_failure_stage": validation_result.failure_stage if validation_result else None,
        "handoff_recommended_strategy": module1_context.get("recommended_strategy") if module1_context else None,
        "handoff_available_capabilities": module1_context.get("available_capabilities") if module1_context else [],
        "handoff_missing_required_assets": module1_context.get("missing_required_assets") if module1_context else [],
        "handoff_standard_assets": handoff_standard_assets if isinstance(handoff_standard_assets, dict) else {},
        "handoff_asset_reason_codes": _build_handoff_asset_reason_codes(module1_context),
        "handoff_present_assets": module1_context.get("present_assets") if module1_context else [],
        "handoff_planned_assets": module1_context.get("planned_assets") if module1_context else [],
        "recommended_strategy": getattr(detection_result, "recommended_strategy", None),
        "detection_failure_stage": getattr(detection_result, "failure_stage", None),
        "conflicts": getattr(detection_result, "conflicts", []),
        "top_problem_summary": getattr(detection_result, "top_problem_summary", None)
        or (validation_result.top_problem_summary if validation_result else None),
        "suggested_next_fix": getattr(detection_result, "suggested_next_fix", None)
        or (validation_result.suggested_next_fix if validation_result else None),
        "warnings_count": len(validation_result.warnings) if validation_result else 0,
        "error_count": len(validation_result.errors) if validation_result else 0,
        "timestamp": datetime.now().isoformat(timespec="seconds"),
    }


class Module3SandboxWindow(QMainWindow):
    """Independent window for download validation and module 3 detection debugging."""

    def __init__(self, initial_dir: str = "", parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("模块3测试台 / Module 3 Sandbox")
        self.setMinimumSize(1240, 860)
        self.setStyleSheet(_sandbox_stylesheet())

        self.validation_result: Optional[DownloadValidationResult] = None
        self.detection_result: Optional[Any] = None
        self.module1_context: Optional[dict[str, Any]] = None
        self.file_details_cache: dict[str, dict[str, Any]] = {}

        self._build_ui()
        if initial_dir:
            self.dir_input.setText(initial_dir)
            self.gse_input.setText(guess_gse_id(initial_dir))

    def _card(self, title: str, description: str = "") -> tuple[QFrame, QVBoxLayout]:
        frame = QFrame()
        frame.setObjectName("card")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        title_label = QLabel(title)
        title_label.setObjectName("sectionTitle")
        layout.addWidget(title_label)
        if description:
            desc = QLabel(description)
            desc.setObjectName("muted")
            desc.setWordWrap(True)
            layout.addWidget(desc)
        return frame, layout

    def _build_ui(self) -> None:
        root = QWidget()
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(14, 12, 14, 12)
        root_layout.setSpacing(10)

        header, header_layout = self._card("模块3测试台", "独立执行下载验收与模块3识别，不触发正式分析流程。")
        title = QLabel("Module 3 Sandbox")
        title.setObjectName("title")
        subtitle = QLabel("选择一个已下载目录，先做下载验收，再做 detector 识别、候选文件预览和报告导出。")
        subtitle.setObjectName("muted")
        subtitle.setWordWrap(True)
        header_layout.insertWidget(0, title)
        header_layout.insertWidget(1, subtitle)
        root_layout.addWidget(header)

        content_splitter = QSplitter(Qt.Horizontal)

        left_card, left_layout = self._card("输入与操作")
        grid = QGridLayout()
        self.gse_input = QLineEdit()
        self.gse_input.setPlaceholderText("可选；留空时从目录名自动猜测")
        self.dir_input = QLineEdit()
        self.dir_input.setPlaceholderText("选择已下载数据集目录")
        browse_btn = QPushButton("浏览")
        browse_btn.clicked.connect(self.choose_directory)
        grid.addWidget(QLabel("GSE 编号"), 0, 0)
        grid.addWidget(self.gse_input, 0, 1, 1, 2)
        grid.addWidget(QLabel("目录"), 1, 0)
        grid.addWidget(self.dir_input, 1, 1)
        grid.addWidget(browse_btn, 1, 2)
        left_layout.addLayout(grid)

        self.validation_btn = QPushButton("运行下载验收")
        self.validation_btn.setObjectName("primary")
        self.validation_btn.clicked.connect(self.run_validation)
        self.detect_btn = QPushButton("运行模块3识别")
        self.detect_btn.clicked.connect(self.run_detection)
        self.detect_btn.setEnabled(False)
        self.export_btn = QPushButton("导出报告")
        self.export_btn.clicked.connect(self.export_reports)
        self.export_btn.setEnabled(False)
        self.reset_btn = QPushButton("刷新/重置")
        self.reset_btn.clicked.connect(self.reset_view)

        for button in [self.validation_btn, self.detect_btn, self.export_btn, self.reset_btn]:
            left_layout.addWidget(button)
        left_layout.addStretch(1)

        right_splitter = QSplitter(Qt.Vertical)

        validation_card, validation_layout = self._card("下载验收摘要")
        self.validation_summary_box = QPlainTextEdit()
        self.validation_summary_box.setReadOnly(True)
        self.validation_summary_box.setPlaceholderText("这里显示 DownloadValidationResult 摘要。")
        validation_layout.addWidget(self.validation_summary_box)

        detection_card, detection_layout = self._card("模块3识别结果")
        self.detection_summary_box = QPlainTextEdit()
        self.detection_summary_box.setReadOnly(True)
        self.detection_summary_box.setPlaceholderText("这里显示 detect_dataset(...) 结果。")
        detection_layout.addWidget(self.detection_summary_box)

        preview_card, preview_layout = self._card("文件详情 / 预览")
        preview_splitter = QSplitter(Qt.Horizontal)
        self.file_list = QListWidget()
        self.file_list.itemSelectionChanged.connect(self.render_selected_file)
        self.file_detail_box = QPlainTextEdit()
        self.file_detail_box.setReadOnly(True)
        self.file_detail_box.setPlaceholderText("点击候选文件后，这里显示路径、类型判断、预览和解释。")
        preview_splitter.addWidget(self.file_list)
        preview_splitter.addWidget(self.file_detail_box)
        preview_splitter.setStretchFactor(0, 2)
        preview_splitter.setStretchFactor(1, 5)
        preview_layout.addWidget(preview_splitter)

        right_splitter.addWidget(validation_card)
        right_splitter.addWidget(detection_card)
        right_splitter.addWidget(preview_card)
        right_splitter.setStretchFactor(0, 2)
        right_splitter.setStretchFactor(1, 2)
        right_splitter.setStretchFactor(2, 3)

        content_splitter.addWidget(left_card)
        content_splitter.addWidget(right_splitter)
        content_splitter.setStretchFactor(0, 1)
        content_splitter.setStretchFactor(1, 3)
        content_splitter.setSizes([320, 920])
        root_layout.addWidget(content_splitter)

        self.statusBar().showMessage("就绪")
        self.setCentralWidget(root)

    def _selected_dir(self) -> str:
        return self.dir_input.text().strip()

    def _selected_gse(self) -> str:
        return (self.gse_input.text().strip() or guess_gse_id(self._selected_dir())).strip()

    def choose_directory(self) -> None:
        selected = QFileDialog.getExistingDirectory(self, "选择已下载数据集目录")
        if not selected:
            return
        self.dir_input.setText(selected)
        if not self.gse_input.text().strip():
            self.gse_input.setText(guess_gse_id(selected))
        self.statusBar().showMessage(f"已选择目录：{selected}", 4000)

    def reset_view(self) -> None:
        self.validation_result = None
        self.detection_result = None
        self.module1_context = None
        self.file_details_cache.clear()
        self.validation_summary_box.clear()
        self.detection_summary_box.clear()
        self.file_detail_box.clear()
        self.file_list.clear()
        self.detect_btn.setEnabled(False)
        self.export_btn.setEnabled(False)
        self.statusBar().showMessage("已重置测试台", 3000)

    def run_validation(self) -> None:
        selected_dir = self._selected_dir()
        if not selected_dir:
            QMessageBox.information(self, "提示", "请先选择已下载目录。")
            return
        try:
            gse_id = self._selected_gse()
            self.gse_input.setText(gse_id)
            self.validation_result = validate_downloaded_dataset(gse_id=gse_id, download_dir=selected_dir)
            self.module1_context = load_module1_dataset_context(selected_dir, validation_payload=self.validation_result.to_dict())
            self.render_validation()
            self.populate_file_list()
            self.export_btn.setEnabled(True)
            self.detect_btn.setEnabled(
                self.validation_result.status in {
                    "ANALYSIS_READY",
                    "PARTIAL_BUT_USABLE",
                    "EXPRESSION_ONLY",
                    "METADATA_ONLY",
                    "RAW_ONLY",
                    "NO_EXPRESSION_PAYLOAD",
                }
            )
            if self.validation_result.status == "EMPTY_OR_BROKEN":
                self.statusBar().showMessage("下载验收提示目录为空壳或损坏，不建议继续进入模块3。", 6000)
            else:
                self.statusBar().showMessage("下载验收完成，可按需继续运行模块3识别。", 5000)
        except Exception as exc:
            QMessageBox.warning(self, "下载验收失败", str(exc))
            self.statusBar().showMessage(f"下载验收失败：{exc}", 5000)

    def run_detection(self) -> None:
        selected_dir = self._selected_dir()
        if not selected_dir:
            QMessageBox.information(self, "提示", "请先选择目录。")
            return
        if self.validation_result is None:
            QMessageBox.information(self, "提示", "请先运行下载验收。")
            return
        if self.validation_result.status == "EMPTY_OR_BROKEN":
            QMessageBox.warning(self, "不建议继续", "当前目录被判定为 EMPTY_OR_BROKEN，不建议进入模块3识别。")
            return
        try:
            self.detection_result = detect_dataset(accession=self._selected_gse(), root_dir=selected_dir)
            self.render_detection()
            self.populate_file_list()
            self.export_btn.setEnabled(True)
            self.statusBar().showMessage("模块3识别完成。", 4000)
        except Exception as exc:
            QMessageBox.warning(self, "模块3识别失败", str(exc))
            self.statusBar().showMessage(f"模块3识别失败：{exc}", 5000)

    def render_validation(self) -> None:
        if self.validation_result is None:
            return
        handoff = self.module1_context or {}
        extra = []
        if handoff:
            extra.extend(
                [
                    "",
                    "module1_handoff:",
                    f"asset_role_counts: {handoff.get('asset_role_counts')}",
                    f"preferred_expression_asset: {handoff.get('preferred_expression_asset', {})}",
                    f"preferred_metadata_asset: {handoff.get('preferred_metadata_asset', {})}",
                    f"preferred_feature_annotation_asset: {handoff.get('preferred_feature_annotation_asset', {})}",
                    f"preferred_clinical_asset: {handoff.get('preferred_clinical_asset', {})}",
                    f"preferred_mutation_asset: {handoff.get('preferred_mutation_asset', {})}",
                    f"warnings_summary: {handoff.get('warnings_summary')}",
                    "",
                    build_module3_asset_summary_text(handoff),
                ]
            )
        self.validation_summary_box.setPlainText(build_validation_summary_text(self.validation_result) + ("\n".join(extra) if extra else ""))

    def render_detection(self) -> None:
        if self.detection_result is None:
            return
        self.detection_summary_box.setPlainText(build_detection_summary_text(self.detection_result))

    def populate_file_list(self) -> None:
        self.file_list.clear()
        seen: dict[str, str] = {}
        if self.module1_context is not None:
            for item in self.module1_context.get("file_inventory", []):
                relative_path = str(item.get("relative_path") or "")
                if relative_path:
                    seen.setdefault(relative_path, f"handoff.{item.get('file_role', 'unknown')}")
        if self.validation_result is not None:
            for relative_path in self.validation_result.candidate_matrix_files:
                seen.setdefault(relative_path, "validation.matrix")
            for relative_path in self.validation_result.candidate_metadata_files:
                seen.setdefault(relative_path, "validation.metadata")
            for relative_path in self.validation_result.candidate_clinical_files:
                seen.setdefault(relative_path, "validation.clinical")
            for relative_path in self.validation_result.raw_files:
                seen.setdefault(relative_path, "validation.raw")
            for relative_path in self.validation_result.archive_files:
                seen.setdefault(relative_path, "validation.archive")
            for relative_path in self.validation_result.platform_annotation_files:
                seen.setdefault(relative_path, "validation.platform")
            for relative_path in self.validation_result.supporting_files:
                seen.setdefault(relative_path, "validation.supporting")
            for relative_path in self.validation_result.broken_files:
                seen.setdefault(relative_path, "validation.broken")
        if self.detection_result is not None:
            for relative_path in self.detection_result.candidate_expression_files:
                seen.setdefault(relative_path, "detector.expression")
            for relative_path in self.detection_result.candidate_metadata_files:
                seen.setdefault(relative_path, "detector.metadata")
            for relative_path in getattr(self.detection_result, "candidate_clinical_files", []):
                seen.setdefault(relative_path, "detector.clinical")
            for relative_path in self.detection_result.candidate_annotation_files:
                seen.setdefault(relative_path, "detector.annotation")
            for relative_path in self.detection_result.raw_files:
                seen.setdefault(relative_path, "detector.raw")
            for relative_path in getattr(self.detection_result, "archive_files", []):
                seen.setdefault(relative_path, "detector.archive")

        for relative_path, source in seen.items():
            item = QListWidgetItem(f"[{source}] {relative_path}")
            item.setData(Qt.UserRole, relative_path)
            self.file_list.addItem(item)

    def render_selected_file(self) -> None:
        item = self.file_list.currentItem()
        if item is None:
            return
        relative_path = item.data(Qt.UserRole)
        selected_dir = Path(self._selected_dir()).expanduser().resolve()
        target = selected_dir / relative_path
        if relative_path in self.file_details_cache:
            detail = self.file_details_cache[relative_path]
        else:
            detail = inspect_download_file(str(target))
            detail["relative_path"] = relative_path
            detail["path"] = str(target)
            self.file_details_cache[relative_path] = detail

        detector_reasons: list[str] = []
        if self.detection_result is not None:
            if relative_path in getattr(self.detection_result, "candidate_expression_files", []):
                detector_reasons.append("模块3将该文件列为 candidate_expression_files")
            if relative_path in getattr(self.detection_result, "candidate_metadata_files", []):
                detector_reasons.append("模块3将该文件列为 candidate_metadata_files")
            if relative_path in getattr(self.detection_result, "candidate_annotation_files", []):
                detector_reasons.append("模块3将该文件列为 candidate_annotation_files")
            if relative_path in getattr(self.detection_result, "candidate_clinical_files", []):
                detector_reasons.append("模块3将该文件列为 candidate_clinical_files")
            if relative_path in getattr(self.detection_result, "raw_files", []):
                detector_reasons.append("模块3将该文件列为 raw_files")
            if relative_path in getattr(self.detection_result, "archive_files", []):
                detector_reasons.append("模块3将该文件列为 archive_files")

        self.file_detail_box.setPlainText(build_file_detail_text(detail, detector_reasons))

    def export_reports(self) -> None:
        selected_dir = self._selected_dir()
        if not selected_dir:
            QMessageBox.information(self, "提示", "请先选择目录。")
            return
        export_dir = QFileDialog.getExistingDirectory(self, "选择报告导出目录", selected_dir) or selected_dir
        export_root = Path(export_dir).expanduser().resolve()
        try:
            if self.validation_result is not None:
                export_download_validation_report(
                    self.validation_result,
                    str(export_root / "download_validation.json"),
                )
            if self.detection_result is not None:
                with (export_root / "module3_detection.json").open("w", encoding="utf-8") as handle:
                    json.dump(asdict(self.detection_result), handle, ensure_ascii=False, indent=2)
            summary = build_sandbox_summary(
                gse_id=self._selected_gse(),
                selected_dir=selected_dir,
                validation_result=self.validation_result,
                detection_result=self.detection_result,
                module1_context=self.module1_context,
            )
            with (export_root / "sandbox_summary.json").open("w", encoding="utf-8") as handle:
                json.dump(summary, handle, ensure_ascii=False, indent=2)
            self.statusBar().showMessage(f"报告已导出到：{export_root}", 5000)
        except Exception as exc:
            QMessageBox.warning(self, "导出失败", str(exc))
            self.statusBar().showMessage(f"导出失败：{exc}", 5000)


def open_module3_sandbox(initial_dir: str = "") -> Module3SandboxWindow:
    """Convenience entrypoint used by the main GUI."""
    window = Module3SandboxWindow(initial_dir=initial_dir)
    window.show()
    return window


def main() -> int:
    app = QApplication.instance() or QApplication(sys.argv)
    window = Module3SandboxWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
