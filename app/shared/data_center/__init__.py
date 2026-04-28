from __future__ import annotations

from app.shared.data_center.service import DataAssetRecord, DataCenter

DATA_TYPES = (
    "GEO 数据",
    "TCGA 数据",
    "GTEx 数据",
    "自有测序数据",
    "文献数据",
    "分析结果表",
    "图表文件",
    "报告文件",
)

__all__ = ["DATA_TYPES", "DataAssetRecord", "DataCenter"]
