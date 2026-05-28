from __future__ import annotations


IMAGEJ_FIJI_INSTALL_GUIDE = "\n".join(
    (
        "ImageJ 是 LabTools 图像分析的优先基础引擎；本机路径可指向 ImageJ.app、ij.jar 或对应可执行入口。",
        "Fiji 保留为增强引擎，只用于后续明确依赖 Fiji 插件的 macro；LabTools 基础图像 workflow 不直接依赖 Fiji。",
        "请优先从 ImageJ 官方渠道安装轻量 ImageJ；需要增强能力时可选择 Fiji，或在用户触发图像分析 workflow 后由 BioMedPilot 下载官方 Fiji runtime 并写入 runtime_manifest.json。",
        "推荐 runtime 位置：macOS ~/Library/Application Support/BioMedPilot/engines/image_analysis/imagej_fiji/；Windows %LOCALAPPDATA%\\BioMedPilot\\engines\\image_analysis\\imagej_fiji\\。",
        "BioMedPilot 不会静默下载、静默安装、上传图片或在未由用户触发 workflow 时运行 macro；下载包必须通过官方 .sha256 校验。",
        "官方入口：https://fiji.sc/ 和 https://imagej.net/software/fiji/",
    )
)


def imagej_fiji_install_guide_text() -> str:
    return IMAGEJ_FIJI_INSTALL_GUIDE


def imagej_fiji_setup_prompt_text(*, workflow_name: str = "图像分析 workflow", can_continue_without_engine: bool = True) -> str:
    fallback = "基础流程可继续，但不会运行 ImageJ 辅助分析。" if can_continue_without_engine else "该功能需要先完成本机 ImageJ 配置。"
    return "\n".join(
        (
            f"{workflow_name} 需要本机 ImageJ 图像分析引擎；Fiji 仅作为增强引擎保留。",
            "需要原因：该后端负责本地图像测量或宏执行，macro 会标记最低引擎要求为 imagej 或 fiji，结果仍需人工复核。",
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


R_ENRICHMENT_INSTALL_GUIDE = "\n".join(
    (
        "外部 R 富集分析后端用于 Bioinformatics 的 ORA / GSEA / Reactome / MSigDB 资源检测与后续受控执行。",
        "BioMedPilot 只做 detect-first 状态读取：不会在 app runtime 内静默安装、静默下载、打包或更新 R / Bioconductor / CRAN 依赖。",
        "必需 R 包：clusterProfiler、fgsea、DOSE、enrichplot、ggplot2、AnnotationDbi、org.Hs.eg.db、ReactomePA、msigdbr。",
        "可选 R 包：pathview、GO.db、KEGGREST；缺失时应作为 warning 或部分能力不可用处理，除非后续策略明确升级为必需。",
        "推荐由 operator 在 BioMedPilot 外部执行：Rscript -e 'options(repos=c(CRAN=\"https://cloud.r-project.org\")); if (!requireNamespace(\"BiocManager\", quietly=TRUE)) install.packages(\"BiocManager\"); BiocManager::install(c(\"ReactomePA\"), ask=FALSE, update=FALSE); install.packages(\"msigdbr\")'",
        "可选补充：Rscript -e 'BiocManager::install(c(\"pathview\", \"GO.db\", \"KEGGREST\"), ask=FALSE, update=FALSE)'",
        "安装后重新运行 external enrichment R backend detection，确认 Rscript 路径、R version、architecture、.libPaths()、package versions、fixture TSV 和 plot smoke metadata。",
        "确认项：install_action 必须保持 none_detect_first_only，packaging_policy 必须保持 external_runtime_not_bundled；R package library、cache、downloaded source tarballs 不应进入 Git 或 BioMedPilot.app。",
    )
)


def r_enrichment_install_guide_text() -> str:
    return R_ENRICHMENT_INSTALL_GUIDE
