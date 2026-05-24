# LabTools Future LAN And Cloud Adapter Boundary

LAN and cloud sync are future adapter options, not current LabTools behavior.

The current implementation has no LAN server, no cloud sync, no multi-user permission model, and no automatic conflict merge. Future adapters must reuse the local data contract fields, version checks, audit log events, and source mode values.

Future LAN/cloud work must enter through a `LabToolsDataSourceAdapter` implementation. It must not require UI pages to read remote payloads directly, and it must not rely on sharing local JSON or SQLite files across machines.
