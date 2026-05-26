# PaddleOCR Local Runtime Acceptance - 2026-05-22

## Scope

This stage accepts PaddleOCR as a local external OCR runtime for Meta Analysis full-text PDF / image OCR.

PaddleOCR remains an external engine. The packaged app includes the `biomedpilot_ocr_worker` module, but it does not bundle the PaddleOCR virtualenv, model assets, runtime manifest, or downloaded OCR models.

## Runtime

- runtime root: `~/Library/Application Support/BioMedPilot/engines/ocr/paddleocr`
- manifest: `runtime_manifest.json`
- engine id: `paddleocr_local`
- runtime id: `paddleocr-macos-arm64-python312-smoke-20260517`
- Python: `3.12.13`
- packages detected:
  - `paddleocr 3.5.0`
  - `paddlepaddle 3.3.1`
  - `paddlex 3.5.2`
  - `pymupdf 1.27.2.3`
  - `pillow 12.2.0`

## Acceptance Checks

Command:

```bash
python3 scripts/paddleocr_local_runtime_acceptance.py \
  --paddleocr-source-root "/Users/changdali/Desktop/PaddleOCR-main" \
  --packaged-resource-root "dist/BioMedPilot Integration Preview.app/Contents/Resources/app"
```

Result:

- runtime detect: passed
- source image OCR worker: passed
- source PDF OCR worker: passed
- packaged image OCR worker: passed
- packaged PDF OCR worker: passed
- local PaddleOCR source-root override: passed
- Meta full-text `use_ocr=True`: passed
- package boundary: passed, no bundled PaddleOCR runtime found

Acceptance result:

```text
~/Library/Application Support/BioMedPilot/engines/ocr/paddleocr/smoke/acceptance_20260522T150447Z/paddleocr_local_runtime_acceptance.json
```

## Product Boundaries

- No automatic PDF download was introduced.
- No paywall or institutional access bypass was introduced.
- OCR output remains auxiliary full-text acquisition output.
- OCR parse level remains `ocr_testing`.
- OCR does not write final extraction records.
- OCR does not write screening decisions.
- OCR does not write quality assessments.
- OCR does not change PRISMA included/excluded counts.

## Packaging Boundary

The Integration Preview app contains:

- `biomedpilot_ocr_worker/__main__.py`

The Integration Preview app does not contain:

- PaddleOCR virtualenv
- PaddleOCR model assets
- `.paddlex`
- `runtime_manifest.json`
- `paddleocr` / `paddlepaddle` runtime package directories

This keeps the large external runtime outside `.app` for now. Final distribution can later choose a managed installer or bundled runtime policy, but this acceptance stage only validates local external runtime use.

## Source Integration

The worker now isolates PaddleOCR-specific behavior in `biomedpilot_ocr_worker/paddleocr_engine.py`.

The adapter follows the local source audit from:

```text
/Users/changdali/Desktop/PaddleOCR-main
```

Integrated source-derived behavior:

- `PaddleOCR(...).predict(...)` high-level PP-OCRv5 pipeline entry.
- `FLAGS_allocator_strategy=auto_growth` runtime setting.
- PDF page rendering through PyMuPDF at 2x scale with fallback to 1x for pages larger than 2000 px.
- Text block ordering by top/left box coordinates.
- Reserved table output field without writing final extraction/table records.

The worker supports a developer/runtime override:

```text
BIOMEDPILOT_PADDLEOCR_SOURCE_ROOT=/Users/changdali/Desktop/PaddleOCR-main
```

This lets local acceptance prove the worker can import the user's PaddleOCR source checkout. It remains optional and is not required for packaged users when the external runtime already has `paddleocr` installed.
