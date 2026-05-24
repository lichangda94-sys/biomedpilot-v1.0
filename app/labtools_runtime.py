from __future__ import annotations

import csv
import json
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path
from typing import Any, Callable
from uuid import uuid4

from app.labtools_storage_adapter import BioMedPilotLabToolsStorageAdapter, LabToolsStorageAdapterState


LABTOOLS_SIBLING_ROOT = Path(__file__).resolve().parents[2] / "LabTools"
REVIEW_NOTICE = "实验计算结果需由用户复核后使用。"


@dataclass(frozen=True)
class LabToolsRuntimeStatus:
    available: bool
    message: str


@dataclass(frozen=True)
class LabToolsUiResult:
    title: str
    primary_result: str
    detail_text: str
    warnings: tuple[str, ...]
    errors: tuple[str, ...]
    copy_text: str

    @property
    def valid(self) -> bool:
        return not self.errors


@dataclass(frozen=True)
class ReagentTemplateSummary:
    template_id: str
    name: str
    category: str
    default_volume: str
    component_count: int
    ph_target: str
    status_label: str


@dataclass(frozen=True)
class ReagentComponentView:
    name: str
    component_type: str
    amount: str
    stage: str
    notes: str
    warning: str


@dataclass(frozen=True)
class ReagentTemplateDetail:
    summary: ReagentTemplateSummary
    notes: str
    components: tuple[ReagentComponentView, ...]
    ph_target: str
    ph_measured: str
    ph_adjustment_note: str
    validation_rows: tuple[str, ...]


@dataclass(frozen=True)
class ReagentPreparationUiResult:
    title: str
    primary_result: str
    detail_text: str
    component_rows: tuple[ReagentComponentView, ...]
    warnings: tuple[str, ...]
    errors: tuple[str, ...]
    copy_text: str

    @property
    def valid(self) -> bool:
        return not self.errors


@dataclass(frozen=True)
class WBLoadingSampleView:
    sample_id: str
    concentration: str
    note: str


@dataclass(frozen=True)
class WBLoadingResultRowView:
    sample_id: str
    concentration: str
    sample_volume: str
    loading_buffer_volume: str
    diluent_volume: str
    final_volume: str
    status: str
    issues: tuple[str, ...]
    note: str


@dataclass(frozen=True)
class WBLaneView:
    lane_number: int
    lane_type: str
    sample_id: str
    sample_volume: str
    status: str
    issues: tuple[str, ...]


@dataclass(frozen=True)
class WBLoadingUiResult:
    title: str
    primary_result: str
    samples: tuple[WBLoadingSampleView, ...]
    rows: tuple[WBLoadingResultRowView, ...]
    lanes: tuple[WBLaneView, ...]
    warnings: tuple[str, ...]
    errors: tuple[str, ...]
    review_notice: str
    copy_text: str
    detail_text: str

    @property
    def valid(self) -> bool:
        return not self.errors


@dataclass(frozen=True)
class LabToolsStoragePilotResult:
    ok: bool
    message: str
    path: Path | None = None
    record_id: str = ""
    warnings: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()


@dataclass(frozen=True)
class LabToolsHistoryEntry:
    record_id: str
    title: str
    created_at: str
    summary: str
    detail_text: str


@dataclass(frozen=True)
class LabToolsHistoryResult:
    entries: tuple[LabToolsHistoryEntry, ...]
    error: str = ""


@dataclass(frozen=True)
class LabToolsLocalDataStatus:
    status: str
    data_source_mode: str
    read_enabled: bool
    write_enabled: bool
    history_enabled: bool
    export_enabled: bool
    reason: str
    reagent_count: int = 0
    sample_count: int = 0
    cell_count: int = 0
    freeze_vial_count: int = 0
    record_count: int = 0


@dataclass(frozen=True)
class LabToolsLocalReagentSummary:
    reagent_id: str
    name: str
    category: str
    concentration: str
    storage_location: str
    status: str
    version: int


@dataclass(frozen=True)
class LabToolsLocalSampleSummary:
    sample_id: str
    sample_name: str
    sample_type: str
    concentration: str
    concentration_unit: str
    storage_location: str
    status: str
    version: int
    wb_compatible: bool


@dataclass(frozen=True)
class LabToolsLocalCellSummary:
    cell_id: str
    cell_name: str
    passage: int
    species: str
    storage_status: str
    status: str
    version: int


@dataclass(frozen=True)
class LabToolsLocalFreezeVialSummary:
    vial_id: str
    freeze_batch_id: str
    vial_label: str
    location: str
    status: str
    version: int


@dataclass(frozen=True)
class LabToolsLocalRecordSummary:
    record_id: str
    record_type: str
    title: str
    status: str
    linked_reagent_count: int
    linked_sample_count: int
    linked_cell_count: int
    version: int


@dataclass(frozen=True)
class LabToolsLocalDataReadModel:
    status: LabToolsLocalDataStatus
    reagents: tuple[LabToolsLocalReagentSummary, ...] = ()
    samples: tuple[LabToolsLocalSampleSummary, ...] = ()
    wb_samples: tuple[LabToolsLocalSampleSummary, ...] = ()
    cells: tuple[LabToolsLocalCellSummary, ...] = ()
    freeze_vials: tuple[LabToolsLocalFreezeVialSummary, ...] = ()
    freeze_vial_status_rows: tuple[str, ...] = ()
    records: tuple[LabToolsLocalRecordSummary, ...] = ()


def runtime_status() -> LabToolsRuntimeStatus:
    try:
        _ensure_labtools_importable()
        import labtools  # noqa: F401

        return LabToolsRuntimeStatus(True, "LabTools backend specs available")
    except Exception as exc:  # pragma: no cover - defensive optional dependency fallback.
        return LabToolsRuntimeStatus(False, f"LabTools backend unavailable: {exc}")


def get_labtools_storage_adapter_status(project_root: Path | str | None) -> LabToolsStorageAdapterState:
    if project_root is None:
        return LabToolsStorageAdapterState(
            status="missing_project_context",
            message="BioMedPilot project context is required before LabTools save/export/history can be enabled.",
            paths=None,
            save_enabled=False,
            export_enabled=False,
            history_enabled=False,
        )
    return BioMedPilotLabToolsStorageAdapter.from_project_root(Path(project_root)).diagnose()


def labtools_storage_pilot_enabled(project_root: Path | str | None) -> bool:
    return project_root is not None


def get_labtools_local_data_read_model(
    project_root: Path | str | None,
    *,
    data_source_mode: str = "local",
) -> LabToolsLocalDataReadModel:
    status = get_labtools_local_data_status(project_root, data_source_mode=data_source_mode)
    if not status.read_enabled or project_root is None or data_source_mode in {"future_lan", "future_cloud"}:
        return LabToolsLocalDataReadModel(status=status)

    try:
        adapter = _local_data_adapter(project_root, data_source_mode=data_source_mode)
        reagents = tuple(
            LabToolsLocalReagentSummary(
                reagent_id=item.id,
                name=item.name,
                category=item.category,
                concentration=item.concentration,
                storage_location=item.storage_location,
                status=item.status,
                version=item.version,
            )
            for item in adapter.list_reagents()
        )
        samples = tuple(
            LabToolsLocalSampleSummary(
                sample_id=item.id,
                sample_name=item.sample_name,
                sample_type=item.sample_type,
                concentration=item.concentration,
                concentration_unit=item.concentration_unit,
                storage_location=item.storage_location,
                status=item.status,
                version=item.version,
                wb_compatible=_is_wb_compatible_sample(item.sample_type),
            )
            for item in adapter.list_samples()
        )
        cells = tuple(
            LabToolsLocalCellSummary(
                cell_id=item.id,
                cell_name=item.cell_name,
                passage=item.passage,
                species=item.species,
                storage_status=item.storage_status,
                status=item.status,
                version=item.version,
            )
            for item in adapter.list_cells()
        )
        freeze_vials = tuple(
            LabToolsLocalFreezeVialSummary(
                vial_id=item.id,
                freeze_batch_id=item.freeze_batch_id,
                vial_label=item.vial_label,
                location=item.location,
                status=item.status,
                version=item.version,
            )
            for item in adapter.list_freeze_vials()
        )
        records = tuple(
            LabToolsLocalRecordSummary(
                record_id=item.id,
                record_type=item.record_type,
                title=item.title,
                status=item.status,
                linked_reagent_count=len(item.linked_reagents),
                linked_sample_count=len(item.linked_samples),
                linked_cell_count=len(item.linked_cells),
                version=item.version,
            )
            for item in adapter.list_records()
        )
        status = LabToolsLocalDataStatus(
            status=status.status,
            data_source_mode=status.data_source_mode,
            read_enabled=status.read_enabled,
            write_enabled=status.write_enabled,
            history_enabled=status.history_enabled,
            export_enabled=status.export_enabled,
            reason=status.reason,
            reagent_count=len(reagents),
            sample_count=len(samples),
            cell_count=len(cells),
            freeze_vial_count=len(freeze_vials),
            record_count=len(records),
        )
        return LabToolsLocalDataReadModel(
            status=status,
            reagents=reagents,
            samples=samples,
            wb_samples=tuple(sample for sample in samples if sample.wb_compatible),
            cells=cells,
            freeze_vials=freeze_vials,
            freeze_vial_status_rows=_freeze_vial_status_rows(freeze_vials),
            records=records,
        )
    except Exception as exc:
        return LabToolsLocalDataReadModel(
            status=LabToolsLocalDataStatus(
                status="blocked_invalid_store",
                data_source_mode=data_source_mode,
                read_enabled=False,
                write_enabled=False,
                history_enabled=False,
                export_enabled=False,
                reason=f"local_data store unavailable: {exc}",
            )
        )


def get_labtools_local_data_status(
    project_root: Path | str | None,
    *,
    data_source_mode: str = "local",
) -> LabToolsLocalDataStatus:
    _ensure_labtools_importable()
    if project_root is None:
        return LabToolsLocalDataStatus(
            status="missing_project_context",
            data_source_mode=data_source_mode,
            read_enabled=False,
            write_enabled=False,
            history_enabled=False,
            export_enabled=False,
            reason="BioMedPilot project context is required before LabTools local_data can be read.",
        )
    try:
        adapter = _local_data_adapter(project_root, data_source_mode=data_source_mode)
        status = adapter.status()
        return LabToolsLocalDataStatus(
            status=status.status,
            data_source_mode=status.data_source_mode,
            read_enabled=status.read_enabled,
            write_enabled=status.write_enabled,
            history_enabled=status.history_enabled,
            export_enabled=status.export_enabled,
            reason=status.reason,
        )
    except Exception as exc:
        return LabToolsLocalDataStatus(
            status="blocked_invalid_store",
            data_source_mode=data_source_mode,
            read_enabled=False,
            write_enabled=False,
            history_enabled=False,
            export_enabled=False,
            reason=f"local_data adapter unavailable: {exc}",
        )


def list_local_reagent_summaries(project_root: Path | str | None) -> tuple[LabToolsLocalReagentSummary, ...]:
    return get_labtools_local_data_read_model(project_root).reagents


def list_local_wb_sample_summaries(project_root: Path | str | None) -> tuple[LabToolsLocalSampleSummary, ...]:
    return get_labtools_local_data_read_model(project_root).wb_samples


def list_local_cell_summaries(project_root: Path | str | None) -> tuple[LabToolsLocalCellSummary, ...]:
    return get_labtools_local_data_read_model(project_root).cells


def list_quick_tasks() -> tuple[Any, ...]:
    _ensure_labtools_importable()
    from labtools.calculators import list_quick_calculator_tasks

    return tuple(list_quick_calculator_tasks())


def get_quick_task(task_id: str) -> Any:
    _ensure_labtools_importable()
    from labtools.calculators import get_quick_calculator_task

    return get_quick_calculator_task(task_id)


def list_formula_specs() -> tuple[Any, ...]:
    _ensure_labtools_importable()
    from labtools.calculators import list_formula_specs

    return tuple(list_formula_specs())


def get_formula_spec(spec_id: str) -> Any:
    _ensure_labtools_importable()
    from labtools.calculators import get_formula_spec

    return get_formula_spec(spec_id)


def supported_units_for_formula_field(field: Any) -> tuple[str, ...]:
    _ensure_labtools_importable()
    from labtools.calculators import supported_units_for_formula_field

    return tuple(supported_units_for_formula_field(field))


def quick_field_label(field_id: str) -> str:
    return _QUICK_FIELD_LABELS.get(field_id, field_id.replace("_", " "))


def quick_field_default(field_id: str) -> str:
    return _QUICK_FIELD_DEFAULTS.get(field_id, "")


def quick_field_units(field_id: str) -> tuple[str, ...]:
    return _QUICK_FIELD_UNITS.get(field_id, ())


def execute_quick_task(task_id: str, values: dict[str, str], units: dict[str, str]) -> LabToolsUiResult:
    _ensure_labtools_importable()
    from labtools.calculators import (
        CellSeedingInput,
        DilutionInput,
        MassMolarityInput,
        QpcrMixInput,
        WesternBlotLoadingInput,
        calculate_cell_seeding_v1,
        calculate_dilution_v1,
        calculate_mass_molarity_v1,
        calculate_qpcr_mix_v1,
        calculate_western_blot_loading_v1,
        format_cell_seeding_copy_text,
        format_dilution_copy_text,
        format_mass_molarity_copy_text,
        solve_solution_preparation_formula,
    )

    task = get_quick_task(task_id)
    try:
        if task.calculator_name == "calculate_dilution_v1":
            input_data = DilutionInput(
                stock_concentration=_value(values, "stock_concentration"),
                stock_unit=_unit(units, "stock_concentration", "mM"),
                target_concentration=_value(values, "target_concentration"),
                target_unit=_unit(units, "target_concentration", "mM"),
                final_volume=_value(values, "final_volume"),
                final_volume_unit=_unit(units, "final_volume", "mL"),
            )
            result = calculate_dilution_v1(input_data)
            copy_text = format_dilution_copy_text(input_data, result) or result.as_text()
            return _result_from_dataclass(task.title, result, copy_text=copy_text)

        if task.calculator_name == "calculate_mass_molarity_v1":
            input_data = MassMolarityInput(
                molecular_weight=_value(values, "molecular_weight"),
                target_concentration=_value(values, "target_concentration"),
                concentration_unit=_unit(units, "target_concentration", "mM"),
                final_volume=_value(values, "final_volume"),
                volume_unit=_unit(units, "final_volume", "mL"),
                output_mass_unit=_unit(units, "output_mass_unit", "mg"),
            )
            result = calculate_mass_molarity_v1(input_data)
            copy_text = format_mass_molarity_copy_text(input_data, result) or result.as_text()
            return _result_from_dataclass(task.title, result, copy_text=copy_text)

        if task.calculator_name == "calculate_qpcr_mix_v1":
            input_data = QpcrMixInput(
                reactions=_value(values, "reactions"),
                reaction_volume_ul=_value(values, "reaction_volume_ul"),
                master_mix_value=_value(values, "master_mix_value"),
                forward_primer_ul=_value(values, "forward_primer_ul"),
                reverse_primer_ul=_value(values, "reverse_primer_ul"),
                template_ul=_value(values, "template_ul"),
            )
            result = calculate_qpcr_mix_v1(input_data)
            return _result_from_dataclass(task.title, result)

        if task.calculator_name == "calculate_cell_seeding_v1":
            input_data = CellSeedingInput(
                current_cell_concentration=_value(values, "current_cell_concentration"),
                concentration_unit=_unit(units, "current_cell_concentration", "cells/mL"),
                target_cells_per_well=_value(values, "target_cells_per_well"),
                well_count=_value(values, "well_count"),
                volume_per_well=_value(values, "volume_per_well"),
                volume_unit=_unit(units, "volume_per_well", "µL"),
            )
            result = calculate_cell_seeding_v1(input_data)
            copy_text = format_cell_seeding_copy_text(input_data, result) or result.as_text()
            return _result_from_dataclass(f"{task.title}（仅计算辅助）", result, copy_text=copy_text)

        if task.calculator_name == "calculate_western_blot_loading_v1":
            input_data = WesternBlotLoadingInput(
                protein_concentration=_value(values, "protein_concentration"),
                concentration_unit=_unit(units, "protein_concentration", "mg/mL"),
                target_protein_mass_ug=_value(values, "target_protein_mass_ug"),
                final_loading_volume=_value(values, "final_loading_volume"),
                volume_unit=_unit(units, "final_loading_volume", "µL"),
                loading_buffer_x=_value(values, "loading_buffer_x"),
            )
            result = calculate_western_blot_loading_v1(input_data)
            return _result_from_dataclass(task.title, result)

        if task.calculator_name == "solve_solution_preparation_formula":
            result = solve_solution_preparation_formula(
                mass=None,
                mass_unit=_unit(units, "mass", "mg"),
                concentration=_value(values, "concentration"),
                concentration_unit=_unit(units, "concentration", "mM"),
                volume=_value(values, "volume"),
                volume_unit=_unit(units, "volume", "mL"),
                molecular_weight=_value(values, "molecular_weight"),
                unknown_field="mass",
            )
            return _result_from_calculation_result(task.title, result)

        return LabToolsUiResult(
            title=task.title,
            primary_result="暂未接入",
            detail_text=f"该 quick task 的 calculator_name 尚未接入 UI adapter：{task.calculator_name}",
            warnings=(REVIEW_NOTICE,),
            errors=(),
            copy_text="",
        )
    except Exception as exc:
        return _error_result(task.title, exc)


def execute_formula(spec_id: str, solve_target: str, values: dict[str, str], units: dict[str, str]) -> LabToolsUiResult:
    _ensure_labtools_importable()
    from labtools.calculators import (
        calculate_serial_dilution,
        solve_concentration_bridge,
        solve_dilution_equation,
        solve_percent_solution,
        solve_solution_preparation_formula,
        solve_stock_working_solution,
    )

    spec = get_formula_spec(spec_id)
    solvers: dict[str, Callable[..., Any]] = {
        "solve_concentration_bridge": solve_concentration_bridge,
        "solve_dilution_equation": solve_dilution_equation,
        "solve_stock_working_solution": solve_stock_working_solution,
        "solve_solution_preparation_formula": solve_solution_preparation_formula,
        "solve_percent_solution": solve_percent_solution,
        "calculate_serial_dilution": calculate_serial_dilution,
    }
    try:
        solver = solvers[spec.solver_name]
        kwargs = _formula_solver_kwargs(spec.solver_name, solve_target, values, units)
        result = solver(**kwargs)
        return _result_from_calculation_result(spec.short_title, result)
    except Exception as exc:
        return _error_result(spec.short_title, exc)


def list_reagent_templates(project_root: Path | str | None = None) -> tuple[ReagentTemplateSummary, ...]:
    stored = _load_stored_reagent_templates(project_root)
    if stored:
        return tuple(_reagent_template_summary_from_payload(template) for template in stored)
    templates = _demo_reagent_templates()
    return tuple(_reagent_template_summary(template) for template in templates)


def get_reagent_template_detail(template_id: str, project_root: Path | str | None = None) -> ReagentTemplateDetail:
    stored = _stored_reagent_template_by_id(project_root, template_id)
    if stored is not None:
        summary = _reagent_template_summary_from_payload(stored)
        components = tuple(
            ReagentComponentView(
                name=str(component.get("name", "")),
                component_type=str(component.get("component_type", "")),
                amount=f"{component.get('base_amount', '')} {component.get('unit', '')}".strip(),
                stage=str(component.get("stage_label", "") or "默认"),
                notes=str(component.get("notes", "")),
                warning=str(component.get("warning", "")),
            )
            for component in stored.get("components", ())
            if isinstance(component, dict)
        )
        validation_rows = tuple(str(row) for row in stored.get("validation_rows", ()) if row)
        return ReagentTemplateDetail(
            summary=summary,
            notes=str(stored.get("notes", "")),
            components=components,
            ph_target=str(stored.get("ph_target", "")),
            ph_measured=str(stored.get("ph_measured", "")),
            ph_adjustment_note=str(stored.get("ph_adjustment_note", "")),
            validation_rows=validation_rows or ("项目存储模板；使用前需人工复核。",),
        )

    template = _get_demo_reagent_template(template_id)
    summary = _reagent_template_summary(template)
    components = tuple(
        ReagentComponentView(
            name=component.name,
            component_type=component.component_type,
            amount=f"{component.base_amount:g} {component.unit}",
            stage=component.stage_label or "默认",
            notes=component.notes,
            warning="水合物形式需人工确认" if component.name == "Na2HPO4" else "",
        )
        for component in template.components
    )
    ph_record = template.ph_record
    validation_rows = (
        "Na2HPO4：水合物形式需人工确认。",
        "KH2PO4：称量量由模板换算，使用前需复核 SOP。",
        "保存模板需要 BioMedPilotLabToolsStorageAdapter。",
    )
    return ReagentTemplateDetail(
        summary=summary,
        notes=template.notes,
        components=components,
        ph_target=ph_record.target_ph if ph_record else "",
        ph_measured=ph_record.measured_ph if ph_record else "",
        ph_adjustment_note=ph_record.adjustment_note if ph_record else "",
        validation_rows=validation_rows,
    )


def save_reagent_template_to_project(project_root: Path | str | None, template_id: str = "demo_pbs_1x") -> LabToolsStoragePilotResult:
    paths_result = _pilot_storage_paths(project_root)
    if not paths_result.ok or paths_result.path is None:
        return paths_result
    try:
        template = _get_demo_reagent_template(template_id)
        payload = _reagent_template_payload(template)
        path = paths_result.path / "reagent_templates.json"
        data = _read_json_payload(path, default={"version": "labtools_reagent_templates_v1", "templates": []})
        templates = [item for item in data.get("templates", ()) if isinstance(item, dict)]
        duplicate = any(item.get("template_id") == template_id for item in templates)
        templates = [item for item in templates if item.get("template_id") != template_id]
        templates.append(payload)
        data["templates"] = templates
        _write_json_payload(path, data)
        warnings = ("Duplicate template ID was safely updated.",) if duplicate else ()
        message = "已保存到项目存储 / Saved to project storage"
        if duplicate:
            message = "已安全更新项目存储模板 / Saved duplicate template by safe update"
        return LabToolsStoragePilotResult(ok=True, message=message, path=path, record_id=template_id, warnings=warnings)
    except Exception as exc:
        return LabToolsStoragePilotResult(ok=False, message="保存模板失败", errors=(str(exc),))


def calculate_reagent_preparation(
    *,
    template_id: str,
    target_volume: str,
    target_volume_unit: str,
    operator_name: str = "",
    measured_ph: str = "",
    adjustment_note: str = "",
) -> ReagentPreparationUiResult:
    _ensure_labtools_importable()
    from labtools.reagent_templates import PreparationRequest, calculate_preparation

    templates = _demo_reagent_templates(measured_ph=measured_ph, adjustment_note=adjustment_note)
    try:
        request = PreparationRequest(
            template_id=template_id,
            target_volume=float(target_volume),
            target_volume_unit=target_volume_unit or "mL",
            target_strength="1X",
            operator_name=operator_name,
            notes="UI-C2d preview only; not saved.",
        )
        result = calculate_preparation(request, templates)
        component_rows = tuple(
            ReagentComponentView(
                name=component.name,
                component_type=component.component_type,
                amount=component.display_amount,
                stage=component.stage_label or "默认",
                notes=component.notes or component.initial_addition_detail,
                warning="; ".join(component.warnings),
            )
            for component in result.direct_components
        )
        warnings = tuple(dict.fromkeys((*tuple(result.warnings or ()), REVIEW_NOTICE, "保存模板和配制记录需要存储适配；当前不会写入 ~/.labtools。")))
        return ReagentPreparationUiResult(
            title=result.title,
            primary_result=f"{result.template_name}: {result.suggested_volume:g} {result.suggested_volume_unit}",
            detail_text=result.as_text(),
            component_rows=component_rows,
            warnings=warnings,
            errors=(),
            copy_text=result.as_text(),
        )
    except Exception as exc:
        return ReagentPreparationUiResult(
            title="本次试剂配制",
            primary_result="输入需要调整",
            detail_text="",
            component_rows=(),
            warnings=(REVIEW_NOTICE,),
            errors=(str(exc),),
            copy_text="",
        )


def save_reagent_preparation_record(
    project_root: Path | str | None,
    *,
    template_id: str,
    target_volume: str,
    target_volume_unit: str,
    operator_name: str,
    measured_ph: str,
    adjustment_note: str,
    result: ReagentPreparationUiResult,
) -> LabToolsStoragePilotResult:
    paths_result = _pilot_storage_paths(project_root)
    if not paths_result.ok or paths_result.path is None:
        return paths_result
    if not result.valid:
        return LabToolsStoragePilotResult(ok=False, message="当前预览包含错误，不能保存记录。", errors=result.errors)
    try:
        path = paths_result.path.parent / "records" / "reagent_preparations.json"
        data = _read_json_payload(path, default={"version": "labtools_reagent_preparations_v1", "records": []})
        records = [item for item in data.get("records", ()) if isinstance(item, dict)]
        record_id = _new_record_id("reagent-prep")
        records.append(
            {
                "record_id": record_id,
                "record_type": "reagent_preparation",
                "created_at": _utc_now(),
                "template_id": template_id,
                "operator_name": operator_name,
                "input_parameters": {
                    "target_volume": target_volume,
                    "target_volume_unit": target_volume_unit,
                    "measured_ph": measured_ph,
                    "adjustment_note": adjustment_note,
                },
                "primary_result": result.primary_result,
                "detail_text": result.detail_text,
                "warnings": list(result.warnings),
                "review_notice": REVIEW_NOTICE,
                "storage_status": "saved_to_biomedpilot_project_storage",
            }
        )
        data["records"] = records
        _write_json_payload(path, data)
        return LabToolsStoragePilotResult(ok=True, message="已保存到项目存储 / Saved to project storage", path=path, record_id=record_id)
    except Exception as exc:
        return LabToolsStoragePilotResult(ok=False, message="保存配制记录失败", errors=(str(exc),))


def export_reagent_preparation_markdown(file_path: Path | str, result: ReagentPreparationUiResult) -> LabToolsStoragePilotResult:
    if not result.valid:
        return LabToolsStoragePilotResult(ok=False, message="当前预览包含错误，不能导出。", errors=result.errors)
    path = Path(file_path).expanduser().resolve()
    content = "\n".join(
        (
            "# BioMedPilot LabTools Reagent Preparation",
            "",
            "## Result",
            result.primary_result,
            "",
            "## Components",
            result.detail_text,
            "",
            "## Warnings",
            "\n".join(f"- {warning}" for warning in result.warnings) or "- None",
            "",
            "## Review Notice",
            REVIEW_NOTICE,
            "",
        )
    )
    return _write_export_text(path, content, expected_suffix=".md")


def export_reagent_preparation_csv(file_path: Path | str, result: ReagentPreparationUiResult) -> LabToolsStoragePilotResult:
    if not result.valid:
        return LabToolsStoragePilotResult(ok=False, message="当前预览包含错误，不能导出。", errors=result.errors)
    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["stage", "name", "component_type", "amount", "notes", "warning"])
    for component in result.component_rows:
        writer.writerow([component.stage, component.name, component.component_type, component.amount, component.notes, component.warning])
    writer.writerow([])
    writer.writerow(["review_notice", REVIEW_NOTICE])
    return _write_export_text(Path(file_path).expanduser().resolve(), buffer.getvalue(), expected_suffix=".csv")


def load_reagent_preparation_history(project_root: Path | str | None) -> LabToolsHistoryResult:
    path = _records_file(project_root, "reagent_preparations.json")
    if path is None or not path.exists():
        return LabToolsHistoryResult(entries=())
    try:
        data = _read_json_payload(path, default={"records": []})
        entries = tuple(
            LabToolsHistoryEntry(
                record_id=str(item.get("record_id", "")),
                title=str(item.get("primary_result", "Reagent preparation")),
                created_at=str(item.get("created_at", "")),
                summary=f"{item.get('template_id', '')} · {item.get('operator_name', '')}".strip(" ·"),
                detail_text=str(item.get("detail_text", "")),
            )
            for item in data.get("records", ())
            if isinstance(item, dict)
        )
        return LabToolsHistoryResult(entries=entries)
    except Exception as exc:
        return LabToolsHistoryResult(entries=(), error=f"项目存储 JSON 读取失败：{exc}")


def calculate_wb_loading_preview(
    *,
    target_protein_ug: str = "20",
    loading_buffer_factor: str = "4",
    final_volume_ul: str = "20",
    reducing_agent_enabled: bool = True,
    lane_count: str | int = 10,
    local_samples: tuple[LabToolsLocalSampleSummary, ...] = (),
) -> WBLoadingUiResult:
    _ensure_labtools_importable()
    from labtools.western_blot.calculator import calculate_wb_loading
    from labtools.western_blot.models import WBLoadingConfig, WBSampleInput

    try:
        samples = _wb_sample_inputs_from_local_samples(local_samples) or (
            WBSampleInput(sample_name="S1", concentration_ug_per_ul=2.0, note="control"),
            WBSampleInput(sample_name="S2", concentration_ug_per_ul=1.5, note="treatment low"),
            WBSampleInput(sample_name="S3", concentration_ug_per_ul=0.8, note="treatment high"),
        )
        config = WBLoadingConfig(
            experiment_name="Protein Experiment / WB 上样计算",
            target_protein_ug=float(target_protein_ug),
            final_volume_ul=float(final_volume_ul),
            loading_buffer_factor=float(loading_buffer_factor),
            reducing_agent_mode="none",
            reducing_agent_name="Yes" if reducing_agent_enabled else "",
            marker_enabled=True,
            marker_name="Marker",
            marker_volume_ul=5,
            lane_count_mode="fixed",
            fixed_lane_count=int(lane_count),
            min_pipette_volume_ul=0.5,
        )
        result = calculate_wb_loading(config, samples)
        sample_views = tuple(
            WBLoadingSampleView(
                sample_id=sample.sample_name,
                concentration=f"{sample.concentration_ug_per_ul:g} µg/µL",
                note=sample.note,
            )
            for sample in samples
        )
        row_views = tuple(
            WBLoadingResultRowView(
                sample_id=row.sample_name,
                concentration=f"{row.concentration_ug_per_ul:g} µg/µL",
                sample_volume=f"{row.sample_volume_ul:.1f} µL",
                loading_buffer_volume=f"{row.loading_buffer_volume_ul:.1f} µL",
                diluent_volume=f"{row.diluent_volume_ul:.1f} µL",
                final_volume=f"{row.final_volume_ul:.1f} µL",
                status=row.status,
                issues=tuple(row.errors or row.warnings),
                note=row.note,
            )
            for row in result.rows
        )
        lane_views = tuple(
            WBLaneView(
                lane_number=lane.lane_index,
                lane_type=lane.lane_type,
                sample_id=lane.sample_name if lane.lane_type != "empty" else "Empty / 空白",
                sample_volume=_lane_sample_volume_text(lane),
                status="Error" if lane.errors else ("Warning" if lane.warnings else ("Empty" if lane.lane_type == "empty" else "OK")),
                issues=tuple(lane.errors or lane.warnings),
            )
            for lane in result.lanes
        )
        errors = tuple(issue for row in result.rows for issue in row.errors)
        warnings = tuple(
            dict.fromkeys(
                (
                    *tuple(issue for row in result.rows for issue in row.warnings),
                    *tuple(result.summary_warnings or ()),
                    "上样计算结果需由实验人员复核后用于台面操作。",
                    "此页不提供图像分析、自动条带识别、抗体推荐或完整 WB 协议。",
                )
            )
        )
        return WBLoadingUiResult(
            title="Western Blot Loading",
            primary_result="WB 上样计算预览：S3 存在体积异常" if errors else "WB 上样计算预览",
            samples=sample_views,
            rows=row_views,
            lanes=lane_views,
            warnings=warnings,
            errors=errors,
            review_notice=result.review_notice,
            copy_text=result.as_text(),
            detail_text=result.as_text(),
        )
    except Exception as exc:
        return WBLoadingUiResult(
            title="Western Blot Loading",
            primary_result="输入需要调整",
            samples=(),
            rows=(),
            lanes=(),
            warnings=("上样计算结果需由实验人员复核后用于台面操作。",),
            errors=(str(exc),),
            review_notice="",
            copy_text="",
            detail_text="",
        )


def save_wb_loading_record(project_root: Path | str | None, *, result: WBLoadingUiResult) -> LabToolsStoragePilotResult:
    paths_result = _pilot_storage_paths(project_root)
    if not paths_result.ok or paths_result.path is None:
        return paths_result
    try:
        path = paths_result.path.parent / "records" / "wb_loading_records.json"
        data = _read_json_payload(path, default={"version": "labtools_wb_loading_records_v1", "records": []})
        records = [item for item in data.get("records", ()) if isinstance(item, dict)]
        record_id = _new_record_id("wb-loading")
        records.append(
            {
                "record_id": record_id,
                "record_type": "wb_loading",
                "created_at": _utc_now(),
                "title": result.title,
                "primary_result": result.primary_result,
                "samples": [sample.__dict__ for sample in result.samples],
                "rows": [row.__dict__ for row in result.rows],
                "lanes": [lane.__dict__ for lane in result.lanes],
                "warnings": list(result.warnings),
                "errors": list(result.errors),
                "review_notice": result.review_notice or REVIEW_NOTICE,
                "detail_text": result.detail_text,
                "copy_text": result.copy_text,
                "storage_status": "saved_to_biomedpilot_project_storage",
            }
        )
        data["records"] = records
        _write_json_payload(path, data)
        return LabToolsStoragePilotResult(ok=True, message="已保存到项目存储 / Saved to project storage", path=path, record_id=record_id)
    except Exception as exc:
        return LabToolsStoragePilotResult(ok=False, message="保存 WB 记录失败", errors=(str(exc),))


def export_wb_loading_markdown(file_path: Path | str, result: WBLoadingUiResult) -> LabToolsStoragePilotResult:
    path = Path(file_path).expanduser().resolve()
    rows = "\n".join(
        f"- {row.sample_id}: sample {row.sample_volume}, buffer {row.loading_buffer_volume}, water {row.diluent_volume}, status {row.status}"
        for row in result.rows
    )
    lanes = "\n".join(f"- Lane {lane.lane_number}: {lane.sample_id} {lane.sample_volume} ({lane.status})" for lane in result.lanes)
    content = "\n".join(
        (
            "# BioMedPilot LabTools WB Loading",
            "",
            "## Result",
            result.primary_result,
            "",
            "## Loading Table",
            rows,
            "",
            "## Lane Preview",
            lanes,
            "",
            "## Warnings",
            "\n".join(f"- {warning}" for warning in result.warnings) or "- None",
            "",
            "## Review Notice",
            result.review_notice or REVIEW_NOTICE,
            "",
        )
    )
    return _write_export_text(path, content, expected_suffix=".md")


def export_wb_loading_csv(file_path: Path | str, result: WBLoadingUiResult) -> LabToolsStoragePilotResult:
    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["sample_id", "concentration", "sample_volume", "loading_buffer_volume", "diluent_volume", "final_volume", "status", "issues"])
    for row in result.rows:
        writer.writerow(
            [
                row.sample_id,
                row.concentration,
                row.sample_volume,
                row.loading_buffer_volume,
                row.diluent_volume,
                row.final_volume,
                row.status,
                "; ".join(row.issues),
            ]
        )
    writer.writerow([])
    writer.writerow(["lane_number", "lane_type", "sample_id", "sample_volume", "status", "issues"])
    for lane in result.lanes:
        writer.writerow([lane.lane_number, lane.lane_type, lane.sample_id, lane.sample_volume, lane.status, "; ".join(lane.issues)])
    writer.writerow([])
    writer.writerow(["review_notice", result.review_notice or REVIEW_NOTICE])
    return _write_export_text(Path(file_path).expanduser().resolve(), buffer.getvalue(), expected_suffix=".csv")


def load_wb_loading_history(project_root: Path | str | None) -> LabToolsHistoryResult:
    path = _records_file(project_root, "wb_loading_records.json")
    if path is None or not path.exists():
        return LabToolsHistoryResult(entries=())
    try:
        data = _read_json_payload(path, default={"records": []})
        entries = tuple(
            LabToolsHistoryEntry(
                record_id=str(item.get("record_id", "")),
                title=str(item.get("primary_result", "WB loading")),
                created_at=str(item.get("created_at", "")),
                summary=str(item.get("title", "Western Blot Loading")),
                detail_text=str(item.get("detail_text", "")),
            )
            for item in data.get("records", ())
            if isinstance(item, dict)
        )
        return LabToolsHistoryResult(entries=entries)
    except Exception as exc:
        return LabToolsHistoryResult(entries=(), error=f"项目存储 JSON 读取失败：{exc}")


def _pilot_storage_paths(project_root: Path | str | None) -> LabToolsStoragePilotResult:
    if project_root is None:
        return LabToolsStoragePilotResult(ok=False, message="missing_project_context：保存历史需要 BioMedPilot project context。")
    adapter = BioMedPilotLabToolsStorageAdapter.from_project_root(Path(project_root))
    state = adapter.ensure_readiness(create_missing=True)
    if state.paths is None:
        return LabToolsStoragePilotResult(ok=False, message=state.message, errors=tuple(error.user_message for error in state.errors))
    if state.status != "ready_read_only":
        return LabToolsStoragePilotResult(ok=False, message=state.message, path=state.paths.templates, errors=tuple(error.user_message for error in state.errors))
    return LabToolsStoragePilotResult(ok=True, message=state.message, path=state.paths.templates)


def _records_file(project_root: Path | str | None, filename: str) -> Path | None:
    if project_root is None:
        return None
    paths = BioMedPilotLabToolsStorageAdapter.from_project_root(Path(project_root)).resolve_paths()
    return paths.records / filename


def _local_data_root(project_root: Path | str) -> Path:
    return BioMedPilotLabToolsStorageAdapter.from_project_root(Path(project_root)).resolve_paths().labtools_root


def _local_data_adapter(project_root: Path | str, *, data_source_mode: str = "local") -> Any:
    _ensure_labtools_importable()
    from labtools.local_data import (
        FutureCloudDataSourceAdapter,
        FutureLanDataSourceAdapter,
        LocalLabToolsDataSourceAdapter,
        ReadOnlyLabToolsDataSourceAdapter,
    )

    if data_source_mode == "readonly":
        return ReadOnlyLabToolsDataSourceAdapter(_local_data_root(project_root))
    if data_source_mode == "future_lan":
        return FutureLanDataSourceAdapter()
    if data_source_mode == "future_cloud":
        return FutureCloudDataSourceAdapter()
    return LocalLabToolsDataSourceAdapter(_local_data_root(project_root))


def _is_wb_compatible_sample(sample_type: str) -> bool:
    return sample_type in {"protein_lysate", "protein", "lysate"}


def _freeze_vial_status_rows(freeze_vials: tuple[LabToolsLocalFreezeVialSummary, ...]) -> tuple[str, ...]:
    counts: dict[str, int] = {}
    for vial in freeze_vials:
        counts[vial.status] = counts.get(vial.status, 0) + 1
    return tuple(f"{status}: {count}" for status, count in sorted(counts.items())) or ("No freeze vials in local_data.",)


def _wb_sample_inputs_from_local_samples(local_samples: tuple[LabToolsLocalSampleSummary, ...]) -> tuple[Any, ...]:
    if not local_samples:
        return ()
    _ensure_labtools_importable()
    from labtools.western_blot.models import WBSampleInput

    inputs = []
    for sample in local_samples:
        concentration = _parse_protein_concentration_as_ug_per_ul(sample.concentration, sample.concentration_unit)
        if concentration is None:
            continue
        inputs.append(
            WBSampleInput(
                sample_name=sample.sample_name or sample.sample_id,
                concentration_ug_per_ul=concentration,
                note=f"local_data:{sample.sample_id}; no sample volume deduction",
            )
        )
    return tuple(inputs)


def _parse_protein_concentration_as_ug_per_ul(value: str, unit: str) -> float | None:
    try:
        concentration = float(value)
    except (TypeError, ValueError):
        return None
    normalized_unit = unit.strip().lower().replace("μ", "µ")
    if normalized_unit in {"µg/µl", "ug/ul", "mg/ml"}:
        return concentration
    if normalized_unit in {"ng/µl", "ng/ul"}:
        return concentration / 1000
    return None


def _load_stored_reagent_templates(project_root: Path | str | None) -> tuple[dict[str, Any], ...]:
    if project_root is None:
        return ()
    path = BioMedPilotLabToolsStorageAdapter.from_project_root(Path(project_root)).resolve_paths().templates / "reagent_templates.json"
    if not path.exists():
        return ()
    data = _read_json_payload(path, default={"templates": []})
    return tuple(item for item in data.get("templates", ()) if isinstance(item, dict))


def _stored_reagent_template_by_id(project_root: Path | str | None, template_id: str) -> dict[str, Any] | None:
    for template in _load_stored_reagent_templates(project_root):
        if template.get("template_id") == template_id:
            return template
    return None


def _reagent_template_payload(template: Any) -> dict[str, Any]:
    ph_record = getattr(template, "ph_record", None)
    return {
        "template_id": template.template_id,
        "name": template.name,
        "category": "缓冲液 / buffer",
        "default_volume": template.default_volume,
        "default_volume_unit": template.default_volume_unit,
        "default_strength": template.default_strength,
        "notes": template.notes,
        "ph_target": ph_record.target_ph if ph_record else "",
        "ph_measured": ph_record.measured_ph if ph_record else "",
        "ph_adjustment_note": ph_record.adjustment_note if ph_record else "",
        "components": [
            {
                "name": component.name,
                "component_type": component.component_type,
                "base_amount": component.base_amount,
                "unit": component.unit,
                "stage_label": component.stage_label or "默认",
                "notes": component.notes,
                "warning": "水合物形式需人工确认" if component.name == "Na2HPO4" else "",
            }
            for component in template.components
        ],
        "validation_rows": [
            "Na2HPO4：水合物形式需人工确认。",
            "KH2PO4：称量量由模板换算，使用前需复核 SOP。",
            "项目存储模板；不连接库存、云模板或批次放行。",
        ],
        "storage_status": "saved_to_biomedpilot_project_storage",
    }


def _reagent_template_summary_from_payload(template: dict[str, Any]) -> ReagentTemplateSummary:
    volume = template.get("default_volume", "")
    unit = template.get("default_volume_unit", "")
    components = template.get("components", ())
    return ReagentTemplateSummary(
        template_id=str(template.get("template_id", "")),
        name=str(template.get("name", "")),
        category=str(template.get("category", "缓冲液 / buffer")),
        default_volume=f"{volume:g} {unit}" if isinstance(volume, int | float) else f"{volume} {unit}".strip(),
        component_count=len(components) if isinstance(components, list) else 0,
        ph_target=str(template.get("ph_target", "")),
        status_label="saved_to_project_storage / review_required",
    )


def _read_json_payload(path: Path, *, default: dict[str, Any]) -> dict[str, Any]:
    if not path.exists():
        return dict(default)
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"{path.name} must contain a JSON object")
    return payload


def _write_json_payload(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")


def _write_export_text(path: Path, content: str, *, expected_suffix: str) -> LabToolsStoragePilotResult:
    if path.suffix.lower() != expected_suffix:
        return LabToolsStoragePilotResult(ok=False, message=f"导出文件后缀必须为 {expected_suffix}", path=path)
    if _is_home_labtools_path(path):
        return LabToolsStoragePilotResult(ok=False, message="拒绝写入 ~/.labtools；请选择 BioMedPilot 项目或用户指定路径。", path=path)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return LabToolsStoragePilotResult(ok=True, message="已通过文件选择器导出 / Exported via file picker", path=path)
    except OSError as exc:
        return LabToolsStoragePilotResult(ok=False, message="导出失败", path=path, errors=(str(exc),))


def _is_home_labtools_path(path: Path) -> bool:
    home_labtools = (Path.home() / ".labtools").expanduser().resolve()
    try:
        path.resolve().relative_to(home_labtools)
    except ValueError:
        return False
    return True


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _new_record_id(prefix: str) -> str:
    return f"{prefix}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{uuid4().hex[:8]}"


def _ensure_labtools_importable() -> None:
    if LABTOOLS_SIBLING_ROOT.exists():
        root = str(LABTOOLS_SIBLING_ROOT)
        if root not in sys.path:
            sys.path.insert(0, root)


def _formula_solver_kwargs(solver_name: str, solve_target: str, values: dict[str, str], units: dict[str, str]) -> dict[str, Any]:
    field_values = {field_id: (None if field_id == solve_target else _value(values, field_id)) for field_id in values}
    if solver_name == "solve_concentration_bridge":
        return {
            "mass_concentration": field_values.get("mass_concentration"),
            "mass_unit": _unit(units, "mass_concentration", "mg/mL"),
            "molar_concentration": field_values.get("molar_concentration"),
            "molar_unit": _unit(units, "molar_concentration", "mM"),
            "molecular_weight": field_values.get("molecular_weight"),
            "unknown_field": solve_target,
        }
    if solver_name == "solve_dilution_equation":
        return {
            "stock_concentration": field_values.get("stock_concentration"),
            "stock_unit": _unit(units, "stock_concentration", "mM"),
            "stock_volume": field_values.get("stock_volume"),
            "stock_volume_unit": _unit(units, "stock_volume", "µL"),
            "target_concentration": field_values.get("target_concentration"),
            "target_unit": _unit(units, "target_concentration", "mM"),
            "final_volume": field_values.get("final_volume"),
            "final_volume_unit": _unit(units, "final_volume", "mL"),
            "molecular_weight": field_values.get("molecular_weight"),
            "unknown_field": solve_target,
        }
    if solver_name == "solve_stock_working_solution":
        return {
            "stock_strength": field_values.get("stock_concentration"),
            "target_strength": field_values.get("target_concentration") or 1,
            "final_volume": field_values.get("final_volume"),
            "final_volume_unit": _unit(units, "final_volume", "mL"),
            "output_volume_unit": _unit(units, "final_volume", "µL"),
        }
    if solver_name == "solve_solution_preparation_formula":
        return {
            "mass": field_values.get("mass"),
            "mass_unit": _unit(units, "mass", "mg"),
            "concentration": field_values.get("concentration"),
            "concentration_unit": _unit(units, "concentration", "mM"),
            "volume": field_values.get("volume"),
            "volume_unit": _unit(units, "volume", "mL"),
            "molecular_weight": field_values.get("molecular_weight"),
            "unknown_field": solve_target,
        }
    if solver_name == "solve_percent_solution":
        return {
            "percent": field_values.get("percent"),
            "percent_type": field_values.get("percent_type") or "w/v",
            "solute_amount": field_values.get("solute_amount"),
            "solute_unit": _unit(units, "solute_amount", "g"),
            "total_amount": field_values.get("total_amount"),
            "total_unit": _unit(units, "total_amount", "mL"),
            "unknown_field": solve_target,
        }
    if solver_name == "calculate_serial_dilution":
        return {
            "initial_concentration": field_values.get("start_concentration"),
            "concentration_unit": _unit(units, "start_concentration", "mM"),
            "dilution_factor": field_values.get("dilution_factor"),
            "levels": field_values.get("levels"),
            "final_volume": field_values.get("final_volume_per_level"),
            "final_volume_unit": _unit(units, "final_volume_per_level", "µL"),
        }
    raise KeyError(f"Unsupported solver: {solver_name}")


def _result_from_dataclass(title: str, result: Any, *, copy_text: str | None = None) -> LabToolsUiResult:
    errors = tuple(getattr(result, "errors", ()) or ())
    warnings = tuple(dict.fromkeys((*tuple(getattr(result, "warnings", ()) or ()), REVIEW_NOTICE)))
    detail_text = result.as_text() if hasattr(result, "as_text") else str(result)
    return LabToolsUiResult(
        title=title,
        primary_result=getattr(result, "summary", "") or title,
        detail_text=detail_text,
        warnings=warnings,
        errors=errors,
        copy_text=copy_text if copy_text is not None else detail_text,
    )


def _result_from_calculation_result(title: str, result: Any) -> LabToolsUiResult:
    warnings = tuple(dict.fromkeys((*tuple(getattr(result, "warnings", ()) or ()), REVIEW_NOTICE)))
    detail_text = result.as_text() if hasattr(result, "as_text") else str(result)
    primary = "\n".join(getattr(result, "result_lines", ()) or ()) or title
    return LabToolsUiResult(
        title=title,
        primary_result=primary,
        detail_text=detail_text,
        warnings=warnings,
        errors=(),
        copy_text=detail_text,
    )


def _error_result(title: str, exc: Exception) -> LabToolsUiResult:
    return LabToolsUiResult(
        title=title,
        primary_result="输入需要调整",
        detail_text="",
        warnings=(REVIEW_NOTICE,),
        errors=(str(exc),),
        copy_text="",
    )


def _value(values: dict[str, str], field_id: str) -> str | None:
    value = values.get(field_id, "")
    return value if value != "" else None


def _unit(units: dict[str, str], field_id: str, default: str) -> str:
    return units.get(field_id) or default


def _demo_reagent_templates(*, measured_ph: str = "", adjustment_note: str = "") -> tuple[Any, ...]:
    _ensure_labtools_importable()
    from labtools.reagent_templates import PHRecord, ReagentComponent, ReagentTemplate

    ph_note = adjustment_note or "必要时用 HCl/NaOH 微调；软件不预测酸碱加入量。"
    return (
        ReagentTemplate(
            template_id="demo_pbs_1x",
            name="PBS 1x 示例模板",
            default_volume=1000,
            default_volume_unit="mL",
            default_strength="1X",
            notes="UI-C2d in-memory demo template; not stored and not linked to inventory.",
            components=(
                ReagentComponent(name="NaCl", component_type="powder", base_amount=8.0, unit="g", stage_label="称量", addition_order=1),
                ReagentComponent(name="KCl", component_type="powder", base_amount=0.2, unit="g", stage_label="称量", addition_order=2),
                ReagentComponent(name="Na2HPO4", component_type="powder", base_amount=1.44, unit="g", stage_label="称量", addition_order=3, notes="水合物形式需复核"),
                ReagentComponent(name="KH2PO4", component_type="powder", base_amount=0.24, unit="g", stage_label="称量", addition_order=4),
                ReagentComponent(
                    name="ddH2O",
                    component_type="solvent",
                    base_amount=1000,
                    unit="mL",
                    contributes_to_final_volume=True,
                    auto_fill_to_final_volume=True,
                    stage_label="定容",
                    addition_order=5,
                    initial_addition_mode="percent_of_final",
                    initial_addition_percent=80,
                    initial_addition_note="先加约 80% 体积，溶解后定容。",
                ),
            ),
            ph_record=PHRecord(target_ph="7.4", measured_ph=measured_ph, adjustment_note=ph_note),
        ),
    )


def _get_demo_reagent_template(template_id: str) -> Any:
    templates = _demo_reagent_templates()
    for template in templates:
        if template.template_id == template_id:
            return template
    raise KeyError(f"Unknown reagent template: {template_id}")


def _reagent_template_summary(template: Any) -> ReagentTemplateSummary:
    ph_record = getattr(template, "ph_record", None)
    return ReagentTemplateSummary(
        template_id=template.template_id,
        name=template.name,
        category="缓冲液 / buffer",
        default_volume=f"{template.default_volume:g} {template.default_volume_unit}",
        component_count=len(template.components),
        ph_target=ph_record.target_ph if ph_record else "",
        status_label="demo_preview / storage_adapter_needed",
    )


def _lane_sample_volume_text(lane: Any) -> str:
    if lane.lane_type == "marker":
        return f"{lane.marker_volume_ul:g} µL"
    if lane.result_row is None:
        return ""
    return f"{lane.result_row.sample_volume_ul:.1f} µL"


_QUICK_FIELD_LABELS: dict[str, str] = {
    "stock_concentration": "Stock 浓度",
    "target_concentration": "目标浓度",
    "final_volume": "终体积",
    "molecular_weight": "分子量 MW",
    "output_mass_unit": "输出质量单位",
    "mass": "称量质量（输出）",
    "concentration": "目标浓度",
    "volume": "终体积",
    "reactions": "反应数",
    "reaction_volume_ul": "单反应体积",
    "master_mix_value": "Master mix 体积",
    "forward_primer_ul": "Forward primer",
    "reverse_primer_ul": "Reverse primer",
    "template_ul": "Template / cDNA",
    "current_cell_concentration": "当前细胞浓度",
    "target_cells_per_well": "目标每孔细胞数",
    "well_count": "孔数",
    "volume_per_well": "每孔体积",
    "protein_concentration": "蛋白浓度",
    "target_protein_mass_ug": "目标蛋白量",
    "final_loading_volume": "终上样体积",
    "loading_buffer_x": "Loading buffer 倍数",
}

_QUICK_FIELD_DEFAULTS: dict[str, str] = {
    "stock_concentration": "100",
    "target_concentration": "10",
    "final_volume": "1",
    "molecular_weight": "180.16",
    "output_mass_unit": "",
    "mass": "",
    "concentration": "100",
    "volume": "10",
    "reactions": "24",
    "reaction_volume_ul": "20",
    "master_mix_value": "10",
    "forward_primer_ul": "0.8",
    "reverse_primer_ul": "0.8",
    "template_ul": "2",
    "current_cell_concentration": "1000000",
    "target_cells_per_well": "5000",
    "well_count": "24",
    "volume_per_well": "100",
    "protein_concentration": "2",
    "target_protein_mass_ug": "20",
    "final_loading_volume": "20",
    "loading_buffer_x": "4",
}

_QUICK_FIELD_UNITS: dict[str, tuple[str, ...]] = {
    "stock_concentration": ("mM", "µM", "M", "mg/mL", "µg/µL"),
    "target_concentration": ("mM", "µM", "M", "mg/mL", "µg/µL"),
    "final_volume": ("mL", "µL", "L", "nL"),
    "molecular_weight": ("g/mol",),
    "output_mass_unit": ("mg", "µg", "g", "ng"),
    "mass": ("mg", "µg", "g", "ng"),
    "concentration": ("mM", "µM", "M", "mg/mL"),
    "volume": ("mL", "µL", "L"),
    "reaction_volume_ul": ("µL",),
    "master_mix_value": ("µL",),
    "forward_primer_ul": ("µL",),
    "reverse_primer_ul": ("µL",),
    "template_ul": ("µL",),
    "current_cell_concentration": ("cells/mL", "cells/µL"),
    "volume_per_well": ("µL", "mL"),
    "protein_concentration": ("mg/mL", "µg/µL"),
    "final_loading_volume": ("µL", "mL"),
}
