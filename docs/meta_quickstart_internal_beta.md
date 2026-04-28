# Meta Analysis Internal Beta Quickstart

1. Start from the BioMedPilot project root.
2. Run the smoke test:

```bash
python3 -m app.main --smoke-test
```

3. Use the Stage M sample inputs from:

```text
examples/meta_analysis_e2e_project/inputs/
```

4. Follow the testing chain:

```text
Import -> Prepare Screening -> Duplicate Review -> Screening -> Extraction -> Quality -> Analysis -> Reporting
```

5. Review generated warnings and manifests before interpreting any result.

Do not treat testing reports, figures, or pooled estimates as production outputs.

