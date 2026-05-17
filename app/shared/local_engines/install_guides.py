from __future__ import annotations


IMAGEJ_FIJI_INSTALL_GUIDE = "\n".join(
    (
        "ImageJ/Fiji 图像分析引擎用于本机辅助图像分析。",
        "请从 Fiji/ImageJ 官方渠道安装，或在用户触发图像分析 workflow 后由 BioMedPilot 下载官方 Fiji runtime 并写入 runtime_manifest.json。",
        "推荐 runtime 位置：macOS ~/Library/Application Support/BioMedPilot/engines/image_analysis/imagej_fiji/；Windows %LOCALAPPDATA%\\BioMedPilot\\engines\\image_analysis\\imagej_fiji\\。",
        "BioMedPilot 不会静默下载、静默安装、上传图片或在未由用户触发 workflow 时运行 macro；下载包必须通过官方 .sha256 校验。",
        "官方入口：https://fiji.sc/ 和 https://imagej.net/software/fiji/",
    )
)


def imagej_fiji_install_guide_text() -> str:
    return IMAGEJ_FIJI_INSTALL_GUIDE


def imagej_fiji_setup_prompt_text(*, workflow_name: str = "图像分析 workflow", can_continue_without_engine: bool = True) -> str:
    fallback = "基础流程可继续，但不会运行 ImageJ/Fiji 辅助分析。" if can_continue_without_engine else "该功能需要先完成本机 ImageJ/Fiji 配置。"
    return "\n".join(
        (
            f"{workflow_name} 需要本机 ImageJ/Fiji 图像分析引擎。",
            "需要原因：该后端负责本地图像测量或宏执行，结果仍需人工复核。",
            fallback,
            "可用操作：自动检测、选择本机路径、查看安装指南，或继续 fallback/manual-review 流程。",
        )
    )


PADDLEOCR_INSTALL_GUIDE = "\n".join(
    (
        "PaddleOCR 本地 OCR 引擎用于将用户导入的 PDF / 图片转换为本地 .txt 和 .ocr.json。",
        "BioMedPilot 应在用户触发 OCR 功能后创建或选择独立 runtime，不会静默下载模型、上传全文或把 OCR 结果直接写入 Meta 提取字段。",
        "推荐 runtime 位置：macOS ~/Library/Application Support/BioMedPilot/engines/ocr/paddleocr/；Windows %LOCALAPPDATA%\\BioMedPilot\\engines\\ocr\\paddleocr\\。",
        "运行时资产、模型、wheel、缓存和用户全文不应进入 Git。",
    )
)


def paddleocr_install_guide_text() -> str:
    return PADDLEOCR_INSTALL_GUIDE
