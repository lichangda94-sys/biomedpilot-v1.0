# Project Management Restore Plan

Date: 2026-05-29

## Current Decision

The accepted packaged preview `9d4edf3` is a UI Shell / visual baseline, but it is not proof that Project Management is complete.

Project Management remains governed separately from UI Shell recovery. This absorption pass does not migrate Project Management code and does not touch `project_storage/`.

## Minimum Required Capabilities

| Capability | Required State | Current Evidence | Status | Best Source Search |
| --- | --- | --- | --- | --- |
| Project creation | User can create a project with stored metadata | not confirmed in this pass | pending | Search old MainLine, UI Shell, Integration, and module branches |
| Project settings | User can view/edit project configuration | not confirmed in this pass | pending | Search old MainLine, UI Shell, Integration, and module branches |
| File import | User can import project input files | not confirmed in this pass | pending | Search Bioinformatics, Meta, and old project pages |
| History / recent projects | User can reopen previous projects | not confirmed in this pass | pending | Search shell and project storage abstractions |
| Workspace/session records | Runtime records current workspace state | not confirmed in this pass | pending | Search shell/session services |
| Project path/storage policy | User-visible path and storage rules exist | not confirmed in this pass | pending | Search project models and storage services |
| User-visible project status | Home shows meaningful project state | not confirmed in this pass | pending | Search project home and dashboard models |

## Prohibited Shortcuts

- Do not treat a static image or decorative card as Project Management.
- Do not merge a whole branch to recover Project Management.
- Do not touch `project_storage/` during planning.
- Do not replace current project/session behavior without tests.

## Next Required Audit

Find the best historical implementation for project creation, settings, file import, history, and workspace/session state, then prepare a scoped restore plan.
