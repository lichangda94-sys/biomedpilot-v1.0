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
from .formal_runner import run_formal_controlled_deg
from .python_backend import run_controlled_deg
from .result_schema import build_formal_deg_result_schema_gate, validate_deg_result_bundle, validate_deg_result_entry, validate_formal_deg_result_index_entry

__all__ = [
    "build_deg_parameter_manifest",
    "build_formal_deg_result_schema_gate",
    "build_multifactor_deg_preflight_manifest",
    "build_r_deg_adapter_contract",
    "build_r_deg_external_handoff_plan",
    "build_r_deg_runtime_gate",
    "build_r_deg_runtime_gate_matrix",
    "check_deg_backend_dependencies",
    "load_deg_parameter_confirmation",
    "run_formal_controlled_deg",
    "run_controlled_deg",
    "save_deg_parameter_confirmation",
    "register_r_limma_external_handoff_result",
    "validate_deg_result_bundle",
    "validate_deg_result_entry",
    "validate_deg_parameter_manifest",
    "validate_deg_parameter_confirmation",
    "validate_formal_deg_result_index_entry",
    "validate_multifactor_deg_preflight_manifest",
    "validate_r_deg_output_schema",
    "validate_r_deg_result_registration_bundle",
]
