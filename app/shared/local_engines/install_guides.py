from __future__ import annotations


IMAGEJ_FIJI_INSTALL_GUIDE = "\n".join(
    (
        "ImageJ/Fiji 图像分析引擎用于本机辅助图像分析。",
        "请从 Fiji/ImageJ 官方渠道安装，并在需要图像分析 workflow 时选择本机 Fiji.app、ImageJ.app 或可执行文件路径。",
        "BioMedPilot 不会静默下载、静默安装、上传图片或在未由用户触发 workflow 时运行 macro。",
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
