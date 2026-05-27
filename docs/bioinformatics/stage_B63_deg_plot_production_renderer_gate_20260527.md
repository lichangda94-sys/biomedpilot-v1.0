# B63 DEG Plot Production Renderer Gate

## Audit

Formal DEG plot artifacts can be registered as source-result-driven plot specs. A separate production renderer gate was missing, so it was not explicit whether a real image renderer was available.

## Implementation

- Added `biomedpilot.formal_deg_plot_production_gate.v1`.
- The gate wraps the existing formal DEG plot source gate.
- It requires an explicit renderer capability snapshot before production plot readiness can pass.
- Default capability is blocked with `real_deg_plot_renderer_not_activated`.
- The gate records source semantics inheritance, result index registration intent, no report-ready upgrade, and no clinical conclusion.

## Boundary

No new renderer backend was activated. Existing spec artifact creation remains unchanged.
