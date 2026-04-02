# P&ID Legend Reader

This repository is currently in **Phase 2**.

## What Phase 2 Does

Phase 2 is intentionally small and focused on manual debugging of one legend box region:

1. Open a PDF file
2. Read page 1
3. Save a full-page debug image
4. Crop one manually defined bounding box (bbox)
5. Save the cropped image
6. Extract text from the cropped region
7. Print clear debug output to the console

This phase does **not** include OCR, automatic detection, symbol recognition, OpenCV, or full legend parsing.

## Input PDF

Place your test PDF at:

- `data/input/sample_pid.pdf`

## Run

From the `pid-legend-reader` directory:

```bash
python src/main.py
```

## Debug Output Files Created

Running the script creates:

- `debug/page_1_full.png`
- `debug/page_1_crop.png`

The script also ensures these folders exist:

- `debug/`
- `data/output/`

## Manual BBox Note

The bbox values are **manually set for now** (for example `(100, 100, 350, 250)`).
They are expected to be tuned as needed in later steps.
