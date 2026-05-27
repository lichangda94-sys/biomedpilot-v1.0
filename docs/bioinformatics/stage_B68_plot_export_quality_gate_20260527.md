# B68 Plot QC / Export Quality Gate

## Audit

B66-B67 generate real SVG artifacts. A dedicated QC gate was still needed to validate image existence, non-empty output, checksum consistency, SVG structure, inherited semantics, and clinical boundary text.

## Implementation

- Added `biomedpilot.plot_export_quality_gate.v1`.
- The gate validates:
  - formal plot source semantics
  - plot semantics inheritance
  - image artifact presence
  - image file existence and size
  - SHA-256 checksum
  - SVG root structure
  - clinical boundary copy
  - no report-ready upgrade

## Boundary

The QC gate does not create plots or reports. It only validates generated plot artifacts.
