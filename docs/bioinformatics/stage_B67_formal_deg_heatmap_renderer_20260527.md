# B67 Formal DEG Heatmap Renderer

## Audit

After B66, volcano SVG rendering was active. DEG heatmap still used the same plot gate but had no real SVG output. Formal DEG result tables usually contain case/control means rather than sample-level expression, so a heatmap renderer must not imply sample-level clustering.

## Implementation

- Activated a built-in SVG `deg_heatmap` renderer.
- The renderer uses `case_mean` and `control_mean` columns from the formal DEG result table.
- Output is explicitly labeled as a Formal DEG Summary Heatmap.
- The plot artifact semantic boundary states `deg_summary_heatmap_not_sample_level_expression_heatmap`.
- Missing case/control mean columns block heatmap rendering.

## Boundary

B67 does not implement sample-level clustered heatmaps. It does not upgrade report-ready eligibility or add clinical interpretation.
