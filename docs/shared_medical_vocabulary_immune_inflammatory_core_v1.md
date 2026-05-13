# Shared Medical Vocabulary Immune & Inflammatory Core v1

## Scope

Immune & Inflammatory Core v1 adds curated, high-value immune disease, inflammatory disease, immune cell, biomarker, process, and phenotype terms to the shared medical vocabulary. The goal is practical query understanding for Bioinformatics Chinese topic retrieval, GEO/GTEx/SRA query assistance, Meta Analysis research question parsing, and PubMed query draft generation.

This stage is not a full ontology import. It intentionally avoids wholesale UBERON, MeSH, MONDO, HPO, or specialist rheumatology ontology ingestion so runtime matching stays auditable and low-risk.

## Coverage

- Autoimmune diseases: SLE, rheumatoid arthritis, Sjogren syndrome, systemic sclerosis, dermatomyositis, polymyositis, mixed connective tissue disease, antiphospholipid syndrome.
- Rheumatic and vasculitis diseases: osteoarthritis, ankylosing spondylitis, psoriatic arthritis, juvenile idiopathic arthritis, gout, vasculitis, giant cell arteritis, Takayasu arteritis, ANCA-associated vasculitis.
- Inflammatory bowel disease: IBD, Crohn disease, ulcerative colitis, microscopic colitis.
- Allergy and airway inflammation: asthma, allergic rhinitis, atopic dermatitis, eczema, food allergy, anaphylaxis, chronic rhinosinusitis, COPD.
- Skin immune disease: psoriasis, vitiligo, alopecia areata, hidradenitis suppurativa, pemphigus, bullous pemphigoid.
- Neuroimmune disease: multiple sclerosis, NMOSD, myasthenia gravis, Guillain-Barre syndrome, autoimmune encephalitis.
- Immune cells: T cell, B cell, macrophage, monocyte, neutrophil, dendritic cell, NK cell, Treg, Th1, Th2, Th17, plasma cell.
- Biomarkers and autoantibodies: CRP, IL-6, IL-1 beta, TNF-alpha, IFN-gamma, IL-10, IL-17, IgE, ANA, RF, anti-CCP, ANCA.

## Category Boundaries

The runtime vocabulary keeps these concept types separate:

- `disease`: immune and inflammatory diseases.
- `immune_cell`: cell populations used in omics and immune profiling queries.
- `biomarker`: cytokines, antibodies, and inflammatory markers.
- `process`: inflammation and immune response.
- `phenotype`: cytokine storm and related inflammatory states.

Immune cells and biomarkers are not treated as disease concepts. This prevents queries such as `T cell RNA-seq` or `IL-6 expression` from being interpreted as disease recognition.

## Cross-Core Boundaries

Some concepts already existed in other core packages:

- Hashimoto thyroiditis and Graves disease remain endocrine/metabolic disease concepts.
- C-reactive protein remains the cardiovascular biomarker concept.
- Inflammation remains a cross-referenced process/phenotype concept.

Immune & Inflammatory Core v1 references these terms instead of creating duplicate conflicting concept IDs.

## Context Boundaries

Bioinformatics context may use immune terms for:

- `disease_terms_en`
- `mesh_terms`
- `tissue_terms`
- `gtex_tissue_candidates`
- `immune_cell_terms`
- `biomarker_terms`
- GEO/GTEx/SRA query assistance

Bioinformatics context should not emit PICO, effect measure, publication type, or PubMed-only results as primary outputs.

Meta Analysis context may use immune terms for disease, exposure, outcome, biomarker, and PubMed/MeSH query support. It should not output TCGA/GEO/GTEx candidates as primary results.

## Short Token Handling

High-risk tokens such as `RA`, `IBD`, `SLE`, `IL-6`, `TNF`, `IFN`, `IgE`, `ANA`, `RF`, and `ANCA` are represented as exact abbreviations with ambiguity notes. They must not be matched through ordinary substring logic.

## Negative Expansion Rules

The vocabulary encodes avoid-expansion boundaries for common leakage risks:

- IBD does not automatically equal Crohn disease or ulcerative colitis.
- Crohn disease does not automatically equal ulcerative colitis.
- Asthma does not automatically equal COPD.
- Psoriasis does not automatically equal psoriatic arthritis.
- SLE does not automatically equal lupus nephritis.
- ANCA biomarker does not automatically equal ANCA-associated vasculitis.

## Remaining Gaps

This release does not attempt exhaustive immunology coverage. It leaves detailed complement disorders, primary immunodeficiency, transplantation immunology, autoinflammatory syndromes, rare vasculitis subtypes, detailed cytokine families, HLA alleles, and immunotherapy adverse event ontologies for later stages.

## Next Stage

Recommended next steps:

- External ontology subset import v1 for carefully selected MeSH/MONDO/EFO immune and inflammation terms.
- Cardio-immune-metabolic cross-domain review for shared biomarkers and risk factors.
- Query intent tests for immune cell deconvolution, immune infiltration, and cytokine expression workflows.
