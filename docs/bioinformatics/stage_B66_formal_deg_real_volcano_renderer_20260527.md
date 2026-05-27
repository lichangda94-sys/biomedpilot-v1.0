# B66 Formal DEG Real Volcano Renderer

## Audit

Before B66, formal DEG plot artifacts were source-result-driven and registered in the result index, but they were spec-only. The production renderer gate defaulted to `real_deg_plot_renderer_not_activated`.

## Implementation

- Activated a built-in SVG volcano renderer for `formal_computed_result` DEG sources.
- The renderer uses only the Python standard library.
- Output path: `plots/formal_deg/<result_id>/<plot_id>.svg`.
- The plot artifact now records:
  - SVG image artifact
  - SHA-256 checksum
  - renderer log artifact
  - inherited source semantics
  - no report-ready upgrade
  - no clinical conclusion boundary
- Imported, testing, exploratory, preflight, non-DEG, and missing-table sources remain blocked by the existing formal DEG plot gate.

## Boundary

B66 activates volcano SVG only. Heatmap and broader plot style systems remain separate stages.
