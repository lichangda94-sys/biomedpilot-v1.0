from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from typing import Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class GeoStudyTextInput:
    accession: str
    title_en: str = ""
    summary_en: str = ""
    overall_design_en: str = ""


@dataclass(frozen=True)
class GeoStudyTextSummary:
    accession: str
    status: str
    title_zh: str = ""
    summary_zh: str = ""
    overall_design_zh: str = ""
    brief_zh: str = ""
    translate_model: str = ""
    brief_model: str = ""
    error_message: str = ""
    model_status: dict[str, str] = field(default_factory=dict)
    quality_warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


class GeoTextSummaryService:
    """Optional local-model text processing for GEO candidate metadata.

    The service keeps the old standalone GEO tool's two-step behavior but makes
    it an optional mainline dependency: callers get a non-failing status when
    the local model endpoint is unavailable.
    """

    def __init__(
        self,
        *,
        base_url: str = "http://127.0.0.1:11434",
        translate_model: str = "translategemma",
        brief_model: str = "medgemma:4b",
        timeout: int = 30,
        generator: Callable[[str, str], str] | None = None,
        availability_checker: Callable[[], bool] | None = None,
        model_names_provider: Callable[[], tuple[str, ...] | list[str] | set[str]] | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.translate_model = translate_model
        self.brief_model = brief_model
        self.timeout = timeout
        self._generator = generator
        self._availability_checker = availability_checker
        self._model_names_provider = model_names_provider

    def is_available(self) -> bool:
        status = self.model_availability()
        return status.get("translate_model_status") == "available" and status.get("brief_model_status") == "available"

    def model_availability(self) -> dict[str, str]:
        if self._availability_checker is not None:
            status = "available" if self._availability_checker() else "unavailable"
            return {
                "ollama": status,
                "translate_model": self.translate_model,
                "translate_model_status": status,
                "brief_model": self.brief_model,
                "brief_model_status": status,
            }
        names = self._available_model_names()
        if names is None:
            return {
                "ollama": "unavailable",
                "translate_model": self.translate_model,
                "translate_model_status": "unavailable",
                "brief_model": self.brief_model,
                "brief_model_status": "unavailable",
            }
        translate_available = _model_name_available(self.translate_model, names)
        brief_available = _model_name_available(self.brief_model, names)
        return {
            "ollama": "available",
            "translate_model": self.translate_model,
            "translate_model_status": "available" if translate_available else "missing",
            "brief_model": self.brief_model,
            "brief_model_status": "available" if brief_available else "missing",
        }

    def _available_model_names(self) -> set[str] | None:
        if self._model_names_provider is not None:
            return {str(name).strip() for name in self._model_names_provider() if str(name).strip()}
        request = Request(f"{self.base_url}/api/tags", method="GET")
        try:
            with urlopen(request, timeout=min(self.timeout, 5)) as response:  # nosec B310 - user-configured local model endpoint.
                if not 200 <= int(response.status) < 300:
                    return None
                payload = json.loads(response.read().decode("utf-8"))
        except (OSError, HTTPError, URLError, json.JSONDecodeError):
            return None
        names: set[str] = set()
        for item in payload.get("models", []) if isinstance(payload, dict) else []:
            if isinstance(item, dict):
                name = str(item.get("name") or item.get("model") or "").strip()
                if name:
                    names.add(name)
        return names

    def summarize(self, text: GeoStudyTextInput) -> GeoStudyTextSummary:
        model_status = self.model_availability()
        if model_status.get("translate_model_status") != "available" or model_status.get("brief_model_status") != "available":
            return GeoStudyTextSummary(
                accession=text.accession,
                status="local_model_unavailable",
                translate_model=self.translate_model,
                brief_model=self.brief_model,
                error_message=_model_status_error(model_status),
                model_status=model_status,
            )
        try:
            translated = self._translate_fields(text)
            brief, warnings = self._build_brief(text, translated)
            warnings = (*_translation_quality_warnings(text, translated), *warnings, *_brief_quality_warnings(text, translated, brief))
        except Exception as exc:
            return GeoStudyTextSummary(
                accession=text.accession,
                status="failed",
                translate_model=self.translate_model,
                brief_model=self.brief_model,
                error_message=str(exc),
                model_status=model_status,
            )
        return GeoStudyTextSummary(
            accession=text.accession,
            status="completed",
            title_zh=translated.get("title_zh", ""),
            summary_zh=translated.get("summary_zh", ""),
            overall_design_zh=translated.get("overall_design_zh", ""),
            brief_zh=brief,
            translate_model=self.translate_model,
            brief_model=self.brief_model,
            model_status=model_status,
            quality_warnings=tuple(dict.fromkeys(warnings)),
        )

    def _translate_fields(self, text: GeoStudyTextInput) -> dict[str, str]:
        prompt = (
            "你是医学英语到中文翻译助手。只做保守翻译，不做总结，不扩写，不编造。"
            "保留基因名、疾病缩写、技术名。病理学术语谨慎翻译，不确定时保留英文并加括号；"
            "例如 oncocytic 优先译为嗜酸细胞性。"
            "请完整翻译非空输入字段，不得只翻译标题或省略 overall design。"
            "请严格输出 JSON，对象只包含 title_zh、summary_zh、overall_design_zh 三个字段。\n\n"
            f"title_en:\n{text.title_en or ''}\n\n"
            f"summary_en:\n{text.summary_en or ''}\n\n"
            f"overall_design_en:\n{text.overall_design_en or ''}\n"
        )
        raw = self._generate(self.translate_model, prompt)
        payload = _parse_json_object(raw, required_keys=("title_zh", "summary_zh", "overall_design_zh"))
        return {
            "title_zh": str(payload.get("title_zh") or "").strip(),
            "summary_zh": str(payload.get("summary_zh") or "").strip(),
            "overall_design_zh": str(payload.get("overall_design_zh") or "").strip(),
        }

    def _build_brief(self, text: GeoStudyTextInput, translated: dict[str, str]) -> tuple[str, tuple[str, ...]]:
        prompt = (
            "你是医学研究设计提炼助手。请只根据给定标题、摘要和 overall design，"
            "输出一句中文总结。必须写清楚疾病或肿瘤类型，必须写清楚比较组；"
            "如果是多组比较，列出组别；如果原文没有比较组，明确写“比较组未说明”。"
            "必须保留关键数据类型，例如 microarray、RNA-seq、expression profiling 或 single-cell。"
            "不要泛化，不要编造，不要把良性腺瘤写成正常组织，不要把甲状腺癌泛化成其他癌种。"
            "请严格输出 JSON，只包含 brief_zh、covered_terms、missing_or_uncertain 三个字段。"
            "brief_zh 只能是一行中文句子，不要项目符号，不要前缀。\n\n"
            f"title_en:\n{text.title_en or ''}\n\n"
            f"summary_en:\n{text.summary_en or ''}\n\n"
            f"overall_design_en:\n{text.overall_design_en or ''}\n\n"
            f"title_zh:\n{translated.get('title_zh', '')}\n\n"
            f"summary_zh:\n{translated.get('summary_zh', '')}\n\n"
            f"overall_design_zh:\n{translated.get('overall_design_zh', '')}\n"
        )
        raw = self._generate(self.brief_model, prompt)
        try:
            payload = _parse_json_object(raw, required_keys=("brief_zh", "covered_terms", "missing_or_uncertain"))
        except Exception:
            brief = _clean_one_line_brief(raw)
            if brief:
                return brief, ("医学模型未返回结构化 JSON，已清理文本输出。",)
            return _fallback_brief(text, translated), ("医学模型输出不可解析，已使用翻译字段生成保守简介。",)
        brief = _clean_one_line_brief(str(payload.get("brief_zh") or ""))
        warnings = tuple(str(item).strip() for item in payload.get("missing_or_uncertain", []) if str(item).strip()) if isinstance(payload.get("missing_or_uncertain"), list) else ()
        if not brief:
            return _fallback_brief(text, translated), (*warnings, "医学模型 brief_zh 为空，已使用翻译字段生成保守简介。")
        return brief, warnings

    def _generate(self, model: str, prompt: str) -> str:
        if self._generator is not None:
            return self._generator(model, prompt).strip()
        body = json.dumps(
            {
                "model": model,
                "prompt": prompt,
                "stream": False,
                "keep_alive": 0,
                "options": {"temperature": 0.1},
            }
        ).encode("utf-8")
        request = Request(
            f"{self.base_url}/api/generate",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:  # nosec B310 - user-configured local model endpoint.
                payload = json.loads(response.read().decode("utf-8"))
        except Exception as exc:
            raise RuntimeError(f"本地模型请求失败：{exc}") from exc
        generated = str(payload.get("response") or "").strip()
        if not generated:
            raise RuntimeError(f"本地模型 {model} 返回空内容。")
        return generated


def _parse_json_object(raw_text: str, *, required_keys: tuple[str, ...] = ()) -> dict[str, object]:
    cleaned = raw_text.strip()
    try:
        payload = json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, flags=re.S)
        if match is None:
            raise RuntimeError("翻译模型未返回 JSON。")
        payload = json.loads(match.group(0))
    if not isinstance(payload, dict):
        raise RuntimeError("翻译模型 JSON 不是对象。")
    for key in required_keys:
        payload.setdefault(key, [] if key in {"covered_terms", "missing_or_uncertain"} else "")
    return payload


def _model_name_available(model: str, names: set[str]) -> bool:
    expected = str(model).strip()
    if not expected:
        return False
    if expected in names:
        return True
    if ":" not in expected and f"{expected}:latest" in names:
        return True
    return any(name.split(":", 1)[0] == expected for name in names if ":" not in expected)


def _model_status_error(status: dict[str, str]) -> str:
    missing: list[str] = []
    if status.get("translate_model_status") != "available":
        missing.append(f"翻译模型 {status.get('translate_model') or ''}".strip())
    if status.get("brief_model_status") != "available":
        missing.append(f"医学提炼模型 {status.get('brief_model') or ''}".strip())
    detail = "、".join(missing) if missing else "本地模型"
    return f"{detail} 暂不可用，已保留英文摘要。"


def _translation_quality_warnings(text: GeoStudyTextInput, translated: dict[str, str]) -> tuple[str, ...]:
    warnings: list[str] = []
    for source_key, target_key, label in (
        ("title_en", "title_zh", "标题"),
        ("summary_en", "summary_zh", "摘要"),
        ("overall_design_en", "overall_design_zh", "overall design"),
    ):
        if str(getattr(text, source_key) or "").strip() and not str(translated.get(target_key) or "").strip():
            warnings.append(f"{label} 原文非空，但翻译为空。")
    return tuple(warnings)


def _brief_quality_warnings(text: GeoStudyTextInput, translated: dict[str, str], brief: str) -> tuple[str, ...]:
    source_text = " ".join([text.title_en, text.summary_en, text.overall_design_en, *translated.values()]).lower()
    warnings: list[str] = []
    if _has_comparison_cue(source_text) and not any(token in brief for token in ("比较", "对照", "正常", "肿瘤", "腺瘤", "病例", "样本", "组")):
        warnings.append("一句话简介可能未覆盖比较组。")
    if _has_data_type_cue(source_text) and not any(token in brief.lower() for token in ("表达", "测序", "芯片", "microarray", "rna-seq", "单细胞", "expression")):
        warnings.append("一句话简介可能未覆盖数据类型。")
    if not brief:
        warnings.append("一句话简介为空。")
    return tuple(warnings)


def _has_comparison_cue(text: str) -> bool:
    return any(token in text for token in (" versus ", " vs ", "compare", "comparison", "control", "normal", "tumor", "benign", "对照", "正常", "肿瘤", "腺瘤"))


def _has_data_type_cue(text: str) -> bool:
    return any(token in text for token in ("expression", "microarray", "rna-seq", "sequencing", "single-cell", "表达", "测序", "芯片", "单细胞"))


def _clean_one_line_brief(value: str) -> str:
    text = str(value or "").strip()
    text = re.sub(r"^```(?:json)?|```$", "", text, flags=re.I).strip()
    text = re.sub(r"^[\-•*\d.、\s]+", "", text).strip()
    text = re.sub(r"^(中文)?(一句话)?(简介|总结|概述)[:：]\s*", "", text).strip()
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _fallback_brief(text: GeoStudyTextInput, translated: dict[str, str]) -> str:
    for key in ("overall_design_zh", "summary_zh", "title_zh"):
        brief = _clean_one_line_brief(translated.get(key, ""))
        if brief:
            return brief
    english = _clean_one_line_brief(text.overall_design_en or text.summary_en or text.title_en)
    return english or "该 GEO 数据集的中文简介暂未生成，请查看英文标题和摘要。"
