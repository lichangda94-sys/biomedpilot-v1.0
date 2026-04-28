from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from bias.models import BiasAssessmentRow, BiasAssessmentTable, BiasDomainTemplate, BiasJudgement, BiasRecord
from bias.store import BiasStore
from extraction.store import ExtractionStore
from literature.store import LiteratureStore


NOS_LIKE_MINIMAL_TEMPLATE = [
    BiasDomainTemplate(
        tool_name="nos_cohort_minimal",
        domain_name="selection",
        description="Representativeness and participant selection quality.",
    ),
    BiasDomainTemplate(
        tool_name="nos_cohort_minimal",
        domain_name="comparability",
        description="Adjustment or comparability across groups.",
    ),
    BiasDomainTemplate(
        tool_name="nos_cohort_minimal",
        domain_name="outcome_assessment",
        description="Outcome ascertainment and follow-up adequacy.",
    ),
]


class BiasAssessmentService:
    def __init__(
        self,
        literature_store: LiteratureStore,
        extraction_store: ExtractionStore,
        bias_store: BiasStore,
    ) -> None:
        self._literature_store = literature_store
        self._extraction_store = extraction_store
        self._bias_store = bias_store

    @classmethod
    def from_root_dir(cls, root_dir: Path) -> "BiasAssessmentService":
        return cls(LiteratureStore(root_dir), ExtractionStore(root_dir), BiasStore(root_dir))

    def initialize_default_domains(
        self,
        *,
        tool_name: str = "nos_cohort_minimal",
    ) -> list[BiasDomainTemplate]:
        existing = self._bias_store.list_templates(tool_name)
        if existing:
            return existing
        if tool_name != "nos_cohort_minimal":
            raise ValueError(f"Unknown bias template tool: {tool_name}")
        return self._bias_store.replace_templates(tool_name, list(NOS_LIKE_MINIMAL_TEMPLATE))

    def submit_domain_judgement(
        self,
        screening_record_id: str,
        *,
        domain_name: str,
        judgement: BiasJudgement,
        tool_name: str = "nos_cohort_minimal",
        extraction_record_id: str | None = None,
        support_text: str = "",
        reviewer_id: str | None = None,
    ) -> BiasRecord:
        screening_record = self._literature_store.get_screening_record(screening_record_id)
        if screening_record is None:
            raise ValueError(f"Screening record does not exist: {screening_record_id}")
        template_names = {template.domain_name for template in self.initialize_default_domains(tool_name=tool_name)}
        if domain_name not in template_names:
            raise ValueError(f"Unknown bias domain for {tool_name}: {domain_name}")
        if extraction_record_id is not None and self._extraction_store.get_extraction_record(extraction_record_id) is None:
            raise ValueError(f"Extraction record does not exist: {extraction_record_id}")

        existing = self._find_domain_record(screening_record_id, tool_name, domain_name)
        if existing is None:
            record = BiasRecord(
                bias_record_id=f"bias-{uuid4().hex[:12]}",
                project_id=screening_record.project_id,
                screening_record_id=screening_record_id,
                extraction_record_id=extraction_record_id,
                tool_name=tool_name,
                domain_name=domain_name,
                judgement=judgement,
                support_text=support_text,
                reviewer_id=reviewer_id,
            )
        else:
            record = existing
            record.judgement = judgement
            record.support_text = support_text
            record.reviewer_id = reviewer_id
            record.extraction_record_id = extraction_record_id
            record.touch()
        return self._bias_store.save_record(record)

    def list_study_assessments(
        self,
        screening_record_id: str,
    ) -> list[BiasRecord]:
        return self._bias_store.list_records(screening_record_id=screening_record_id)

    def summarize_overall_judgement(
        self,
        screening_record_id: str,
    ) -> BiasJudgement:
        records = self.list_study_assessments(screening_record_id)
        if not records:
            return BiasJudgement.UNCLEAR
        judgements = {record.judgement for record in records}
        if BiasJudgement.HIGH in judgements:
            return BiasJudgement.HIGH
        if BiasJudgement.UNCLEAR in judgements:
            return BiasJudgement.UNCLEAR
        return BiasJudgement.LOW

    def generate_bias_assessment_table(
        self,
        screening_record_id: str,
        *,
        tool_name: str = "nos_cohort_minimal",
    ) -> BiasAssessmentTable:
        records = [
            record
            for record in self.list_study_assessments(screening_record_id)
            if record.tool_name == tool_name
        ]
        if records:
            project_id = records[0].project_id
        else:
            screening_record = self._literature_store.get_screening_record(screening_record_id)
            if screening_record is None:
                raise ValueError(f"Screening record does not exist: {screening_record_id}")
            project_id = screening_record.project_id
        rows = [
            BiasAssessmentRow(
                screening_record_id=record.screening_record_id,
                extraction_record_id=record.extraction_record_id,
                domain_name=record.domain_name,
                judgement=record.judgement,
                support_text=record.support_text,
            )
            for record in records
        ]
        return BiasAssessmentTable(
            project_id=project_id,
            tool_name=tool_name,
            overall_judgement=self.summarize_overall_judgement(screening_record_id),
            rows=rows,
        )

    def _find_domain_record(
        self,
        screening_record_id: str,
        tool_name: str,
        domain_name: str,
    ) -> BiasRecord | None:
        for record in self._bias_store.list_records(screening_record_id=screening_record_id):
            if record.tool_name == tool_name and record.domain_name == domain_name:
                return record
        return None
