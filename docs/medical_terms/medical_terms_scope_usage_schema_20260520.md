# Medical Terms Scope Usage Schema

Date: 2026-05-20

## Scope

This is Phase S2 of the shared core cleanup plan. It defines a common annotation schema for later vocabulary migration and routing.

Schema file:

`data/medical_terms/schema/medical_terms_scope_usage_schema.json`

No runtime vocabulary entries were migrated in this phase.

## Required Sections

Every future migrated or annotated term should include:

- `scope`
- `usage`
- `requires_context`
- `migration`

## Scope Fields

`scope.shared_core_allowed`

Whether the term can remain active in shared core.

`scope.bioinformatics_allowed`

Whether the term can be loaded by Bioinformatics scoped vocabulary or routing.

`scope.meta_analysis_allowed`

Whether the term can be loaded by Meta Analysis scoped vocabulary or routing.

## Usage Fields

`usage.query_expansion_allowed`

Allowed values:

- `true`
- `false`
- `conditional`
- `filter_only`

Other usage fields:

- `usage.standalone_search_allowed`
- `usage.filter_only`
- `usage.pdf_extraction_target`
- `usage.analysis_plan_allowed`
- `usage.report_label_allowed`

## Context Fields

`requires_context.requires_population_or_disease`

Used for outcomes or effect concepts that require population/disease pairing.

`requires_context.requires_intervention_or_exposure`

Used for terms that should only expand when paired with intervention or exposure concepts.

`requires_context.requires_qualified_term`

Used for broad or ambiguous terms that should not stand alone.

## Migration Fields

Required fields:

- `migration.legacy_concept_id`
- `migration.new_concept_id`
- `migration.migration_status`
- `migration.compatibility_alias`
- `migration.active_in_shared`

Allowed `migration_status` values:

- `not_migrated`
- `candidate_for_migration`
- `mirrored_to_meta_scoped`
- `mirrored_to_bioinformatics_scoped`
- `deprecated_in_shared`
- `removed_from_shared`
- `manual_review_required`

## Example

```json
{
  "scope": {
    "shared_core_allowed": false,
    "bioinformatics_allowed": false,
    "meta_analysis_allowed": true
  },
  "usage": {
    "query_expansion_allowed": "conditional",
    "standalone_search_allowed": false,
    "filter_only": false,
    "pdf_extraction_target": true,
    "analysis_plan_allowed": false,
    "report_label_allowed": true
  },
  "requires_context": {
    "requires_population_or_disease": true,
    "requires_intervention_or_exposure": false,
    "requires_qualified_term": false
  },
  "migration": {
    "legacy_concept_id": "mini:overall_survival",
    "new_concept_id": "meta_outcome:overall_survival",
    "migration_status": "candidate_for_migration",
    "compatibility_alias": true,
    "active_in_shared": true
  }
}
```

## Next Step

Use this schema in Phase S3 mirror files and compatibility maps. Do not use it as justification to delete or rewrite shared core entries without a separate cleanup decision phase.
