from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from PySide6.QtWidgets import QFrame, QGridLayout, QHBoxLayout, QLabel, QPlainTextEdit, QPushButton, QVBoxLayout, QWidget

from app.shared.ai_gateway import DEFAULT_LOCAL_OLLAMA_ROLE_MODEL_MAPPING, desktop_local_ollama_config, load_ai_gateway_config
from app.shared.local_engines import (
    ENGINE_STATUS_AVAILABLE,
    ENGINE_STATUS_FAILED,
    ENGINE_STATUS_NOT_CONFIGURED,
    PYTHON_STATISTICAL_ENGINE_FAMILY,
    REPORT_RENDERER_ENGINE_FAMILY,
    R_BIOCONDUCTOR_ENGINE_FAMILY,
    ExternalEngineRegistry,
    IMAGEJ_FIJI_ENGINE_ID,
    ImageJFijiBridge,
    OllamaLLMPreflightResult,
    default_ollama_llm_runtime_manifest_path,
    detect_all_external_dependencies,
    load_external_engine_registry,
    load_ollama_llm_runtime_manifest,
    ollama_model_role_registry,
    run_ollama_llm_preflight,
)
from app.shared.local_engines.engine_status import EngineStatus
from app.shared.local_engines.ollama_llm_manifest import OllamaLLMRuntimeManifest
from app.shared.local_engines.ollama_llm_registry import OLLAMA_LLM_ENGINE_ID, OLLAMA_LLM_HTTP_ENDPOINT
from app.ui_style_tokens import COLORS, FONT_SIZE, RADIUS, SPACING


@dataclass(frozen=True)
class ExternalEngineCardState:
    engine_family: str
    display_name: str
    status: str
    last_checked: str
    summary: str


PreflightRunner = Callable[..., OllamaLLMPreflightResult]
DependencyDetector = Callable[..., ExternalEngineRegistry]

_DEPENDENCY_ENGINE_FAMILIES = (
    R_BIOCONDUCTOR_ENGINE_FAMILY,
    PYTHON_STATISTICAL_ENGINE_FAMILY,
    REPORT_RENDERER_ENGINE_FAMILY,
)


class ExternalEngineManagerPage(QWidget):
    def __init__(
        self,
        *,
        manifest_path: str | Path | None = None,
        ai_gateway_config_path: str | Path | None = None,
        preflight_runner: PreflightRunner = run_ollama_llm_preflight,
        imagej_bridge: ImageJFijiBridge | None = None,
        dependency_storage_root: str | Path | None = None,
        dependency_detector: DependencyDetector = detect_all_external_dependencies,
    ) -> None:
        super().__init__()
        self.setObjectName("externalEngineManagerPage")
        self._manifest_path = Path(manifest_path) if manifest_path is not None else default_ollama_llm_runtime_manifest_path()
        self._ai_gateway_config_path = Path(ai_gateway_config_path) if ai_gateway_config_path is not None else None
        self._preflight_runner = preflight_runner
        self._imagej_bridge = imagej_bridge or ImageJFijiBridge()
        self._dependency_storage_root = Path(dependency_storage_root) if dependency_storage_root is not None else None
        self._dependency_detector = dependency_detector
        self._latest_manifest: OllamaLLMRuntimeManifest | None = None
        self._latest_dependency_registry: ExternalEngineRegistry | None = None
        self._build_ui()
        self.refresh()

    def refresh(self) -> None:
        manifest = self._load_manifest_or_none()
        registry = self._load_dependency_registry()
        self._latest_manifest = manifest
        self._latest_dependency_registry = registry
        self._render_engine_cards(manifest, registry)
        self._render_ollama_detail(manifest)
        self._render_dependency_detail(registry)

    def run_ollama_check(self) -> None:
        try:
            result = self._preflight_runner(
                manifest_path=self._manifest_path,
                write_manifest=True,
                run_smoke=True,
            )
        except Exception as exc:
            manifest = self._load_manifest_or_none()
            registry = self._latest_dependency_registry or self._load_dependency_registry()
            self._latest_manifest = manifest
            self._render_engine_cards(manifest, registry)
            self._detail_text.setPlainText(f"local_llm_ollama 检查失败：{exc.__class__.__name__}")
            self._manifest_text.setPlainText("检查失败；未写入 AI Gateway 配置，也不会自动安装或 pull 模型。")
            return
        self._latest_manifest = result.manifest
        registry = self._latest_dependency_registry or self._load_dependency_registry()
        self._render_engine_cards(result.manifest, registry)
        self._render_ollama_detail(result.manifest)

    def run_dependency_detection(self) -> None:
        try:
            registry = self._dependency_detector(storage_root=self._dependency_storage_root, write_snapshots=True)
        except Exception as exc:
            registry = self._latest_dependency_registry or self._load_dependency_registry()
            self._dependency_detail_text.setPlainText(f"外部依赖检测失败：{exc.__class__.__name__}")
            self._dependency_registry_text.setPlainText("检测失败；未声明任何 DEG / Cox / report 业务能力完成。")
            self._render_engine_cards(self._latest_manifest, registry)
            return
        self._latest_dependency_registry = registry
        self._render_engine_cards(self._latest_manifest, registry)
        self._render_dependency_detail(registry)

    def show_dependency_registry_summary(self) -> None:
        registry = self._latest_dependency_registry or self._load_dependency_registry()
        self._dependency_registry_text.setPlainText(json.dumps(registry.to_dict(), ensure_ascii=False, indent=2, sort_keys=True))

    def show_manifest_summary(self) -> None:
        manifest = self._latest_manifest or self._load_manifest_or_none()
        if manifest is None:
            self._manifest_text.setPlainText("尚未生成 runtime manifest。请先运行检查。")
            return
        self._manifest_text.setPlainText(json.dumps(_manifest_summary(manifest), ensure_ascii=False, indent=2, sort_keys=True))

    def generate_ai_gateway_config_draft(self) -> dict[str, object]:
        config = desktop_local_ollama_config(
            enabled=True,
            base_url=OLLAMA_LLM_HTTP_ENDPOINT,
            default_model=DEFAULT_LOCAL_OLLAMA_ROLE_MODEL_MAPPING["medical"],
            role_model_mapping=DEFAULT_LOCAL_OLLAMA_ROLE_MODEL_MAPPING,
        )
        payload = {
            "default_provider": config.default_provider,
            "allow_network": config.allow_network,
            "allow_external_model": config.allow_external_model,
            "allow_sensitive_upload": config.allow_sensitive_upload,
            "store_raw_prompts": config.store_raw_prompts,
            "store_raw_responses": config.store_raw_responses,
            "role_model_mapping": dict(config.role_model_mapping),
            "provider_configs": dict(config.provider_configs),
            "note": "配置草案未自动写入。用户明确保存后才会启用本地 Ollama。",
        }
        self._manifest_text.setPlainText(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
        self._gateway_status_label.setText(self._ai_gateway_status_text())
        return payload

    def card_states(self) -> tuple[ExternalEngineCardState, ...]:
        manifest = self._latest_manifest or self._load_manifest_or_none()
        registry = self._latest_dependency_registry or self._load_dependency_registry()
        return (
            _ollama_card_state(manifest),
            self._imagej_card_state(),
            *_dependency_card_states(registry),
        )

    def _build_ui(self) -> None:
        self.setStyleSheet(self._stylesheet())
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(SPACING["md"])

        title = QLabel("外部引擎 / 本地引擎与模型")
        title.setObjectName("externalEngineTitle")
        subtitle = QLabel("本地模型默认关闭。启用后仅用于生成草稿或辅助文本，正式结果仍需用户确认。模型文件较大，缺失模型不会自动下载。")
        subtitle.setObjectName("externalEngineSubtitle")
        subtitle.setWordWrap(True)
        root.addWidget(title)
        root.addWidget(subtitle)

        self._card_grid = QGridLayout()
        self._card_grid.setSpacing(SPACING["md"])
        root.addLayout(self._card_grid)

        detail = QFrame()
        detail.setObjectName("externalEngineDetailCard")
        detail_layout = QVBoxLayout(detail)
        detail_layout.setContentsMargins(SPACING["md"], SPACING["md"], SPACING["md"], SPACING["md"])
        detail_layout.setSpacing(SPACING["sm"])
        detail_title = QLabel("local_llm_ollama 详情")
        detail_title.setObjectName("externalEngineCardTitle")
        detail_layout.addWidget(detail_title)
        self._detail_text = QPlainTextEdit()
        self._detail_text.setObjectName("ollamaLLMDetailText")
        self._detail_text.setReadOnly(True)
        self._detail_text.setMinimumHeight(220)
        detail_layout.addWidget(self._detail_text)

        actions = QHBoxLayout()
        self._run_check_button = QPushButton("运行检查")
        self._run_check_button.setObjectName("runOllamaPreflightButton")
        self._run_check_button.clicked.connect(self.run_ollama_check)
        self._manifest_button = QPushButton("查看 manifest 摘要")
        self._manifest_button.setObjectName("showOllamaManifestSummaryButton")
        self._manifest_button.clicked.connect(self.show_manifest_summary)
        self._draft_button = QPushButton("生成本地模型配置草案")
        self._draft_button.setObjectName("generateLocalModelConfigDraftButton")
        self._draft_button.clicked.connect(self.generate_ai_gateway_config_draft)
        for button in (self._run_check_button, self._manifest_button, self._draft_button):
            actions.addWidget(button)
        actions.addStretch(1)
        detail_layout.addLayout(actions)

        self._gateway_status_label = QLabel()
        self._gateway_status_label.setObjectName("aiGatewayProviderStatusLabel")
        self._gateway_status_label.setWordWrap(True)
        detail_layout.addWidget(self._gateway_status_label)

        self._manifest_text = QPlainTextEdit()
        self._manifest_text.setObjectName("ollamaManifestSummaryText")
        self._manifest_text.setReadOnly(True)
        self._manifest_text.setMinimumHeight(150)
        detail_layout.addWidget(self._manifest_text)
        root.addWidget(detail)

        dependency_detail = QFrame()
        dependency_detail.setObjectName("externalEngineDetailCard")
        dependency_layout = QVBoxLayout(dependency_detail)
        dependency_layout.setContentsMargins(SPACING["md"], SPACING["md"], SPACING["md"], SPACING["md"])
        dependency_layout.setSpacing(SPACING["sm"])
        dependency_title = QLabel("R / Python / 报告渲染依赖")
        dependency_title.setObjectName("externalEngineCardTitle")
        dependency_layout.addWidget(dependency_title)
        self._dependency_detail_text = QPlainTextEdit()
        self._dependency_detail_text.setObjectName("externalDependencyDetailText")
        self._dependency_detail_text.setReadOnly(True)
        self._dependency_detail_text.setMinimumHeight(190)
        dependency_layout.addWidget(self._dependency_detail_text)

        dependency_actions = QHBoxLayout()
        self._run_dependency_check_button = QPushButton("重新检测依赖")
        self._run_dependency_check_button.setObjectName("runExternalDependencyDetectionButton")
        self._run_dependency_check_button.clicked.connect(self.run_dependency_detection)
        self._dependency_registry_button = QPushButton("查看 capability registry")
        self._dependency_registry_button.setObjectName("showExternalDependencyRegistryButton")
        self._dependency_registry_button.clicked.connect(self.show_dependency_registry_summary)
        for button in (self._run_dependency_check_button, self._dependency_registry_button):
            dependency_actions.addWidget(button)
        dependency_actions.addStretch(1)
        dependency_layout.addLayout(dependency_actions)

        self._dependency_registry_text = QPlainTextEdit()
        self._dependency_registry_text.setObjectName("externalDependencyRegistryText")
        self._dependency_registry_text.setReadOnly(True)
        self._dependency_registry_text.setMinimumHeight(150)
        dependency_layout.addWidget(self._dependency_registry_text)
        root.addWidget(dependency_detail)

    def _render_engine_cards(self, manifest: OllamaLLMRuntimeManifest | None, registry: ExternalEngineRegistry | None = None) -> None:
        _clear_layout(self._card_grid)
        states = (_ollama_card_state(manifest), self._imagej_card_state(), *_dependency_card_states(registry))
        for index, state in enumerate(states):
            action_text = "运行检查" if state.engine_family == OLLAMA_LLM_ENGINE_ID else ("重新检测依赖" if state.engine_family in _DEPENDENCY_ENGINE_FAMILIES else "只读状态")
            self._card_grid.addWidget(_engine_card(state, action_text=action_text), index // 3, index % 3)

    def _render_ollama_detail(self, manifest: OllamaLLMRuntimeManifest | None) -> None:
        self._gateway_status_label.setText(self._ai_gateway_status_text())
        if manifest is None:
            self._detail_text.setPlainText(
                "\n".join(
                    (
                        "状态：尚未检查。",
                        f"runtime manifest：{self._manifest_path}",
                        "请点击“运行检查”检测本机 Ollama、HTTP 服务和模型 role。",
                        "不会自动安装 Ollama，不会自动 pull 大模型。",
                    )
                )
            )
            self._manifest_text.setPlainText("尚未生成 runtime manifest。")
            return
        lines = [
            f"Ollama command path：{manifest.ollama_command_path or '未检测到'}",
            f"Ollama version：{manifest.ollama_version or 'unknown'}",
            f"HTTP service available：{manifest.service_available}",
            f"endpoint：{manifest.http_endpoint}",
            f"runtime manifest：{self._manifest_path}",
            f"privacy mode：{manifest.privacy_mode}",
            f"last checked：{manifest.detected_at or '未记录'}",
            "",
            "installed models：",
            *[f"- {model.name} | size={model.size or 'unknown'} | modified={model.modified_at or 'unknown'}" for model in manifest.installed_models],
            "",
            "missing models：",
            *([f"- {model}" for model in manifest.missing_models] or ["- 无"]),
            "",
            "role registry：",
            *[f"- {role.role_id} -> {role.default_model} | {role.display_name}" for role in ollama_model_role_registry()],
            "",
            "smoke results：",
            *[f"- {result.role_id} / {result.model_name}: {result.status}{' | ' + result.error_summary if result.error_summary else ''}" for result in manifest.smoke_results],
            "",
            "notes / warnings：",
            *([f"- {item}" for item in [*manifest.notes, *manifest.warnings]] or ["- 无"]),
        ]
        self._detail_text.setPlainText("\n".join(lines))
        self._manifest_text.setPlainText("点击“查看 manifest 摘要”显示简化 JSON。")

    def _render_dependency_detail(self, registry: ExternalEngineRegistry | None) -> None:
        registry = registry or self._load_dependency_registry()
        capabilities = registry.capabilities
        if not capabilities:
            self._dependency_detail_text.setPlainText(
                "\n".join(
                    (
                        "状态：尚未检测。",
                        "点击“重新检测依赖”生成 R / Python / renderer dependency snapshot。",
                        "本页只显示依赖可用性，不显示 limma、DESeq2、edgeR、Cox 或报告业务已完成。",
                    )
                )
            )
            self._dependency_registry_text.setPlainText("尚未生成 capability registry snapshot。")
            return
        lines = ["dependency snapshots："]
        for family in _DEPENDENCY_ENGINE_FAMILIES:
            snapshot = registry.query_engine_family(family) or {}
            lines.append(f"- {family}: {snapshot.get('status', 'unknown')} | checked_at={snapshot.get('checked_at', '')} | snapshot={snapshot.get('snapshot_path', '')}")
        lines.extend(("", "capability status："))
        for key in sorted(capabilities):
            row = capabilities[key]
            blockers = row.get("blockers") if isinstance(row.get("blockers"), list) else []
            blocker_codes = ",".join(str(item.get("code")) for item in blockers if isinstance(item, dict)) or "none"
            lines.append(f"- {key}: {row.get('status', 'unknown')} | version={row.get('version', '') or '-'} | blockers={blocker_codes}")
        lines.extend(("", "boundary：dependency detection only；no formal DEG / Cox / report execution is declared here."))
        self._dependency_detail_text.setPlainText("\n".join(lines))
        self._dependency_registry_text.setPlainText("点击“查看 capability registry”显示统一 JSON。")

    def _load_manifest_or_none(self) -> OllamaLLMRuntimeManifest | None:
        try:
            return load_ollama_llm_runtime_manifest(self._manifest_path)
        except ValueError:
            return None

    def _load_dependency_registry(self) -> ExternalEngineRegistry:
        return load_external_engine_registry(self._dependency_storage_root)

    def _imagej_card_state(self) -> ExternalEngineCardState:
        try:
            config = self._imagej_bridge.load_config()
        except ValueError:
            return ExternalEngineCardState(IMAGEJ_FIJI_ENGINE_ID, "ImageJ / Fiji 图像引擎", "not_configured", "", "只读配置读取失败。")
        status: EngineStatus | None = config.last_status
        if status is None:
            if config.configured_path_or_endpoint:
                return ExternalEngineCardState(IMAGEJ_FIJI_ENGINE_ID, "ImageJ / Fiji 图像引擎", "not_configured", "", "已配置路径，但尚未在本页运行检测。")
            return ExternalEngineCardState(IMAGEJ_FIJI_ENGINE_ID, "ImageJ / Fiji 图像引擎", "not_configured", "", "shared 检测逻辑已存在；本页第一版仅只读展示。")
        return ExternalEngineCardState(
            IMAGEJ_FIJI_ENGINE_ID,
            "ImageJ / Fiji 图像引擎",
            _engine_status_label(status.status),
            status.last_check_at,
            status.last_error or status.smoke_test_result or status.configured_path_or_endpoint or "只读状态。",
        )

    def _ai_gateway_status_text(self) -> str:
        config = load_ai_gateway_config(self._ai_gateway_config_path)
        mapping = dict(getattr(config, "role_model_mapping", {}) or {})
        mapping_text = ", ".join(f"{key}->{value}" for key, value in mapping.items()) if mapping else "未配置"
        return (
            f"AI Gateway 当前 provider：{config.default_provider}；"
            f"allow_network={config.allow_network}；role_model_mapping：{mapping_text}。"
        )

    def _stylesheet(self) -> str:
        return f"""
        QWidget#externalEngineManagerPage {{
            background: transparent;
            color: {COLORS["text"]};
            font-size: {FONT_SIZE["body"]}px;
        }}
        QLabel#externalEngineTitle {{
            color: {COLORS["bio"]};
            font-size: 22px;
            font-weight: 760;
        }}
        QLabel#externalEngineSubtitle {{
            color: {COLORS["muted"]};
        }}
        QFrame#externalEngineCard, QFrame#externalEngineDetailCard {{
            background: {COLORS["surface"]};
            border: 1px solid {COLORS["border"]};
            border-radius: {RADIUS["sm"]}px;
        }}
        QLabel#externalEngineCardTitle {{
            color: {COLORS["bio"]};
            font-size: {FONT_SIZE["card_title"]}px;
            font-weight: 720;
        }}
        QLabel#externalEngineCardStatus {{
            color: {COLORS["text"]};
            font-weight: 700;
        }}
        QLabel#externalEngineCardSummary, QLabel#aiGatewayProviderStatusLabel {{
            color: {COLORS["muted"]};
        }}
        QPlainTextEdit#ollamaLLMDetailText, QPlainTextEdit#ollamaManifestSummaryText, QPlainTextEdit#externalDependencyDetailText, QPlainTextEdit#externalDependencyRegistryText {{
            background: {COLORS["background"]};
            border: 1px solid {COLORS["border"]};
            border-radius: {RADIUS["sm"]}px;
            padding: 8px;
        }}
        """


def _ollama_card_state(manifest: OllamaLLMRuntimeManifest | None) -> ExternalEngineCardState:
    if manifest is None:
        return ExternalEngineCardState(OLLAMA_LLM_ENGINE_ID, "Ollama 本地 LLM", "not_configured", "", "尚未检查；点击运行检查生成 runtime manifest。")
    status = _ollama_status_from_manifest(manifest)
    installed = len(manifest.installed_models)
    missing = len(manifest.missing_models)
    smoke = ", ".join(f"{item.role_id}:{item.status}" for item in manifest.smoke_results) or "not_run"
    summary = f"service={manifest.service_available}；installed={installed}；missing={missing}；smoke={smoke}"
    return ExternalEngineCardState(OLLAMA_LLM_ENGINE_ID, "Ollama 本地 LLM", status, manifest.detected_at, summary)


def _ollama_status_from_manifest(manifest: OllamaLLMRuntimeManifest) -> str:
    if not manifest.ollama_command_path:
        return "missing"
    if not manifest.service_available:
        return "missing"
    if manifest.missing_models:
        return "partial"
    smoke_statuses = {result.status for result in manifest.smoke_results}
    if smoke_statuses and smoke_statuses <= {"passed"}:
        return "available"
    if "failed" in smoke_statuses:
        return "partial"
    return "available"


def _engine_status_label(status: str) -> str:
    return {
        ENGINE_STATUS_AVAILABLE: "available",
        ENGINE_STATUS_FAILED: "missing",
        ENGINE_STATUS_NOT_CONFIGURED: "not_configured",
    }.get(status, status or "not_configured")


def _manifest_summary(manifest: OllamaLLMRuntimeManifest) -> dict[str, object]:
    return {
        "engine_family": manifest.engine_family,
        "detected_at": manifest.detected_at,
        "ollama_command_path": manifest.ollama_command_path,
        "ollama_version": manifest.ollama_version,
        "http_endpoint": manifest.http_endpoint,
        "service_available": manifest.service_available,
        "installed_models": [model.name for model in manifest.installed_models],
        "missing_models": list(manifest.missing_models),
        "smoke_results": [result.to_dict() for result in manifest.smoke_results],
        "privacy_mode": manifest.privacy_mode,
        "warnings": list(manifest.warnings),
    }


def _dependency_card_states(registry: ExternalEngineRegistry | None) -> tuple[ExternalEngineCardState, ...]:
    if registry is None:
        registry = ExternalEngineRegistry(())
    display_names = {
        R_BIOCONDUCTOR_ENGINE_FAMILY: "R / Bioconductor 依赖",
        PYTHON_STATISTICAL_ENGINE_FAMILY: "Python 统计依赖",
        REPORT_RENDERER_ENGINE_FAMILY: "报告渲染工具链",
    }
    states: list[ExternalEngineCardState] = []
    for family in _DEPENDENCY_ENGINE_FAMILIES:
        snapshot = registry.query_engine_family(family)
        if not snapshot:
            states.append(ExternalEngineCardState(family, display_names[family], "not_configured", "", "尚未检测；点击重新检测生成 dependency snapshot。"))
            continue
        blockers = snapshot.get("blockers") if isinstance(snapshot.get("blockers"), list) else []
        available_count = sum(1 for package in snapshot.get("packages", []) if isinstance(package, dict) and package.get("status") == "available")
        total_count = sum(1 for package in snapshot.get("packages", []) if isinstance(package, dict))
        states.append(
            ExternalEngineCardState(
                family,
                display_names[family],
                str(snapshot.get("status") or "unknown"),
                str(snapshot.get("checked_at") or ""),
                f"available={available_count}/{total_count}；blockers={len(blockers)}；只表示依赖状态。",
            )
        )
    return tuple(states)


def _engine_card(state: ExternalEngineCardState, *, action_text: str) -> QFrame:
    frame = QFrame()
    frame.setObjectName("externalEngineCard")
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(SPACING["md"], SPACING["md"], SPACING["md"], SPACING["md"])
    layout.setSpacing(SPACING["xs"])
    title = QLabel(state.display_name)
    title.setObjectName("externalEngineCardTitle")
    family = QLabel(f"engine family：{state.engine_family}")
    family.setObjectName("externalEngineCardSummary")
    family.setWordWrap(True)
    status = QLabel(f"状态：{state.status}")
    status.setObjectName("externalEngineCardStatus")
    checked = QLabel(f"最近检查：{state.last_checked or '未检查'}")
    checked.setObjectName("externalEngineCardSummary")
    checked.setWordWrap(True)
    summary = QLabel(state.summary)
    summary.setObjectName("externalEngineCardSummary")
    summary.setWordWrap(True)
    action = QLabel(f"操作：{action_text}")
    action.setObjectName("externalEngineCardSummary")
    for widget in (title, family, status, checked, summary, action):
        layout.addWidget(widget)
    layout.addStretch(1)
    return frame


def _clear_layout(layout: QGridLayout) -> None:
    while layout.count():
        item = layout.takeAt(0)
        widget = item.widget()
        if widget is not None:
            widget.deleteLater()
