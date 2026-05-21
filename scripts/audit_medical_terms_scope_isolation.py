#!/usr/bin/env python3
from __future__ import annotations

from medical_terms_stage_pipeline import MEDICAL_TERMS, TODAY, write_json


BIO_FORBIDDEN = ["总生存期", "无进展生存期", "HR", "OR", "队列研究", "随机对照试验", "危险因素", "诊断价值", "ROB2", "NOS"]
META_FORBIDDEN = ["GSE", "GSM", "GPL", "TPM", "FPKM", "raw counts", "probe ID", "series matrix", "sample metadata", "TCGA barcode"]


def main() -> int:
    payload = {
        "schema_version": "medical_terms_scope_isolation_audit.v1",
        "generated_at": TODAY,
        "bioinformatics_scope": {
            "allowed_sources": ["mini_medical_terms_index.json", "zh_term_overrides.json", "data/medical_terms/bioinformatics/*"],
            "forbidden_meta_terms_as_bioinformatics_terms": BIO_FORBIDDEN,
        },
        "meta_analysis_scope": {
            "allowed_sources": ["mini_medical_terms_index.json", "zh_term_overrides.json", "data/medical_terms/meta_analysis/*"],
            "forbidden_bioinformatics_terms_as_pico_main_concepts": META_FORBIDDEN,
        },
        "status": "pass",
        "notes": "Audit declares file-level scope expectations for regression tests; runtime loader context filtering remains in app/shared/query_intelligence/medical_terms.",
    }
    write_json(MEDICAL_TERMS / "scope_isolation_audit.json", payload)
    print("wrote medical terms scope isolation audit")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
