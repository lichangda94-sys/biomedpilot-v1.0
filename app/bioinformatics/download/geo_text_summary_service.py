from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
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
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.translate_model = translate_model
        self.brief_model = brief_model
        self.timeout = timeout
        self._generator = generator
        self._availability_checker = availability_checker

    def is_available(self) -> bool:
        if self._availability_checker is not None:
            return bool(self._availability_checker())
        request = Request(f"{self.base_url}/api/tags", method="GET")
        try:
            with urlopen(request, timeout=min(self.timeout, 5)) as response:  # nosec B310 - user-configured local model endpoint.
                return 200 <= int(response.status) < 300
        except (OSError, HTTPError, URLError):
            return False

    def summarize(self, text: GeoStudyTextInput) -> GeoStudyTextSummary:
        if not self.is_available():
            return GeoStudyTextSummary(
                accession=text.accession,
                status="local_model_unavailable",
                translate_model=self.translate_model,
                brief_model=self.brief_model,
                error_message="本地翻译/医学模型暂不可用，已保留英文摘要。",
            )
        try:
            translated = self._translate_fields(text)
            brief = self._build_brief(text, translated)
        except Exception as exc:
            return GeoStudyTextSummary(
                accession=text.accession,
                status="failed",
                translate_model=self.translate_model,
                brief_model=self.brief_model,
                error_message=str(exc),
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
        )

    def _translate_fields(self, text: GeoStudyTextInput) -> dict[str, str]:
        prompt = (
            "你是医学英语到中文翻译助手。只做保守翻译，不做总结，不扩写，不编造。"
            "保留基因名、疾病缩写、技术名。请严格输出 JSON，对象包含 "
            "title_zh、summary_zh、overall_design_zh 三个字段。\n\n"
            f"title_en:\n{text.title_en or ''}\n\n"
            f"summary_en:\n{text.summary_en or ''}\n\n"
            f"overall_design_en:\n{text.overall_design_en or ''}\n"
        )
        raw = self._generate(self.translate_model, prompt)
        payload = _parse_json_object(raw)
        return {
            "title_zh": str(payload.get("title_zh") or "").strip(),
            "summary_zh": str(payload.get("summary_zh") or "").strip(),
            "overall_design_zh": str(payload.get("overall_design_zh") or "").strip(),
        }

    def _build_brief(self, text: GeoStudyTextInput, translated: dict[str, str]) -> str:
        prompt = (
            "你是医学研究设计提炼助手。请只根据给定标题、摘要和 overall design，"
            "输出一句中文总结。必须写清楚疾病或肿瘤类型和比较组；不要泛化，不要编造。"
            "输出只允许一行中文句子，不要项目符号，不要前缀。\n\n"
            f"title_en:\n{text.title_en or ''}\n\n"
            f"summary_en:\n{text.summary_en or ''}\n\n"
            f"overall_design_en:\n{text.overall_design_en or ''}\n\n"
            f"title_zh:\n{translated.get('title_zh', '')}\n\n"
            f"summary_zh:\n{translated.get('summary_zh', '')}\n\n"
            f"overall_design_zh:\n{translated.get('overall_design_zh', '')}\n"
        )
        return self._generate(self.brief_model, prompt).strip()

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


def _parse_json_object(raw_text: str) -> dict[str, object]:
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
    return payload
