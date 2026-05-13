# Stage V8 Medical Vocabulary Local Model Unknown-Term Candidates

## Goal

Stage V8 allows the local model to help with unknown Chinese medical terms
without replacing the shared vocabulary or deciding final retrieval behavior.

## Runtime Policy

- Existing vocabulary matches remain authoritative.
- When `lookup_medical_terms()` has no match and the caller explicitly enables
  local model use, model output is treated as candidate suggestions only.
- Candidate English terms must pass term lookup and disease guard validation.
- Validated candidates are returned as `candidate_terms`.
- Candidate terms are not written into final PubMed, GEO, TCGA, or GTEx query
  fields.

## Boundaries

- The model cannot override locked disease-domain terms.
- The model cannot decide TCGA or GTEx mappings.
- The model cannot bypass forbidden leakage checks.
- The model cannot write to global vocabulary JSON or sqlite.
- No Bioinformatics or Meta Analysis business code was modified.

## Validation

The shared query intelligence tests cover:

- Unknown-term candidate generation.
- Invalid model candidates being excluded.
- Candidate terms not entering final query fields.
- Meta context continuing to filter Bio dataset fields.
