# Project Management Restore Plan

Date: 2026-05-29

## Current Decision

The `9d4edf3` UI preview is accepted as the UI Shell visual baseline, but its Project Management surface is regressed because it presents an image-like entry rather than a complete project management module.

MainLine home cannot be called complete until Project Management is restored or explicitly replaced by a tested equivalent.

## Minimum Required Capabilities

| Capability | Required State | Current Evidence | Status | Best Source Search |
| --- | --- | --- | --- | --- |
| Project creation | User can create a project with stored metadata | not confirmed | pending | Search old MainLine, UI Shell, Integration, module branches |
| Project settings | User can view/edit project configuration | not confirmed | pending | Search old MainLine, UI Shell, Integration, module branches |
| File import | User can import project input files | not confirmed | pending | Search Bioinformatics, Meta, old project pages |
| History / recent projects | User can reopen previous projects | not confirmed | pending | Search shell and project storage abstractions |
| Workspace/session records | Runtime records current workspace state | not confirmed | pending | Search shell/session services |
| Project path/storage policy | User-visible path and storage rules exist | not confirmed | pending | Search project models and storage services |
| User-visible project status | Home shows meaningful project state | not confirmed | pending | Search project home and dashboard models |

## Restore Strategy Template

| Candidate Source | Commit | Files | Capability Covered | Risk | Direct Migration Allowed? | Proposed Method |
| --- | --- | --- | --- | --- | --- | --- |
| needs audit | needs audit | needs audit | needs audit | needs audit | no | scoped plan required |

## Prohibited Shortcuts

- Do not treat a static image or decorative card as Project Management.
- Do not merge a whole branch to recover Project Management.
- Do not touch `project_storage/` during planning.
- Do not replace current project/session behavior without tests.

## Next Required Audit

Find the best historical implementation for project creation, settings, file import, history, and workspace/session state, then prepare a scoped restore plan.
