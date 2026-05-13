# LabTools Recipe Draft Store Schema

日期：2026-05-13

## Schema

- Schema version：`labtools_recipe_draft_store.v1`
- Export type：`labtools_user_recipe_draft_store`
- Channel：`Developer Preview / testing`
- Review status：`manual_review_required`

This schema documents the local JSON file produced by LabTools when the user explicitly chooses to save confirmed user recipe drafts. It is an internal preview schema for local draft persistence, not a formal SOP format, not a database migration contract, and not a clinical or safety operation artifact.

## Top-Level Fields

- `schema_version`：must be `labtools_recipe_draft_store.v1`.
- `export_type`：must be `labtools_user_recipe_draft_store`.
- `created_at`：UTC ISO-like timestamp generated at save time.
- `software_channel`：currently `Developer Preview / testing`.
- `review_status`：currently `manual_review_required`.
- `recipe_count`：number of recipes in `recipes`.
- `recipes`：list of user-confirmed recipe draft records.
- `safety_reviews`：one safety review entry per recipe.
- `safety_note`：manual-review and SOP/SDS review notice.
- `persistence_note`：states that writing happens only after user-selected local path, without autosave, network, or AI.

## Recipe Fields

Each item in `recipes` is the JSON-compatible representation of `Recipe`:

- `recipe_id`
- `name`
- `category`
- `description`
- `stock_concentration`
- `default_volume`
- `default_volume_unit`
- `components`
- `preparation_notes`
- `safety_notes`
- `source_label`
- `version`
- `is_user_defined`
- `review_notice`
- `source_url`
- `source_title`
- `accessed_at`
- `user_confirmed`
- `edited_by_user`

Each item in `components` contains:

- `name`
- `amount`
- `unit`
- `role`
- `optional`
- `notes`

## Import And Conflict Rules

- Loading requires `schema_version == labtools_recipe_draft_store.v1`.
- Loading rejects malformed JSON, missing `recipes`, invalid recipe structures, and blocked high-risk scope terms.
- Imported recipes are merged into the current in-memory `UserRecipeStore`.
- If an imported `recipe_id` already exists, LabTools clones the imported recipe to a new `user_recipe_imported_<token>` id.
- Conflicts are surfaced in the UI as `recipe_id 冲突数` and a warning that existing user recipes were not overwritten.
- Recipe `version` is preserved on import and displayed in the user recipe summary.

## Safety Boundaries

- The JSON file is a local recipe draft store only.
- It does not replace laboratory SOP, SDS, reagent instructions, or institutional safety review.
- It does not support dangerous chemical synthesis, toxins, animal/human experiment protocols, viral packaging, or other high-risk operating procedures.
- It does not upload, sync, fetch, or call AI.
- It does not write Bioinformatics, Meta Analysis, or shared project manifests.
