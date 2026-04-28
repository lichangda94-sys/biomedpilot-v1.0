from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

from app.meta_analysis.models.analysis_dataset import StudyAnalysisRow
from app.meta_analysis.models.analysis_result import StudyMetaAnalysisResult
from app.meta_analysis.services.advanced_analysis_service import SMALL_STUDY_BIAS_WARNING, _egger_test
from app.meta_analysis.stats.meta_effects import (
    ci_to_standard_error,
    diagnostic_accuracy_metrics,
    diagnostic_ratio_variance,
    fisher_z_back_transform,
    fisher_z_transform,
    proportion_effect,
    study_effect_from_row,
)
from app.meta_analysis.stats.meta_models import pool_effects


FIXTURE_PATH = Path("tests/fixtures/meta_stats/reference_cases.json")


@pytest.fixture(scope="module")
def reference_cases() -> dict[str, object]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def test_binary_effect_references(reference_cases: dict[str, object]) -> None:
    binary = reference_cases["binary"]
    for measure in ("OR", "RR", "RD"):
        case = binary[measure]
        effect = study_effect_from_row(_binary_row(measure, case))
        _assert_effect_matches(effect, case)


def test_zero_event_correction_reference_warning(reference_cases: dict[str, object]) -> None:
    case = reference_cases["binary"]["zero_event_OR"]
    effect = study_effect_from_row(_binary_row("OR", case))

    _assert_effect_matches(effect, case)
    assert case["expected_warning"] in effect.warnings


def test_continuous_effect_references(reference_cases: dict[str, object]) -> None:
    continuous = reference_cases["continuous"]
    for measure in ("MD", "SMD"):
        case = continuous[measure]
        effect = study_effect_from_row(_continuous_row(measure, case))
        _assert_effect_matches(effect, case)


def test_generic_hr_ci_to_se_reference(reference_cases: dict[str, object]) -> None:
    case = reference_cases["generic_inverse_variance"]["HR"]
    standard_error = ci_to_standard_error(case["ci_lower"], case["ci_upper"], log_scale=True)
    effect = study_effect_from_row(
        StudyAnalysisRow(
            study_id="study-hr",
            record_id="rec-hr",
            first_author="HR Study",
            year=2023,
            outcome_name="Survival",
            effect_measure="HR",
            outcome_data_type="generic_effect",
            raw_data={},
            normalized_data={
                "effect": case["effect"],
                "ci_lower": case["ci_lower"],
                "ci_upper": case["ci_upper"],
                "standard_error": None,
                "p_value": None,
                "adjusted": True,
                "covariates": ["age"],
                "effect_measure": "HR",
            },
            analysis_status="included",
        )
    )

    assert standard_error == pytest.approx(case["standard_error"], abs=1e-12)
    assert effect.transformed_effect == pytest.approx(case["theta"], abs=1e-12)
    assert effect.standard_error == pytest.approx(case["standard_error"], abs=1e-12)
    assert effect.adjusted is True
    assert effect.covariates == ["age"]


def test_fixed_random_pooling_and_heterogeneity_reference(reference_cases: dict[str, object]) -> None:
    case = reference_cases["pooling"]["OR_three_study"]
    effects = [study_effect_from_row(_binary_row("OR", item)) for item in case["studies"]]

    fixed = pool_effects(effects, effect_measure="OR", model="fixed")
    random = pool_effects(effects, effect_measure="OR", model="random")

    for pooled, expected in ((fixed, case["fixed"]), (random, case["random"])):
        assert pooled.pooled_effect == pytest.approx(expected["pooled_effect"], abs=1e-12)
        assert pooled.ci_lower == pytest.approx(expected["ci_lower"], abs=1e-12)
        assert pooled.ci_upper == pytest.approx(expected["ci_upper"], abs=1e-12)
        assert pooled.q_statistic == pytest.approx(expected["q_statistic"], abs=1e-12)
        assert pooled.i_squared == pytest.approx(expected["i_squared"], abs=1e-12)
        assert pooled.tau_squared == pytest.approx(expected["tau_squared"], abs=1e-12)


def test_prevalence_fisher_z_and_diagnostic_metric_references(reference_cases: dict[str, object]) -> None:
    advanced = reference_cases["advanced"]
    prevalence = advanced["prevalence"]
    theta, variance, warnings = proportion_effect(prevalence["events"], prevalence["total"], measure="PREVALENCE")
    assert warnings == []
    assert theta == pytest.approx(prevalence["theta"], abs=1e-12)
    assert math.sqrt(variance) == pytest.approx(prevalence["standard_error"], abs=1e-12)

    correlation = advanced["correlation"]
    assert fisher_z_transform(correlation["r"]) == pytest.approx(correlation["theta"], abs=1e-12)
    assert fisher_z_back_transform(correlation["theta"]) == pytest.approx(correlation["effect"], abs=1e-12)

    diagnostic = advanced["diagnostic"]
    metrics = diagnostic_accuracy_metrics(tp=diagnostic["tp"], fp=diagnostic["fp"], fn=diagnostic["fn"], tn=diagnostic["tn"])
    assert metrics.sensitivity == pytest.approx(diagnostic["sensitivity"], abs=1e-12)
    assert metrics.specificity == pytest.approx(diagnostic["specificity"], abs=1e-12)
    assert metrics.plr == pytest.approx(diagnostic["plr"], abs=1e-12)
    assert metrics.nlr == pytest.approx(diagnostic["nlr"], abs=1e-12)
    assert metrics.dor == pytest.approx(diagnostic["dor"], abs=1e-12)
    variance = diagnostic_ratio_variance(
        tp=diagnostic["tp"],
        fp=diagnostic["fp"],
        fn=diagnostic["fn"],
        tn=diagnostic["tn"],
        measure="DOR",
    )
    assert math.log(metrics.dor) == pytest.approx(diagnostic["theta_dor"], abs=1e-12)
    assert math.sqrt(variance) == pytest.approx(diagnostic["standard_error_dor"], abs=1e-12)


def test_egger_reference_and_small_sample_warning(reference_cases: dict[str, object]) -> None:
    expected = reference_cases["advanced"]["egger"]
    rows = [
        StudyMetaAnalysisResult("s1", "r1", "A", 2020, 0.44, 0.2, 1.0, 0.4166666667, 0.1736111111, 1.0, -0.8109302162),
        StudyMetaAnalysisResult("s2", "r2", "B", 2021, 0.52, 0.25, 1.1, 0.39, 0.1521, 1.0, -0.6539264674),
        StudyMetaAnalysisResult("s3", "r3", "C", 2022, 0.61, 0.31, 1.2, 0.34, 0.1156, 1.0, -0.4942963218),
        StudyMetaAnalysisResult("s4", "r4", "D", 2023, 0.78, 0.40, 1.5, 0.33, 0.1089, 1.0, -0.2484613593),
    ]

    egger = _egger_test(rows)

    assert egger["intercept"] == pytest.approx(expected["intercept"], abs=1e-12)
    assert egger["slope"] == pytest.approx(expected["slope"], abs=1e-12)
    assert egger["p_value"] == pytest.approx(expected["p_value"], abs=1e-12)
    assert SMALL_STUDY_BIAS_WARNING == "Publication bias tests are unreliable when the number of studies is small."


def _binary_row(measure: str, case: dict[str, object]) -> StudyAnalysisRow:
    return StudyAnalysisRow(
        study_id=f"study-{measure}",
        record_id=f"record-{measure}",
        first_author="Reference",
        year=2024,
        outcome_name="Mortality",
        effect_measure=measure,
        outcome_data_type="binary",
        raw_data={},
        normalized_data={
            "experimental_events": case["experimental_events"],
            "experimental_non_events": case["experimental_total"] - case["experimental_events"],
            "experimental_total": case["experimental_total"],
            "control_events": case["control_events"],
            "control_non_events": case["control_total"] - case["control_events"],
            "control_total": case["control_total"],
            "effect_measure": measure,
        },
        analysis_status="included",
    )


def _continuous_row(measure: str, case: dict[str, object]) -> StudyAnalysisRow:
    return StudyAnalysisRow(
        study_id=f"study-{measure}",
        record_id=f"record-{measure}",
        first_author="Reference",
        year=2024,
        outcome_name="Change",
        effect_measure=measure,
        outcome_data_type="continuous",
        raw_data={},
        normalized_data={
            "experimental_mean": case["experimental_mean"],
            "experimental_sd": case["experimental_sd"],
            "experimental_total": case["experimental_total"],
            "control_mean": case["control_mean"],
            "control_sd": case["control_sd"],
            "control_total": case["control_total"],
            "effect_measure": measure,
        },
        analysis_status="included",
    )


def _assert_effect_matches(effect, expected: dict[str, object]) -> None:
    assert effect.transformed_effect == pytest.approx(expected["theta"], abs=1e-12)
    assert effect.standard_error == pytest.approx(expected["standard_error"], abs=1e-12)
    assert effect.effect == pytest.approx(expected["effect"], abs=1e-12)
    assert effect.ci_lower == pytest.approx(expected["ci_lower"], abs=1e-12)
    assert effect.ci_upper == pytest.approx(expected["ci_upper"], abs=1e-12)

