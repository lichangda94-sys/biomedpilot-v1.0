# Meta Analysis Internal Beta Quickstart

1. Start from the BioMedPilot project root.
2. Run the smoke test:

```bash
python3 -m app.main --smoke-test
```

3. Use the Stage M mock sample inputs from:

```text
examples/meta_analysis_e2e_project/inputs/
```

4. Use the Stage W PubMed-derived realistic sample inputs from:

```text
examples/meta_analysis_realistic_project/inputs/
```

5. Follow the testing chain:

```text
Import -> Prepare Screening -> Duplicate Review -> Screening -> Extraction -> Quality -> Analysis -> Reporting
```

6. Review generated warnings and manifests before interpreting any result.

Do not treat testing reports, figures, or pooled estimates as production outputs.
