# MainLine LabTools Local Engine Scoped Carry-over

Date: 2026-05-14

Scope carried from Integration closure:

- Shared ImageJ/Fiji local engine foundation under `app/shared/local_engines/`.
- Minimal LabTools consumer for ImageJ/Fiji path configuration, status loading,
  explicit detection, and clearing.
- LabTools module icon wiring in the shell without adding a complex local tools
  center on the main screen.
- LabTools image boundary copy and review notice.
- LaunchServices `-psn_*` tolerance and local package signing gate.

Explicitly not carried:

- WB/gel real analysis.
- Agarose gel.
- Cell counting.
- Automatic ROI.
- Pathology workflow.
- Ollama/local LLM.
- Cloud AI, login, credits, or payment behavior.
- A new packaging release artifact.

Bioinformatics note:

- MainLine already contains the GEO Series Matrix species regression coverage
  and parser behavior for `!Sample_organism_ch1`, including `species_group`.
  This carry-over keeps that test in the validation set rather than replacing
  the existing MainLine implementation.
