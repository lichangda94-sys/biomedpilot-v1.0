# Lexicon Coverage Audit

## Category Coverage

### disease_or_project_terms

- tcga_gdc: full=102, mappings=181, terms=Project ID, Project Name, Disease Type, TCGA-ACC, Adrenocortical Carcinoma, mapping targets=Acute Myeloid Leukemia, TCGA-LAML, Adrenal Gland, Adrenocortical Carcinoma, TCGA-ACC
- gtex: full=0, mappings=51, terms=none, mapping targets=Adrenal Gland, Bladder, Brain, Breast, Cervix Uteri
- geo: full=0, mappings=110, terms=none, mapping targets=acute myeloid leukemia, adrenocortical carcinoma, bladder cancer, bladder urothelial carcinoma, brain lower grade glioma
- shared: full=0, mappings=0, terms=none, mapping targets=none
- concept layer: 61 concepts; examples: disease.acute_myeloid_leukemia, disease.adrenocortical_carcinoma, disease.bladder_cancer, disease.bladder_urothelial_carcinoma, disease.brain_lower_grade_glioma
- bias note: not_obvious

### sample_terms

- tcga_gdc: full=25, mappings=11, terms=Sample Type, Tissue Type, Tumor Descriptor, Primary Tumor, Recurrent Tumor, mapping targets=Metastatic, Normal, normal tissue, Primary Tumor, primary tumor
- gtex: full=10, mappings=0, terms=Sex, Age, Male, Female, 20-29, mapping targets=none
- geo: full=0, mappings=11, terms=none, mapping targets=metastatic, normal, normal tissue, primary tumor, tumor
- shared: full=0, mappings=0, terms=none, mapping targets=none
- concept layer: 7 concepts; examples: sample_type.metastatic, sample_type.normal, sample_type.primary_tumor, sample_type.recurrent_tumor, sample_type.solid_tissue_normal
- bias note: not_obvious

### data_terms

- tcga_gdc: full=38, mappings=8, terms=Data Category, Data Type, Experimental Strategy, Workflow Type, Access, mapping targets=Biospecimen Supplement, biospecimen, Clinical Supplement, clinical, copy number
- gtex: full=8, mappings=7, terms=Release, Read Count, TPM, Sample Attributes, Subject Phenotypes, mapping targets=eQTL, gene expression, read count, sample attributes, sQTL
- geo: full=0, mappings=21, terms=none, mapping targets=biospecimen, biospecimen metadata, clinical, clinical metadata, cnv
- shared: full=0, mappings=0, terms=none, mapping targets=none
- concept layer: 11 concepts; examples: analysis_resource.biospecimen, analysis_resource.clinical, analysis_resource.copy_number, analysis_resource.eqtl, analysis_resource.gene_expression
- bias note: not_obvious

### access_terms

- tcga_gdc: full=2, mappings=3, terms=State, Released, mapping targets=controlled, open, released
- gtex: full=3, mappings=3, terms=Open Access, Protected, Release, mapping targets=open access, protected, release
- geo: full=0, mappings=6, terms=none, mapping targets=controlled, open, open access, protected, release
- shared: full=2, mappings=0, terms=Open, Controlled, mapping targets=none
- concept layer: 4 concepts; examples: access.controlled, access.open, access.protected, access.release
- bias note: not_obvious

### tissue_terms

- tcga_gdc: full=27, mappings=33, terms=Primary Site, Adrenal Gland, Bladder, Breast, Cervix Uteri, mapping targets=Adrenal Gland, Bile Duct, Bladder, Hematopoietic and Reticuloendothelial Systems, Brain
- gtex: full=67, mappings=35, terms=Tissue, Subregion, Adipose Tissue, Subcutaneous, Visceral (Omentum), mapping targets=Adipose Tissue, Adrenal Gland, Bladder, Blood, Blood Vessel
- geo: full=0, mappings=53, terms=none, mapping targets=adipose tissue, adrenal gland, bile duct, bladder, blood
- shared: full=0, mappings=0, terms=none, mapping targets=none
- concept layer: 44 concepts; examples: tissue.adipose_tissue, tissue.adrenal_gland, tissue.bile_duct, tissue.bladder, tissue.blood
- bias note: not_obvious

### display_terms

- tcga_gdc: full=0, mappings=0, terms=none, mapping targets=none
- gtex: full=0, mappings=0, terms=none, mapping targets=none
- geo: full=0, mappings=0, terms=none, mapping targets=none
- shared: full=7, mappings=0, terms=Clinical, Biospecimen, Mutation, Copy Number, Normal Tissue, mapping targets=none
- concept layer: 0 concepts; examples: none
- bias note: not_obvious

### source_entities

- tcga_gdc: full=1, mappings=4, terms=Annotations, mapping targets=Annotations, Cases, Files, Projects
- gtex: full=7, mappings=1, terms=Tissue, Dataset, Sample Attributes, Subject Phenotypes, Gene Expression, mapping targets=Dataset
- geo: full=0, mappings=0, terms=none, mapping targets=none
- shared: full=3, mappings=0, terms=Projects, Cases, Files, mapping targets=none
- concept layer: 5 concepts; examples: database_entity.annotations, database_entity.cases, database_entity.dataset, database_entity.files, database_entity.projects
- bias note: not_obvious

## Disease Coverage

### TCGA project IDs

TCGA-ACC, TCGA-BLCA, TCGA-BRCA, TCGA-CESC, TCGA-CHOL, TCGA-COAD, TCGA-DLBC, TCGA-ESCA, TCGA-GBM, TCGA-HNSC, TCGA-KICH, TCGA-KIRC, TCGA-KIRP, TCGA-LAML, TCGA-LGG, TCGA-LIHC, TCGA-LUAD, TCGA-LUSC, TCGA-MESO, TCGA-OV, TCGA-PAAD, TCGA-PCPG, TCGA-PRAD, TCGA-READ, TCGA-SARC, TCGA-SKCM, TCGA-STAD, TCGA-TGCT, TCGA-THCA, TCGA-THYM, TCGA-UCEC, TCGA-UCS, TCGA-UVM

### High-frequency cancer status

- thyroid cancer: fully_covered (missing: none)
- breast cancer: fully_covered (missing: none)
- lung adenocarcinoma: fully_covered (missing: none)
- lung squamous cell carcinoma: fully_covered (missing: none)
- hepatocellular carcinoma: fully_covered (missing: none)
- colorectal cancer: fully_covered (missing: none)
- gastric cancer: fully_covered (missing: none)
- prostate cancer: fully_covered (missing: none)
- pancreatic cancer: fully_covered (missing: none)
- ovarian cancer: fully_covered (missing: none)
- glioblastoma: fully_covered (missing: none)
- melanoma: fully_covered (missing: none)
- leukemia: fully_covered (missing: none)
- lymphoma: fully_covered (missing: none)
- cervical cancer: fully_covered (missing: none)
- endometrial cancer: fully_covered (missing: none)
- bladder cancer: fully_covered (missing: none)
- kidney clear cell carcinoma: fully_covered (missing: none)
- kidney papillary carcinoma: fully_covered (missing: none)
- head and neck squamous cell carcinoma: fully_covered (missing: none)
- esophageal carcinoma: fully_covered (missing: none)
- cholangiocarcinoma: partially_covered (missing: gtex_tissue_reference)
- mesothelioma: fully_covered (missing: none)
- thymoma: partially_covered (missing: gtex_tissue_reference)
- testicular germ cell tumors: fully_covered (missing: none)
- sarcoma: partially_covered (missing: gtex_tissue_reference)
- lower grade glioma: fully_covered (missing: none)
- adrenocortical carcinoma: fully_covered (missing: none)
- pheochromocytoma and paraganglioma: fully_covered (missing: none)

## Tissue Coverage

### GTEx tissues

Adipose Tissue, Adrenal Gland, Bladder, Blood, Blood Vessel, Brain, Breast, Cervix Uteri, Colon, Esophagus, Fallopian Tube, Heart, Kidney, Liver, Lung, Minor Salivary Gland, Muscle, Nerve, Ovary, Pancreas, Pituitary, Prostate, Skin, Small Intestine, Spleen, Stomach, Testis, Thyroid, Uterus, Vagina

### High-frequency tissue status

- thyroid: fully_covered (missing: none)
- breast: fully_covered (missing: none)
- lung: fully_covered (missing: none)
- liver: fully_covered (missing: none)
- brain: fully_covered (missing: none)
- colon / colorectal: fully_covered (missing: none)
- stomach: fully_covered (missing: none)
- prostate: fully_covered (missing: none)
- pancreas: fully_covered (missing: none)
- ovary: fully_covered (missing: none)
- skin: fully_covered (missing: none)
- blood / bone marrow: fully_covered (missing: none)
- lymph node / lymphoid tissue: fully_covered (missing: none)
- kidney: fully_covered (missing: none)
- bladder: fully_covered (missing: none)
- cervix: fully_covered (missing: none)
- uterus: fully_covered (missing: none)
- esophagus: fully_covered (missing: none)
- bile duct: partially_covered (missing: gtex_mapping)
- small intestine: partially_covered (missing: tcga_primary_site_mapping)
- salivary gland: partially_covered (missing: tcga_primary_site_mapping)
- pituitary: partially_covered (missing: tcga_primary_site_mapping)
- adrenal gland: fully_covered (missing: none)
- testis: fully_covered (missing: none)
- fallopian tube: partially_covered (missing: tcga_primary_site_mapping)
- vagina: partially_covered (missing: tcga_primary_site_mapping)
- nerve: partially_covered (missing: tcga_primary_site_mapping)
- blood vessel: partially_covered (missing: tcga_primary_site_mapping)
- heart: partially_covered (missing: tcga_primary_site_mapping)
- muscle: partially_covered (missing: tcga_primary_site_mapping)

## Bias Flags


## Recommended Next Expansions

- Expand Chinese disease entry points beyond thyroid-first coverage, starting with: cholangiocarcinoma, thymoma, sarcoma.
- Add shared tissue concepts and Chinese bridges for: bile duct, small intestine, salivary gland, pituitary, fallopian tube.
- Add umbrella concepts that are currently missing but important for navigation, such as colorectal cancer, gastric cancer, prostate cancer, pancreatic cancer, ovarian cancer, melanoma, leukemia, lymphoma, and lymphoid tissue.
- Keep GEO in the concept-to-query-expansion layer only, but broaden GEO preview terms once non-thyroid Chinese concepts are added.
