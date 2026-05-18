from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from uuid import uuid4

from app.shared.storage import default_storage_root
from app.labtools.western_blot.models import utc_now


WB_WORKFLOW_RECORD_SCHEMA_VERSION = "western_blot_workflow_record.v1"
WB_WORKFLOW_STORE_SCHEMA_VERSION = "western_blot_workflow_store.v1"
WB_REVIEW_NOTICE = "请先核对 SOP、试剂纯度、pH、温度和安全要求。"

WB_WORKFLOW_STEPS: tuple[tuple[str, str], ...] = (
    ("sample_preparation", "蛋白样品准备"),
    ("bca_assay", "BCA 蛋白浓度测定"),
    ("protein_loading", "蛋白上样计算"),
    ("gel_lane_layout", "配胶与 Lane 布局"),
    ("electrophoresis", "电泳记录"),
    ("transfer", "电转记录"),
    ("blocking", "封闭记录"),
    ("primary_antibody", "一抗孵育记录"),
    ("primary_wash", "一抗后洗膜记录"),
    ("secondary_antibody", "二抗孵育记录"),
    ("secondary_wash", "二抗后洗膜记录"),
    ("imaging", "显影/成像记录"),
    ("result_analysis", "结果与灰度分析"),
)

WB_RECORD_STEP_FIELDS: dict[str, tuple[str, ...]] = {
    "sample_preparation": ("样品来源", "样品编号", "组织/细胞类型", "实验分组", "裂解液类型", "保存条件", "备注"),
    "electrophoresis": ("实验日期", "胶类型", "胶浓度", "running buffer", "电压模式", "总运行时间", "异常记录"),
    "transfer": ("膜类型", "膜孔径", "transfer buffer", "转膜方式", "电压", "电流", "时间", "异常记录"),
    "blocking": ("blocking buffer", "buffer 基础", "Tween 浓度", "封闭体积", "封闭时间", "温度", "备注"),
    "primary_antibody": ("靶蛋白名称", "一抗名称", "厂家", "货号", "lot 号", "抗体稀释比例", "孵育时间", "孵育温度", "备注"),
    "primary_wash": ("洗膜阶段", "wash buffer", "Tween 浓度", "每次洗膜时间", "洗膜次数", "总体积", "备注"),
    "secondary_antibody": ("二抗名称", "识别对象", "标记类型", "厂家", "货号", "lot 号", "稀释比例", "孵育时间", "备注"),
    "secondary_wash": ("洗膜阶段", "wash buffer", "Tween 浓度", "每次洗膜时间", "洗膜次数", "总体积", "备注"),
    "imaging": ("显影方式", "显影试剂", "曝光设备", "曝光时间", "通道", "图像文件路径", "是否进入后续灰度分析", "备注"),
}


class WBWorkflowRecordError(ValueError):
    pass


@dataclass(frozen=True)
class WBWorkflowRecord:
    step_id: str
    step_label: str
    fields: dict[str, str]
    sop_text: str = ""
    free_text: str = ""
    record_id: str = field(default_factory=lambda: f"wb_workflow_{uuid4().hex}")
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)
    review_notice: str = WB_REVIEW_NOTICE
    schema_version: str = WB_WORKFLOW_RECORD_SCHEMA_VERSION

    def with_updated_timestamp(self) -> "WBWorkflowRecord":
        return WBWorkflowRecord(
            step_id=self.step_id,
            step_label=self.step_label,
            fields=dict(self.fields),
            sop_text=self.sop_text,
            free_text=self.free_text,
            record_id=self.record_id,
            created_at=self.created_at,
            updated_at=utc_now(),
            review_notice=self.review_notice,
            schema_version=self.schema_version,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "record_id": self.record_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "step_id": self.step_id,
            "step_label": self.step_label,
            "fields": dict(self.fields),
            "sop_text": self.sop_text,
            "free_text": self.free_text,
            "review_notice": self.review_notice,
        }

    @classmethod
    def from_dict(cls, payload: Any) -> "WBWorkflowRecord":
        if not isinstance(payload, dict):
            raise WBWorkflowRecordError("Western Blot workflow record payload 必须是 JSON object。")
        if payload.get("schema_version") != WB_WORKFLOW_RECORD_SCHEMA_VERSION:
            raise WBWorkflowRecordError("Western Blot workflow record schema 不匹配。")
        fields = payload.get("fields")
        return cls(
            record_id=str(payload.get("record_id") or f"wb_workflow_{uuid4().hex}"),
            created_at=str(payload.get("created_at") or utc_now()),
            updated_at=str(payload.get("updated_at") or utc_now()),
            step_id=str(payload.get("step_id") or ""),
            step_label=str(payload.get("step_label") or ""),
            fields={str(key): str(value) for key, value in fields.items()} if isinstance(fields, dict) else {},
            sop_text=str(payload.get("sop_text") or ""),
            free_text=str(payload.get("free_text") or ""),
            review_notice=str(payload.get("review_notice") or WB_REVIEW_NOTICE),
            schema_version=str(payload.get("schema_version") or WB_WORKFLOW_RECORD_SCHEMA_VERSION),
        )

    def as_text(self) -> str:
        lines = [self.step_label, f"记录 ID：{self.record_id}", f"更新时间：{self.updated_at}", ""]
        lines.extend(f"{key}：{value}" for key, value in self.fields.items())
        lines.extend(["", "SOP 模板", self.sop_text or "未填写", "", "自由文本实验记录", self.free_text or "未填写", "", "人工核对提示", self.review_notice])
        return "\n".join(lines)


def default_wb_workflow_store_path() -> Path:
    return default_storage_root() / "labtools" / "western_blot_workflow_records.json"


@dataclass
class WBWorkflowRecordStore:
    path: Path | None = None

    def resolved_path(self) -> Path:
        return self.path or default_wb_workflow_store_path()

    def load(self) -> tuple[WBWorkflowRecord, ...]:
        path = self.resolved_path()
        if not path.exists():
            return ()
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise WBWorkflowRecordError("Western Blot workflow record JSON 不是有效 JSON。") from exc
        if payload.get("schema_version") != WB_WORKFLOW_STORE_SCHEMA_VERSION:
            raise WBWorkflowRecordError("Western Blot workflow store schema 不匹配。")
        records = payload.get("records")
        if not isinstance(records, list):
            raise WBWorkflowRecordError("Western Blot workflow store 缺少 records 列表。")
        return tuple(WBWorkflowRecord.from_dict(record) for record in records)

    def save_record(self, record: WBWorkflowRecord) -> WBWorkflowRecord:
        records = list(self.load())
        updated = record.with_updated_timestamp()
        for index, current in enumerate(records):
            if current.record_id == record.record_id:
                records[index] = updated
                self.save_all(tuple(records))
                return updated
        records.append(updated)
        self.save_all(tuple(records))
        return updated

    def latest_for_step(self, step_id: str) -> WBWorkflowRecord | None:
        matches = [record for record in self.load() if record.step_id == step_id]
        return max(matches, key=lambda record: record.updated_at) if matches else None

    def save_all(self, records: tuple[WBWorkflowRecord, ...]) -> Path:
        path = self.resolved_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": WB_WORKFLOW_STORE_SCHEMA_VERSION,
            "updated_at": utc_now(),
            "records": [record.to_dict() for record in records],
        }
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return path
