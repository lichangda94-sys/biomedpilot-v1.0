from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
from string import Template
from typing import Any, Mapping


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_DIR = REPO_ROOT / "config" / "bioinformatics"
DEFAULT_TEMPLATE_PATH = REPO_ROOT / "reporting" / "templates" / "bioinformatics_standard_report.md.j2"
DEFAULT_REPORT_NAME = "bioinformatics_standard_report.md"
CONFIG_SNAPSHOT_RELATIVE_PATH = Path("reproducibility") / "config_snapshot" / "bioinformatics_config_snapshot.yaml"

DEFAULT_RISK_WARNINGS = (
    "DESeq2 requires raw integer counts. Rounded non-count expression matrices should not be used as default input.",
    "Enrichment universe/background uses mapped expressed genes by default unless user provides a custom universe.",
    "Example thesis genes are not hard-coded software defaults.",
    "Missing font family uses system_or_sans fallback.",
    "Missing plot size uses software plotting defaults.",
)


@dataclass(frozen=True)
class StandardReportResult:
    markdown_path: Path
    config_snapshot_path: Path
    markdown: str
    warnings: tuple[str, ...]


def load_bioinformatics_configs(config_dir: Path | str | None = None) -> dict[str, Any]:
    config_root = Path(config_dir) if config_dir is not None else DEFAULT_CONFIG_DIR
    configs: dict[str, Any] = {}
    for path in sorted(config_root.glob("*.yaml")):
        configs[path.stem] = load_yaml_file(path)
    return configs


def generate_standard_report(
    analysis_result: Mapping[str, Any] | None = None,
    output_dir: Path | str = "results",
    config_dir: Path | str | None = None,
    template_path: Path | str | None = None,
) -> StandardReportResult:
    result = dict(analysis_result or {})
    configs = load_bioinformatics_configs(config_dir)
    output_root = Path(output_dir)
    report_dir = output_root / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)

    snapshot_path = output_root / CONFIG_SNAPSHOT_RELATIVE_PATH
    snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    snapshot = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "config_source": str(Path(config_dir) if config_dir is not None else DEFAULT_CONFIG_DIR),
        "configs": configs,
    }
    snapshot_path.write_text(dump_yaml(snapshot), encoding="utf-8")

    markdown, warnings = render_standard_report_markdown(
        result,
        configs=configs,
        config_snapshot_path=snapshot_path,
        template_path=Path(template_path) if template_path is not None else DEFAULT_TEMPLATE_PATH,
    )

    markdown_path = report_dir / str(result.get("report_filename") or DEFAULT_REPORT_NAME)
    markdown_path.write_text(markdown, encoding="utf-8")

    return StandardReportResult(
        markdown_path=markdown_path,
        config_snapshot_path=snapshot_path,
        markdown=markdown,
        warnings=tuple(warnings),
    )


def render_standard_report_markdown(
    analysis_result: Mapping[str, Any] | None,
    configs: Mapping[str, Any] | None = None,
    config_snapshot_path: Path | None = None,
    template_path: Path | str = DEFAULT_TEMPLATE_PATH,
) -> tuple[str, list[str]]:
    result = dict(analysis_result or {})
    config_map = dict(configs or load_bioinformatics_configs())
    warnings = collect_warnings(result)
    context = build_template_context(result, config_map, warnings, config_snapshot_path)
    template_text = Path(template_path).read_text(encoding="utf-8")
    return render_template_text(template_text, context), warnings


def collect_warnings(analysis_result: Mapping[str, Any]) -> list[str]:
    warnings: list[str] = []
    for warning in DEFAULT_RISK_WARNINGS:
        if warning not in warnings:
            warnings.append(warning)
    for warning in _as_list(analysis_result.get("warnings")):
        text = str(warning)
        if text and text not in warnings:
            warnings.append(text)
    requested_formats = {str(fmt).lower() for fmt in _as_list(analysis_result.get("requested_output_formats"))}
    if {"docx", "pdf"} & requested_formats:
        warnings.append("DOCX/PDF export is not available in standard report v1; Markdown was generated.")
    return warnings


def build_template_context(
    analysis_result: Mapping[str, Any],
    configs: Mapping[str, Any],
    warnings: list[str],
    config_snapshot_path: Path | None,
) -> dict[str, str]:
    title = str(analysis_result.get("title") or "Bioinformatics Standard Report")
    return {
        "title": title,
        "project_summary": _section(analysis_result.get("project_summary") or analysis_result.get("project")),
        "dataset_summary": _section(analysis_result.get("dataset_summary") or analysis_result.get("datasets")),
        "input_files": _section(analysis_result.get("input_files")),
        "sample_annotation_and_grouping": _section(
            analysis_result.get("sample_annotation_and_grouping")
            or analysis_result.get("sample_annotation")
            or analysis_result.get("grouping")
        ),
        "analysis_workflow": _section(analysis_result.get("analysis_workflow") or analysis_result.get("workflow")),
        "parameter_summary": _parameter_summary(analysis_result.get("parameters"), configs),
        "differential_expression_results": _section(
            analysis_result.get("differential_expression_results") or analysis_result.get("differential_expression")
        ),
        "target_gene_expression_results": _section(
            analysis_result.get("target_gene_expression_results") or analysis_result.get("target_gene_expression")
        ),
        "correlation_results": _section(analysis_result.get("correlation_results") or analysis_result.get("correlation")),
        "enrichment_gsea_results": _section(
            analysis_result.get("enrichment_gsea_results")
            or analysis_result.get("enrichment")
            or analysis_result.get("gsea")
        ),
        "survival_analysis_results": _section(
            analysis_result.get("survival_analysis_results") or analysis_result.get("survival")
        ),
        "figures": _artifact_section(analysis_result.get("figures")),
        "tables": _artifact_section(analysis_result.get("tables")),
        "warnings_and_limitations": _bullet_list(warnings),
        "reproducibility_information": _reproducibility_section(analysis_result, config_snapshot_path),
        "software_configuration_snapshot": _config_snapshot_summary(configs, config_snapshot_path),
    }


def render_template_text(template_text: str, context: Mapping[str, str]) -> str:
    rendered = template_text
    for key, value in context.items():
        rendered = rendered.replace("{{ " + key + " }}", value)
        rendered = rendered.replace("{{" + key + "}}", value)
    if "{{" in rendered or "{%" in rendered:
        return Template(rendered.replace("{{", "$").replace("}}", "")).safe_substitute(context)
    return rendered.rstrip() + "\n"


def load_yaml_file(path: Path | str) -> dict[str, Any]:
    text = Path(path).read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore
    except Exception:
        return parse_simple_yaml(text)
    loaded = yaml.safe_load(text)
    return dict(loaded or {})


def parse_simple_yaml(text: str) -> dict[str, Any]:
    root: dict[str, Any] = {}
    stack: list[tuple[int, dict[str, Any]]] = [(-1, root)]
    for raw_line in text.splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        indent = len(raw_line) - len(raw_line.lstrip(" "))
        line = raw_line.strip()
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip().strip("\"'")
        value = value.strip()
        while indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]
        if not value:
            child: dict[str, Any] = {}
            parent[key] = child
            stack.append((indent, child))
        else:
            parent[key] = _parse_scalar(value)
    return root


def dump_yaml(value: Any, indent: int = 0) -> str:
    lines = _dump_yaml_lines(value, indent)
    return "\n".join(lines) + "\n"


def _dump_yaml_lines(value: Any, indent: int = 0) -> list[str]:
    prefix = " " * indent
    if isinstance(value, Mapping):
        lines: list[str] = []
        for key, item in value.items():
            if isinstance(item, Mapping):
                lines.append(f"{prefix}{key}:")
                lines.extend(_dump_yaml_lines(item, indent + 2))
            elif isinstance(item, list):
                lines.append(f"{prefix}{key}: {_format_scalar(item)}")
            else:
                lines.append(f"{prefix}{key}: {_format_scalar(item)}")
        return lines
    return [f"{prefix}{_format_scalar(value)}"]


def _parse_scalar(value: str) -> Any:
    if value == "null":
        return None
    if value == "true":
        return True
    if value == "false":
        return False
    if value in {"Inf", ".inf", "+.inf"}:
        return "Inf"
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [_parse_scalar(part.strip()) for part in _split_inline_list(inner)]
    if (value.startswith("\"") and value.endswith("\"")) or (value.startswith("'") and value.endswith("'")):
        return value[1:-1]
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        return value


def _split_inline_list(value: str) -> list[str]:
    parts: list[str] = []
    current: list[str] = []
    quote: str | None = None
    for char in value:
        if char in {"'", "\""}:
            quote = None if quote == char else char if quote is None else quote
        if char == "," and quote is None:
            parts.append("".join(current))
            current = []
        else:
            current.append(char)
    parts.append("".join(current))
    return parts


def _format_scalar(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, list):
        return "[" + ", ".join(_format_scalar(item) for item in value) + "]"
    text = str(value)
    if not text or any(char in text for char in [":", "#", "[", "]", "{", "}", ","]) or text.lower() in {"true", "false", "null"}:
        return json.dumps(text)
    return text


def _section(value: Any) -> str:
    if _is_empty(value):
        return "Not available in this run."
    if isinstance(value, str):
        return value
    if isinstance(value, Mapping):
        return _mapping_list(value)
    if isinstance(value, list):
        return _list_section(value)
    return str(value)


def _parameter_summary(parameters: Any, configs: Mapping[str, Any]) -> str:
    lines: list[str] = []
    if not _is_empty(parameters):
        lines.append(_section(parameters))
    plotting = configs.get("plotting_defaults", {})
    analysis = configs.get("analysis_defaults", {})
    enrichment = configs.get("enrichment_defaults", {})
    lines.append("")
    lines.append("Software defaults loaded for this report:")
    lines.append(f"- p_adjust_method: {_get_nested(analysis, 'global', 'p_adjust_method') or 'BH'}")
    lines.append(f"- output_format: {_get_nested(plotting, 'output', 'output_format') or 'png'}")
    lines.append(f"- dpi: {_get_nested(plotting, 'output', 'dpi') or 300}")
    lines.append(f"- font_family: {_get_nested(plotting, 'font', 'font_family') or 'system_or_sans'}")
    lines.append(f"- enrichment_universe: {_get_nested(enrichment, 'universe', 'default') or 'mapped_expressed_genes'}")
    return "\n".join(line for line in lines if line is not None).strip()


def _artifact_section(value: Any) -> str:
    if _is_empty(value):
        return "Not available in this run."
    return _section(value)


def _reproducibility_section(analysis_result: Mapping[str, Any], config_snapshot_path: Path | None) -> str:
    items = {
        "analysis_id": analysis_result.get("analysis_id", "Not provided"),
        "generated_by": "bioinformatics standard report v1",
        "config_snapshot": str(config_snapshot_path) if config_snapshot_path else "Not written during render-only mode",
    }
    return _mapping_list(items)


def _config_snapshot_summary(configs: Mapping[str, Any], config_snapshot_path: Path | None) -> str:
    config_names = ", ".join(sorted(configs.keys())) or "None"
    path = str(config_snapshot_path) if config_snapshot_path else "Not written during render-only mode"
    return f"- Config files loaded: {config_names}\n- Snapshot path: {path}"


def _mapping_list(value: Mapping[str, Any]) -> str:
    lines: list[str] = []
    for key, item in value.items():
        label = str(key).replace("_", " ")
        if isinstance(item, Mapping):
            lines.append(f"- {label}:")
            for sub_key, sub_item in item.items():
                lines.append(f"  - {str(sub_key).replace('_', ' ')}: {_inline_value(sub_item)}")
        elif isinstance(item, list):
            lines.append(f"- {label}: {_inline_value(item)}")
        else:
            lines.append(f"- {label}: {_inline_value(item)}")
    return "\n".join(lines) if lines else "Not available in this run."


def _list_section(value: list[Any]) -> str:
    if not value:
        return "Not available in this run."
    lines: list[str] = []
    for item in value:
        if isinstance(item, Mapping):
            summary = ", ".join(f"{key}: {_inline_value(val)}" for key, val in item.items())
            lines.append(f"- {summary}")
        else:
            lines.append(f"- {item}")
    return "\n".join(lines)


def _bullet_list(values: list[str] | tuple[str, ...]) -> str:
    return "\n".join(f"- {value}" for value in values) if values else "Not available in this run."


def _inline_value(value: Any) -> str:
    if isinstance(value, list):
        return ", ".join(str(item) for item in value) if value else "none"
    if isinstance(value, Mapping):
        return "; ".join(f"{key}={_inline_value(item)}" for key, item in value.items())
    if value is None:
        return "null"
    return str(value)


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def _is_empty(value: Any) -> bool:
    return value is None or value == "" or value == [] or value == {}


def _get_nested(value: Any, *keys: str) -> Any:
    current = value
    for key in keys:
        if not isinstance(current, Mapping):
            return None
        current = current.get(key)
    return current
