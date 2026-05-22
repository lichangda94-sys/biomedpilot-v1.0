from __future__ import annotations

from pathlib import Path

from app.bioinformatics.clinical_analysis import build_clinical_association_preflight, build_survival_package
from app.bioinformatics.survival_clinical import build_cox_multivariate_parameter_manifest


def test_cox_multivariate_parameter_manifest_passes_controlled_design(tmp_path: Path) -> None:
    manifest = _manifest(tmp_path)

    assert manifest["status"] == "passed"
    assert manifest["events_per_variable"] >= 10
    assert manifest["model_formula_manifest"]["formula"] == "Surv(time, event) ~ age + marker"
    assert manifest["provenance"]["risk_score_generated"] is False
    assert "risk_score" not in str(manifest["output_plan"]) if "output_plan" in manifest else True


def test_cox_multivariate_parameter_gate_blocks_low_event_count(tmp_path: Path) -> None:
    clinical = tmp_path / "clinical.tsv"
    clinical.write_text(
        "sample_id\tOS_time\tOS_event\tage\tmarker\n"
        "S1\t5\t1\t50\t0\nS2\t8\t0\t55\t1\nS3\t12\t1\t60\t0\nS4\t6\t0\t65\t1\n",
        encoding="utf-8",
    )
    manifest = _manifest_from_clinical(tmp_path, clinical, ["age", "marker"])

    assert manifest["status"] == "blocked"
    assert "minimum_event_count_not_met" in manifest["blockers"]
    assert "events_per_variable_not_met" in manifest["blockers"]


def test_cox_multivariate_parameter_gate_blocks_too_many_variables_for_events(tmp_path: Path) -> None:
    clinical = _clinical_fixture(tmp_path, extra_column=True)
    manifest = _manifest_from_clinical(tmp_path, clinical, ["age", "marker", "burden"])

    assert manifest["status"] == "blocked"
    assert "events_per_variable_not_met" in manifest["blockers"]


def test_cox_multivariate_parameter_gate_blocks_high_missingness(tmp_path: Path) -> None:
    clinical = _clinical_fixture(tmp_path, missing_marker=True)
    manifest = _manifest_from_clinical(tmp_path, clinical, ["age", "marker"])

    assert manifest["status"] == "blocked"
    assert "missingness_too_high:marker" in manifest["blockers"]


def test_cox_multivariate_parameter_gate_records_collinearity(tmp_path: Path) -> None:
    clinical = _clinical_fixture(tmp_path, collinear=True)
    manifest = _manifest_from_clinical(tmp_path, clinical, ["age", "age_clone"])

    assert manifest["status"] == "blocked"
    assert "collinearity_unresolved" in manifest["blockers"]
    assert manifest["collinearity_report"]["high_correlation_pairs"]


def test_cox_multivariate_parameter_gate_blocks_missing_dependency(tmp_path: Path) -> None:
    clinical = _clinical_fixture(tmp_path)
    manifest = _manifest_from_clinical(tmp_path, clinical, ["age", "marker"], dependency={"status": "preflight_only", "blockers": ["lifelines_missing_formal_survival_disabled"]})

    assert manifest["status"] == "blocked"
    assert "dependency_snapshot_not_passed" in manifest["blockers"]


def _manifest(tmp_path: Path) -> dict[str, object]:
    return _manifest_from_clinical(tmp_path, _clinical_fixture(tmp_path), ["age", "marker"])


def _manifest_from_clinical(tmp_path: Path, clinical: Path, selected: list[str], *, dependency: dict[str, object] | None = None) -> dict[str, object]:
    rows = _read_rows(clinical)
    package = build_survival_package({"input_package_id": "pkg", "clinical_asset": {"path": str(clinical)}})
    audit = build_clinical_association_preflight(rows)
    return build_cox_multivariate_parameter_manifest(
        package,
        outcome_gate={"status": "passed", "survival_outcome_gate_id": "outcome-1", "blockers": []},
        clinical_variable_audit=audit,
        selected_covariates=selected,
        dependency_snapshot=dependency or {"status": "passed", "python_lifelines": {"available": True, "version": "test"}},
    )


def _clinical_fixture(tmp_path: Path, *, extra_column: bool = False, missing_marker: bool = False, collinear: bool = False) -> Path:
    path = tmp_path / "clinical.tsv"
    header = ["sample_id", "OS_time", "OS_event", "age", "marker"]
    if extra_column:
        header.append("burden")
    if collinear:
        header.append("age_clone")
    lines = ["\t".join(header)]
    for index in range(24):
        event = "0" if index in {3, 8, 15, 22} else "1"
        marker = "" if missing_marker and index < 11 else str(index % 2)
        row = [f"S{index + 1}", str(5 + index), event, str(40 + index), marker]
        if extra_column:
            row.append(str((index * 3) % 11))
        if collinear:
            row.append(str(41 + index))
        lines.append("\t".join(row))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def _read_rows(path: Path) -> list[dict[str, str]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    header = lines[0].split("\t")
    return [dict(zip(header, line.split("\t"), strict=False)) for line in lines[1:]]
