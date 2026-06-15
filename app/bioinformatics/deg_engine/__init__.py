from __future__ import annotations

from .dependency_check import check_deg_backend_dependencies
from .confirmation import load_deg_parameter_confirmation, save_deg_parameter_confirmation, validate_deg_parameter_confirmation
from .parameter_gate import build_deg_parameter_manifest, validate_deg_parameter_manifest
from .multifactor_gate import build_multifactor_deg_preflight_manifest, validate_multifactor_deg_preflight_manifest
from .r_adapter_contract import (
    build_r_deg_adapter_contract,
    build_r_deg_runtime_gate,
    build_r_deg_runtime_gate_matrix,
    validate_r_deg_output_schema,
    validate_r_deg_result_registration_bundle,
)
from .r_backend_handoff import (
    build_r_deg_external_handoff_plan,
    register_r_limma_external_handoff_result,
)
from .rscript_adapter import (
    detect_r_limma_runtime_capabilities,
    resolve_rscript_path,
    run_r_limma_rscript_execution,
)
from .r_limma_confirmation import (
    build_r_limma_parameter_manifest,
    load_r_limma_design_config,
    load_r_limma_parameter_confirmation,
    save_r_limma_parameter_confirmation,
    validate_r_limma_parameter_confirmation,
    validate_r_limma_parameter_manifest,
)
from .r_limma_design import (
    build_r_limma_design_config,
    save_r_limma_design_config,
)
from .r_count_model_planning import build_r_count_model_activation_plan, build_r_count_model_activation_plans
from .r_deseq2_planning import (
    build_r_deseq2_dry_run_acceptance_gate,
    build_r_deseq2_parameter_manifest,
    build_r_deseq2_rscript_adapter_plan,
    load_r_deseq2_parameter_confirmation,
    validate_r_deseq2_count_fixture,
    save_r_deseq2_parameter_confirmation,
    validate_r_deseq2_parameter_confirmation,
    validate_r_deseq2_parameter_manifest,
)
from .r_deseq2_runtime import detect_r_deseq2_runtime_capabilities, run_r_deseq2_rscript_execution
from .r_deseq2_runtime_validation import run_r_deseq2_runtime_validation
from .r_edger_planning import (
    build_r_edger_parameter_manifest,
    build_r_edger_rscript_adapter_plan,
    load_r_edger_parameter_confirmation,
    save_r_edger_parameter_confirmation,
    validate_r_edger_parameter_confirmation,
    validate_r_edger_parameter_manifest,
)
from .r_edger_runtime import detect_r_edger_runtime_capabilities, run_r_edger_rscript_execution
from .r_edger_runtime_validation import run_r_edger_runtime_validation
from .formal_runner import run_formal_controlled_deg
from .input_adaptation import build_deg_input_adaptation_gate
from .python_backend import run_controlled_deg
from .result_schema import build_formal_deg_result_schema_gate, validate_deg_result_bundle, validate_deg_result_entry, validate_formal_deg_result_index_entry

__all__ = [
    "build_deg_parameter_manifest",
    "build_deg_input_adaptation_gate",
    "build_formal_deg_result_schema_gate",
    "build_multifactor_deg_preflight_manifest",
    "build_r_deg_adapter_contract",
    "build_r_deg_external_handoff_plan",
    "build_r_limma_parameter_manifest",
    "build_r_limma_design_config",
    "build_r_count_model_activation_plan",
    "build_r_count_model_activation_plans",
    "build_r_deseq2_dry_run_acceptance_gate",
    "build_r_deseq2_parameter_manifest",
    "build_r_deseq2_rscript_adapter_plan",
    "build_r_edger_parameter_manifest",
    "build_r_edger_rscript_adapter_plan",
    "build_r_deg_runtime_gate",
    "build_r_deg_runtime_gate_matrix",
    "check_deg_backend_dependencies",
    "detect_r_limma_runtime_capabilities",
    "detect_r_deseq2_runtime_capabilities",
    "detect_r_edger_runtime_capabilities",
    "load_deg_parameter_confirmation",
    "load_r_limma_design_config",
    "load_r_limma_parameter_confirmation",
    "load_r_deseq2_parameter_confirmation",
    "load_r_edger_parameter_confirmation",
    "run_formal_controlled_deg",
    "run_controlled_deg",
    "save_deg_parameter_confirmation",
    "save_r_limma_design_config",
    "save_r_limma_parameter_confirmation",
    "save_r_deseq2_parameter_confirmation",
    "save_r_edger_parameter_confirmation",
    "register_r_limma_external_handoff_result",
    "resolve_rscript_path",
    "run_r_limma_rscript_execution",
    "run_r_deseq2_rscript_execution",
    "run_r_deseq2_runtime_validation",
    "run_r_edger_rscript_execution",
    "run_r_edger_runtime_validation",
    "validate_deg_result_bundle",
    "validate_deg_result_entry",
    "validate_deg_parameter_manifest",
    "validate_deg_parameter_confirmation",
    "validate_formal_deg_result_index_entry",
    "validate_multifactor_deg_preflight_manifest",
    "validate_r_limma_parameter_confirmation",
    "validate_r_limma_parameter_manifest",
    "validate_r_deseq2_parameter_confirmation",
    "validate_r_deseq2_parameter_manifest",
    "validate_r_deseq2_count_fixture",
    "validate_r_edger_parameter_confirmation",
    "validate_r_edger_parameter_manifest",
    "validate_r_deg_output_schema",
    "validate_r_deg_result_registration_bundle",
]
