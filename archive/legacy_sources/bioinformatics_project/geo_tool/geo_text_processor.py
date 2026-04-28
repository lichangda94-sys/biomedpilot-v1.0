"""Ollama-backed translation and one-line GEO study summarization."""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from typing import Optional

import requests

from geo_info_fetcher import GeoSeriesInfo


LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class ProcessedGeoText:
    title_zh: str
    summary_zh: str
    overall_design_zh: str
    brief_zh: str


class OllamaAPIError(Exception):
    """Raised when Ollama API requests fail."""


class GeoTextProcessor:
    """Serial text processing with two Ollama models and keep_alive=0."""

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:11434",
        translate_model: str = "translategemma",
        brief_model: str = "medgemma:4b",
        timeout: int = 180,
        session: Optional[requests.Session] = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.translate_model = translate_model
        self.brief_model = brief_model
        self.timeout = timeout
        self.session = session or requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})

    def is_available(self) -> bool:
        try:
            response = self.session.get(f"{self.base_url}/api/tags", timeout=10)
            response.raise_for_status()
            return True
        except Exception:
            return False

    def enrich_series_info(self, info: GeoSeriesInfo) -> GeoSeriesInfo:
        translated = self.translate_fields(
            title_en=info.title_en,
            summary_en=info.summary_en,
            overall_design_en=info.overall_design_en,
        )
        brief = self.build_brief(
            title_en=info.title_en,
            summary_en=info.summary_en,
            overall_design_en=info.overall_design_en,
            title_zh=translated.title_zh,
            summary_zh=translated.summary_zh,
            overall_design_zh=translated.overall_design_zh,
        )
        info.title_zh = translated.title_zh
        info.summary_zh = translated.summary_zh
        info.overall_design_zh = translated.overall_design_zh
        info.brief_zh = brief
        return info

    def translate_fields(
        self,
        title_en: str,
        summary_en: str,
        overall_design_en: str,
    ) -> ProcessedGeoText:
        prompt = (
            "你是医学英语到中文翻译助手。"
            "只做保守翻译，不做总结，不扩写，不编造。"
            "保留基因名、疾病缩写、技术名。"
            "病理学术语谨慎翻译，不确定时保留英文并加括号。"
            "例如 oncocytic 优先译为嗜酸细胞性。"
            "请严格输出 JSON，对象包含 title_zh、summary_zh、overall_design_zh 三个字段。\n\n"
            f"title_en:\n{title_en or ''}\n\n"
            f"summary_en:\n{summary_en or ''}\n\n"
            f"overall_design_en:\n{overall_design_en or ''}\n"
        )
        raw = self._generate(model=self.translate_model, prompt=prompt)
        data = self._parse_json_object(raw, required_keys=["title_zh", "summary_zh", "overall_design_zh"])
        return ProcessedGeoText(
            title_zh=data.get("title_zh", "").strip(),
            summary_zh=data.get("summary_zh", "").strip(),
            overall_design_zh=data.get("overall_design_zh", "").strip(),
            brief_zh="",
        )

    def build_brief(
        self,
        title_en: str,
        summary_en: str,
        overall_design_en: str,
        title_zh: str,
        summary_zh: str,
        overall_design_zh: str,
    ) -> str:
        prompt = (
            "你是医学研究设计提炼助手。"
            "请只根据给定的标题、摘要和 overall design 信息，输出一句中文总结。"
            "必须写清楚疾病或肿瘤类型，必须写清楚比较组。"
            "如果是多组比较，列出组别；不要泛化，不要解释，不要编造。"
            "输出只允许一行中文句子，不要项目符号，不要前缀。\n\n"
            f"title_en:\n{title_en or ''}\n\n"
            f"summary_en:\n{summary_en or ''}\n\n"
            f"overall_design_en:\n{overall_design_en or ''}\n\n"
            f"title_zh:\n{title_zh or ''}\n\n"
            f"summary_zh:\n{summary_zh or ''}\n\n"
            f"overall_design_zh:\n{overall_design_zh or ''}\n"
        )
        return self._generate(model=self.brief_model, prompt=prompt).strip()

    def _generate(self, model: str, prompt: str) -> str:
        try:
            response = self.session.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "keep_alive": 0,
                    "options": {"temperature": 0.1},
                },
                timeout=self.timeout,
            )
            response.raise_for_status()
            payload = response.json()
        except Exception as exc:
            raise OllamaAPIError(f"Ollama request failed for model {model}: {exc}") from exc

        text = (payload.get("response") or "").strip()
        if not text:
            raise OllamaAPIError(f"Ollama returned empty text for model {model}")
        return text

    @staticmethod
    def _parse_json_object(raw_text: str, required_keys: list[str]) -> dict:
        cleaned = raw_text.strip()
        try:
            payload = json.loads(cleaned)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", cleaned, flags=re.S)
            if not match:
                raise OllamaAPIError("Translation model did not return valid JSON")
            payload = json.loads(match.group(0))

        if not isinstance(payload, dict):
            raise OllamaAPIError("Translation model JSON response is not an object")

        for key in required_keys:
            payload.setdefault(key, "")
        return payload
