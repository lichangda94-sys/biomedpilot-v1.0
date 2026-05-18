from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from app.shared.storage import default_storage_root


CELL_EXPERIMENT_STORE_SCHEMA_VERSION = "labtools_cell_experiment_store.v1"
CELL_EXPERIMENT_RECORD_SCHEMA_VERSION = "labtools_cell_experiment_record.v1"

CELL_EXPERIMENT_RECORD_TYPES: tuple[tuple[str, str], ...] = (
    ("cell_profile", "细胞档案"),
    ("thaw", "细胞复苏记录"),
    ("passage", "细胞传代记录"),
    ("seeding", "细胞接种 / 铺板记录"),
    ("freezing", "细胞冻存记录"),
    ("treatment", "给药 / 处理记录"),
    ("transfection", "转染记录"),
    ("other", "其他处理记录"),
)

CRYOVIAL_STATUSES = ("可用", "已复苏", "已转移", "已丢弃", "状态未知")

RECORD_TEMPLATE_FIELDS: dict[str, tuple[str, ...]] = {
    "thaw": (
        "thaw_date",
        "cryovial_id",
        "cryovial_code",
        "freezing_batch_id",
        "freezing_passage",
        "freezing_date",
        "freezing_location",
        "passage_after_thaw",
        "water_bath_temperature",
        "thawing_time",
        "recovery_medium",
        "remove_dmso",
        "seeding_vessel",
        "attachment_or_growth_status",
        "contamination_observation",
    ),
    "passage": (
        "passage_date",
        "passage_before",
        "passage_after",
        "confluence_before_passage",
        "cell_status",
        "culture_vessel",
        "dissociation_reagent",
        "split_ratio",
        "new_vessel",
        "final_culture_volume",
        "update_profile_passage",
    ),
    "seeding": (
        "seeding_date",
        "current_cell_concentration",
        "cell_concentration_unit",
        "target_cells_per_well",
        "volume_per_well",
        "well_count",
        "extra_percent",
        "group_name",
        "replicate_count",
        "plate_layout_notes",
    ),
    "freezing": (
        "freezing_date",
        "passage",
        "confluence_before_freezing",
        "cell_status",
        "cell_concentration",
        "viability_percent",
        "cryovial_count",
        "cells_per_vial",
        "volume_per_vial",
        "freezing_medium_formula",
        "dmso_percent",
        "serum_percent",
        "cooling_method",
        "liquid_nitrogen_tank",
        "rack",
        "box",
        "start_box_position",
    ),
    "treatment": (
        "treatment_date",
        "treatment_type",
        "treatment_name",
        "working_concentration",
        "solvent_or_vehicle",
        "treatment_duration",
        "group_name",
        "dose",
        "time_point",
        "replicate_count",
        "observation_result",
    ),
    "transfection": (
        "transfection_date",
        "transfection_type",
        "transfection_method",
        "transfection_reagent_name",
        "dna_or_rna_name",
        "dna_or_rna_amount_per_well",
        "reagent_volume",
        "detection_time_point",
        "transfection_efficiency_method",
        "toxicity_observation",
    ),
    "other": (
        "operation_date",
        "operation_type",
        "operation_purpose",
        "key_reagents",
        "operation_steps",
        "duration",
        "temperature_or_culture_condition",
        "group_design",
        "replicate_count",
        "observation_result",
    ),
}


class CellExperimentError(ValueError):
    pass


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def default_cell_experiment_root() -> Path:
    return default_storage_root() / "labtools" / "cell_experiments"


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex}"


def _string_dict(payload: Any) -> dict[str, str]:
    return {str(key): str(value) for key, value in payload.items()} if isinstance(payload, dict) else {}


def _read_json(path: Path, missing: dict[str, Any]) -> dict[str, Any]:
    if not path.exists():
        return missing
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise CellExperimentError(f"{path.name} 不是有效 JSON。") from exc
    if not isinstance(payload, dict):
        raise CellExperimentError(f"{path.name} 必须是 JSON object。")
    if payload.get("schema_version") != CELL_EXPERIMENT_STORE_SCHEMA_VERSION:
        raise CellExperimentError(f"{path.name} schema 不匹配。")
    return payload


def _write_json(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


@dataclass(frozen=True)
class CellProfile:
    cell_name: str
    cell_profile_id: str = field(default_factory=lambda: _new_id("cell_profile"))
    alias: str = ""
    cell_type: str = "细胞株"
    species: str = ""
    tissue_origin: str = ""
    disease_background: str = ""
    morphology: str = "贴壁"
    source: str = ""
    catalog_number: str = ""
    batch_or_lot: str = ""
    received_date: str = ""
    initial_passage: str = ""
    current_passage: str = ""
    owner: str = ""
    basal_medium: str = ""
    serum_type: str = ""
    serum_percent: str = ""
    antibiotics: str = ""
    additional_supplements: str = ""
    culture_temperature: str = "37 C"
    co2_percent: str = "5"
    oxygen_percent: str = ""
    recommended_vessel: str = ""
    recommended_split_ratio: str = ""
    recommended_medium_change_frequency: str = ""
    recommended_seeding_density: str = ""
    recommended_max_passage: str = ""
    culture_notes: str = ""
    current_status: str = "培养中"
    mycoplasma_status: str = "未检测"
    mycoplasma_test_date: str = ""
    str_status: str = "未检测"
    str_test_date: str = ""
    contamination_record: str = ""
    abnormal_status_record: str = ""
    last_observation_date: str = ""
    last_observation_result: str = ""
    notes: str = ""
    sop_text: str = ""
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)

    def with_updated_timestamp(self) -> "CellProfile":
        return self._replace(updated_at=utc_now())

    def _replace(self, **changes: str) -> "CellProfile":
        payload = self.to_dict()
        payload.update(changes)
        return CellProfile.from_dict(payload)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: Any) -> "CellProfile":
        if not isinstance(payload, dict):
            raise CellExperimentError("细胞档案 payload 必须是 JSON object。")
        allowed = set(cls.__dataclass_fields__)
        values = {key: str(value) for key, value in payload.items() if key in allowed and value is not None}
        if not values.get("cell_name"):
            raise CellExperimentError("细胞档案缺少 cell_name。")
        return cls(**values)

    def snapshot(self) -> dict[str, str]:
        return {
            "cell_name": self.cell_name,
            "alias": self.alias,
            "cell_type": self.cell_type,
            "species": self.species,
            "tissue_origin": self.tissue_origin,
            "current_passage": self.current_passage,
            "culture_medium": self.basal_medium,
            "serum": " ".join(part for part in (self.serum_type, self.serum_percent) if part),
            "antibiotics": self.antibiotics,
            "culture_temperature": self.culture_temperature,
            "co2_percent": self.co2_percent,
            "recommended_split_ratio": self.recommended_split_ratio,
            "recommended_seeding_density": self.recommended_seeding_density,
            "quality_status": f"支原体：{self.mycoplasma_status}; STR：{self.str_status}; 状态：{self.current_status}",
        }

    def as_text(self) -> str:
        lines = [
            "细胞档案摘要",
            f"细胞名称：{self.cell_name}",
            f"档案 ID：{self.cell_profile_id}",
            f"别名：{self.alias}",
            f"类型：{self.cell_type}",
            f"来源：{self.source} {self.catalog_number} {self.batch_or_lot}".strip(),
            f"当前 passage：{self.current_passage}",
            f"培养基：{self.basal_medium}",
            f"培养条件：{self.culture_temperature}; CO2 {self.co2_percent}%",
            f"质控：支原体 {self.mycoplasma_status}; STR {self.str_status}",
            "",
            "SOP / 备注：",
            self.sop_text or self.notes or "未填写",
        ]
        return "\n".join(lines)


@dataclass(frozen=True)
class FreezingBatch:
    cell_profile_id: str
    cell_name: str
    freezing_batch_id: str = field(default_factory=lambda: _new_id("freezing_batch"))
    batch_code: str = ""
    freezing_date: str = field(default_factory=lambda: date.today().isoformat())
    passage: str = ""
    cell_status_before_freezing: str = ""
    confluence_before_freezing: str = ""
    cell_concentration: str = ""
    viability_percent: str = ""
    cryovial_count: int = 0
    cells_per_vial: str = ""
    volume_per_vial: str = ""
    freezing_medium_formula: str = ""
    dmso_percent: str = ""
    serum_percent: str = ""
    cooling_method: str = ""
    time_to_minus_80: str = ""
    time_to_liquid_nitrogen: str = ""
    operator: str = ""
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: Any) -> "FreezingBatch":
        if not isinstance(payload, dict):
            raise CellExperimentError("冻存批次 payload 必须是 JSON object。")
        values = {key: payload.get(key) for key in cls.__dataclass_fields__ if key in payload}
        values["cryovial_count"] = int(values.get("cryovial_count") or 0)
        return cls(**values)


@dataclass(frozen=True)
class Cryovial:
    freezing_batch_id: str
    cell_profile_id: str
    cell_name: str
    cryovial_id: str = field(default_factory=lambda: _new_id("cryovial"))
    cryovial_code: str = ""
    passage: str = ""
    freezing_date: str = ""
    cells_per_vial: str = ""
    volume_per_vial: str = ""
    status: str = "可用"
    liquid_nitrogen_tank: str = ""
    rack: str = ""
    box: str = ""
    box_position: str = ""
    location_notes: str = ""
    removed_date: str = ""
    thaw_record_id: str = ""
    operator: str = ""
    notes: str = ""

    def with_updates(self, **changes: str) -> "Cryovial":
        payload = self.to_dict()
        payload.update(changes)
        return Cryovial.from_dict(payload)

    @property
    def location(self) -> str:
        return " / ".join(part for part in (self.liquid_nitrogen_tank, self.rack, self.box, self.box_position) if part)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: Any) -> "Cryovial":
        if not isinstance(payload, dict):
            raise CellExperimentError("冻存管 payload 必须是 JSON object。")
        values = {key: str(payload.get(key) or "") for key in cls.__dataclass_fields__ if key in payload}
        if values.get("status") not in CRYOVIAL_STATUSES:
            values["status"] = "状态未知"
        return cls(**values)


@dataclass(frozen=True)
class CellExperimentRecord:
    record_type: str
    cell_profile_id: str
    cell_profile_snapshot: dict[str, str]
    experiment_name: str
    fields: dict[str, str] = field(default_factory=dict)
    operator: str = ""
    notes: str = ""
    free_text_sop: str = ""
    exported_text_path: str = ""
    record_id: str = field(default_factory=lambda: _new_id("cell_record"))
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)
    schema_version: str = CELL_EXPERIMENT_RECORD_SCHEMA_VERSION

    def with_updated_timestamp(self) -> "CellExperimentRecord":
        payload = self.to_dict()
        payload["updated_at"] = utc_now()
        return CellExperimentRecord.from_dict(payload)

    def copied_from_last(self) -> "CellExperimentRecord":
        payload = self.to_dict()
        payload["record_id"] = _new_id("cell_record")
        payload["created_at"] = utc_now()
        payload["updated_at"] = payload["created_at"]
        payload["exported_text_path"] = ""
        return CellExperimentRecord.from_dict(payload)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "record_id": self.record_id,
            "record_type": self.record_type,
            "cell_profile_id": self.cell_profile_id,
            "cell_profile_snapshot": dict(self.cell_profile_snapshot),
            "experiment_name": self.experiment_name,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "operator": self.operator,
            "notes": self.notes,
            "free_text_sop": self.free_text_sop,
            "exported_text_path": self.exported_text_path,
            "fields": dict(self.fields),
        }

    @classmethod
    def from_dict(cls, payload: Any) -> "CellExperimentRecord":
        if not isinstance(payload, dict):
            raise CellExperimentError("实验记录 payload 必须是 JSON object。")
        if payload.get("schema_version", CELL_EXPERIMENT_RECORD_SCHEMA_VERSION) != CELL_EXPERIMENT_RECORD_SCHEMA_VERSION:
            raise CellExperimentError("实验记录 schema 不匹配。")
        return cls(
            record_id=str(payload.get("record_id") or _new_id("cell_record")),
            record_type=str(payload.get("record_type") or ""),
            cell_profile_id=str(payload.get("cell_profile_id") or ""),
            cell_profile_snapshot=_string_dict(payload.get("cell_profile_snapshot")),
            experiment_name=str(payload.get("experiment_name") or ""),
            created_at=str(payload.get("created_at") or utc_now()),
            updated_at=str(payload.get("updated_at") or utc_now()),
            operator=str(payload.get("operator") or ""),
            notes=str(payload.get("notes") or ""),
            free_text_sop=str(payload.get("free_text_sop") or ""),
            exported_text_path=str(payload.get("exported_text_path") or ""),
            fields=_string_dict(payload.get("fields")),
        )

    def as_text(self) -> str:
        lines = [
            f"记录类型：{dict(CELL_EXPERIMENT_RECORD_TYPES).get(self.record_type, self.record_type)}",
            f"实验名称：{self.experiment_name}",
            f"记录 ID：{self.record_id}",
            f"创建时间：{self.created_at}",
            f"操作者：{self.operator}",
            "",
            "细胞档案快照：",
        ]
        lines.extend(f"- {key}：{value}" for key, value in self.cell_profile_snapshot.items())
        lines.extend(["", "主要参数："])
        lines.extend(f"{key}：{value}" for key, value in self.fields.items())
        lines.extend(["", "SOP / 自由文本：", self.free_text_sop or "未填写", "", "备注：", self.notes or "未填写"])
        return "\n".join(lines)


@dataclass(frozen=True)
class SeedingCalculationResult:
    total_target_cells: float
    suggested_total_volume: float
    cell_suspension_volume: float
    medium_volume: float
    unit: str
    warnings: tuple[str, ...] = ()


def calculate_seeding_preparation(
    current_cell_concentration: float,
    concentration_unit: str,
    target_cells_per_well: float,
    well_count: int,
    volume_per_well: float,
    extra_percent: float = 0,
) -> SeedingCalculationResult:
    if current_cell_concentration <= 0:
        raise CellExperimentError("当前细胞浓度不能为 0。")
    if well_count <= 0 or target_cells_per_well < 0 or volume_per_well < 0 or extra_percent < 0:
        raise CellExperimentError("接种计算输入不能为负数，孔数必须大于 0。")
    factor = 1 + extra_percent / 100
    total_target_cells = target_cells_per_well * well_count * factor
    suggested_total_volume = volume_per_well * well_count * factor
    unit = "µL" if concentration_unit == "cells/µL" else "mL"
    cell_suspension_volume = total_target_cells / current_cell_concentration
    medium_volume = suggested_total_volume - cell_suspension_volume
    warnings: tuple[str, ...] = ()
    if cell_suspension_volume > suggested_total_volume:
        warnings = ("当前细胞浓度不足，需要浓缩细胞悬液或调整接种条件。",)
    return SeedingCalculationResult(
        total_target_cells=total_target_cells,
        suggested_total_volume=suggested_total_volume,
        cell_suspension_volume=cell_suspension_volume,
        medium_volume=medium_volume,
        unit=unit,
        warnings=warnings,
    )


@dataclass
class CellProfileStore:
    path: Path | None = None

    def resolved_path(self) -> Path:
        return self.path or default_cell_experiment_root() / "cell_profiles.json"

    def load(self) -> tuple[CellProfile, ...]:
        payload = _read_json(self.resolved_path(), {"schema_version": CELL_EXPERIMENT_STORE_SCHEMA_VERSION, "profiles": []})
        profiles = payload.get("profiles")
        if not isinstance(profiles, list):
            raise CellExperimentError("细胞档案 JSON 缺少 profiles 列表。")
        return tuple(CellProfile.from_dict(item) for item in profiles)

    def save_all(self, profiles: tuple[CellProfile, ...]) -> Path:
        ids: set[str] = set()
        for profile in profiles:
            if profile.cell_profile_id in ids:
                raise CellExperimentError("细胞档案 cell_profile_id 重复。")
            ids.add(profile.cell_profile_id)
        return _write_json(
            self.resolved_path(),
            {"schema_version": CELL_EXPERIMENT_STORE_SCHEMA_VERSION, "updated_at": utc_now(), "profiles": [profile.to_dict() for profile in profiles]},
        )

    def save_profile(self, profile: CellProfile) -> CellProfile:
        profiles = list(self.load())
        updated = profile.with_updated_timestamp()
        for index, current in enumerate(profiles):
            if current.cell_profile_id == profile.cell_profile_id:
                profiles[index] = updated
                self.save_all(tuple(profiles))
                return updated
        profiles.append(updated)
        self.save_all(tuple(profiles))
        return updated

    def get(self, cell_profile_id: str) -> CellProfile:
        for profile in self.load():
            if profile.cell_profile_id == cell_profile_id:
                return profile
        raise CellExperimentError("细胞档案不存在。")

    def search(self, query: str) -> tuple[CellProfile, ...]:
        query = query.strip().lower()
        if not query:
            return self.load()
        return tuple(profile for profile in self.load() if query in profile.cell_name.lower() or query in profile.alias.lower())

    def copy_profile(self, cell_profile_id: str) -> CellProfile:
        source = self.get(cell_profile_id)
        copied = CellProfile.from_dict({**source.to_dict(), "cell_profile_id": _new_id("cell_profile"), "cell_name": f"{source.cell_name} copy", "created_at": utc_now(), "updated_at": utc_now()})
        return self.save_profile(copied)

    def export_profile_text(self, cell_profile_id: str, export_dir: Path | None = None) -> Path:
        profile = self.get(cell_profile_id)
        directory = export_dir or default_cell_experiment_root() / "exports"
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f"{profile.cell_profile_id}_profile.txt"
        path.write_text(profile.as_text() + "\n", encoding="utf-8")
        return path


@dataclass
class FreezingInventoryStore:
    path: Path | None = None

    def resolved_path(self) -> Path:
        return self.path or default_cell_experiment_root() / "freezing_inventory.json"

    def load(self) -> tuple[tuple[FreezingBatch, ...], tuple[Cryovial, ...]]:
        payload = _read_json(self.resolved_path(), {"schema_version": CELL_EXPERIMENT_STORE_SCHEMA_VERSION, "freezing_batches": [], "cryovials": []})
        batches = payload.get("freezing_batches")
        cryovials = payload.get("cryovials")
        if not isinstance(batches, list) or not isinstance(cryovials, list):
            raise CellExperimentError("冻存库存 JSON 缺少 freezing_batches 或 cryovials 列表。")
        return tuple(FreezingBatch.from_dict(item) for item in batches), tuple(Cryovial.from_dict(item) for item in cryovials)

    def save_all(self, batches: tuple[FreezingBatch, ...], cryovials: tuple[Cryovial, ...]) -> Path:
        return _write_json(
            self.resolved_path(),
            {
                "schema_version": CELL_EXPERIMENT_STORE_SCHEMA_VERSION,
                "updated_at": utc_now(),
                "freezing_batches": [batch.to_dict() for batch in batches],
                "cryovials": [cryovial.to_dict() for cryovial in cryovials],
            },
        )

    def save_batch_with_generated_cryovials(
        self,
        batch: FreezingBatch,
        *,
        liquid_nitrogen_tank: str = "",
        rack: str = "",
        box: str = "",
        start_box_position: str = "1",
    ) -> tuple[FreezingBatch, tuple[Cryovial, ...]]:
        batches, cryovials = self.load()
        batch_code = batch.batch_code or batch.freezing_batch_id
        generated = tuple(
            Cryovial(
                freezing_batch_id=batch.freezing_batch_id,
                cryovial_code=f"{batch_code}-{index + 1:02d}",
                cell_profile_id=batch.cell_profile_id,
                cell_name=batch.cell_name,
                passage=batch.passage,
                freezing_date=batch.freezing_date,
                cells_per_vial=batch.cells_per_vial,
                volume_per_vial=batch.volume_per_vial,
                liquid_nitrogen_tank=liquid_nitrogen_tank,
                rack=rack,
                box=box,
                box_position=_next_box_position(start_box_position, index),
                operator=batch.operator,
            )
            for index in range(max(batch.cryovial_count, 0))
        )
        kept_batches = tuple(current for current in batches if current.freezing_batch_id != batch.freezing_batch_id)
        kept_cryovials = tuple(current for current in cryovials if current.freezing_batch_id != batch.freezing_batch_id)
        self.save_all(kept_batches + (batch,), kept_cryovials + generated)
        return batch, generated

    def update_cryovial(self, cryovial_id: str, **changes: str) -> Cryovial:
        batches, cryovials = self.load()
        updated: Cryovial | None = None
        next_cryovials: list[Cryovial] = []
        for cryovial in cryovials:
            if cryovial.cryovial_id == cryovial_id:
                updated = cryovial.with_updates(**changes)
                next_cryovials.append(updated)
            else:
                next_cryovials.append(cryovial)
        if updated is None:
            raise CellExperimentError("冻存管不存在。")
        self.save_all(batches, tuple(next_cryovials))
        return updated

    def mark_cryovial_status(self, cryovial_id: str, status: str, *, thaw_record_id: str = "", operator: str = "", removed_date: str | None = None) -> Cryovial:
        if status not in CRYOVIAL_STATUSES:
            raise CellExperimentError("冻存管状态不受支持。")
        changes = {"status": status, "operator": operator}
        if status == "已复苏":
            changes["thaw_record_id"] = thaw_record_id
            changes["removed_date"] = removed_date or date.today().isoformat()
        return self.update_cryovial(cryovial_id, **changes)

    def list_cryovials(self, *, cell_profile_id: str = "", status: str = "", query: str = "") -> tuple[Cryovial, ...]:
        _, cryovials = self.load()
        results = cryovials
        if cell_profile_id:
            results = tuple(cryovial for cryovial in results if cryovial.cell_profile_id == cell_profile_id)
        if status:
            results = tuple(cryovial for cryovial in results if cryovial.status == status)
        if query:
            needle = query.lower()
            results = tuple(
                cryovial
                for cryovial in results
                if needle in " ".join((cryovial.cell_name, cryovial.cryovial_code, cryovial.passage, cryovial.location, cryovial.status)).lower()
            )
        return results

    def list_available_cryovials(self, cell_profile_id: str) -> tuple[Cryovial, ...]:
        return self.list_cryovials(cell_profile_id=cell_profile_id, status="可用")

    def export_inventory_text(self, export_dir: Path | None = None) -> Path:
        _, cryovials = self.load()
        directory = export_dir or default_cell_experiment_root() / "exports"
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / "freezing_inventory.txt"
        lines = ["细胞名称\t批次编号\t冻存日期\tPassage\t冻存管编号\t位置\t状态\t每管体积\t每管细胞数\t备注"]
        lines.extend(
            "\t".join(
                (
                    cryovial.cell_name,
                    cryovial.freezing_batch_id,
                    cryovial.freezing_date,
                    cryovial.passage,
                    cryovial.cryovial_code,
                    cryovial.location,
                    cryovial.status,
                    cryovial.volume_per_vial,
                    cryovial.cells_per_vial,
                    cryovial.notes,
                )
            )
            for cryovial in cryovials
        )
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return path


@dataclass
class CellExperimentRecordStore:
    path: Path | None = None
    profile_store: CellProfileStore | None = None
    inventory_store: FreezingInventoryStore | None = None

    def resolved_path(self) -> Path:
        return self.path or default_cell_experiment_root() / "cell_records.json"

    def load(self) -> tuple[CellExperimentRecord, ...]:
        payload = _read_json(self.resolved_path(), {"schema_version": CELL_EXPERIMENT_STORE_SCHEMA_VERSION, "records": []})
        records = payload.get("records")
        if not isinstance(records, list):
            raise CellExperimentError("细胞实验记录 JSON 缺少 records 列表。")
        return tuple(CellExperimentRecord.from_dict(item) for item in records)

    def save_all(self, records: tuple[CellExperimentRecord, ...]) -> Path:
        return _write_json(
            self.resolved_path(),
            {"schema_version": CELL_EXPERIMENT_STORE_SCHEMA_VERSION, "updated_at": utc_now(), "records": [record.to_dict() for record in records]},
        )

    def save_record(self, record: CellExperimentRecord, *, update_profile_passage: bool = True) -> CellExperimentRecord:
        records = list(self.load())
        updated = record.with_updated_timestamp()
        for index, current in enumerate(records):
            if current.record_id == record.record_id:
                records[index] = updated
                break
        else:
            records.append(updated)
        self.save_all(tuple(records))
        if updated.record_type == "thaw" and updated.fields.get("cryovial_id"):
            self._inventory().mark_cryovial_status(updated.fields["cryovial_id"], "已复苏", thaw_record_id=updated.record_id, operator=updated.operator)
        if updated.record_type == "passage" and update_profile_passage and updated.fields.get("passage_after"):
            profile_store = self._profiles()
            profile = profile_store.get(updated.cell_profile_id)
            profile_store.save_profile(profile._replace(current_passage=updated.fields["passage_after"]))
        return updated

    def latest_for_type(self, record_type: str) -> CellExperimentRecord | None:
        matches = [record for record in self.load() if record.record_type == record_type]
        return max(matches, key=lambda record: record.updated_at) if matches else None

    def create_from_last(self, record_type: str) -> CellExperimentRecord | None:
        latest = self.latest_for_type(record_type)
        return latest.copied_from_last() if latest else None

    def export_record_text(self, record_id: str, export_dir: Path | None = None) -> Path:
        record = self.get(record_id)
        directory = export_dir or default_cell_experiment_root() / "exports"
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f"{record.record_id}.txt"
        path.write_text(record.as_text() + "\n", encoding="utf-8")
        exported = CellExperimentRecord.from_dict({**record.to_dict(), "exported_text_path": str(path)})
        records = tuple(exported if current.record_id == record_id else current for current in self.load())
        self.save_all(records)
        return path

    def get(self, record_id: str) -> CellExperimentRecord:
        for record in self.load():
            if record.record_id == record_id:
                return record
        raise CellExperimentError("细胞实验记录不存在。")

    def _profiles(self) -> CellProfileStore:
        return self.profile_store or CellProfileStore()

    def _inventory(self) -> FreezingInventoryStore:
        return self.inventory_store or FreezingInventoryStore()


def _next_box_position(start: str, index: int) -> str:
    try:
        return str(int(start) + index)
    except ValueError:
        return f"{start}-{index + 1}"
