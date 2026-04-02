# P&ID Legend Reader

This repository is currently in **Phase 2** with an added **valve extraction test path**.

## What This Phase Does

This phase supports reusable multi-section legend detection and cropping from page 1.

The script now:

1. Opens the PDF
2. Reads page 1
3. Saves a full-page debug image
4. Extracts word-level data
5. Extracts structural line and rectangle data from `pdfplumber`
6. Combines line + rectangle edges into normalized line-like segments
7. Detects section anchors for:
   - **FIXTURE SYMBOLS**
   - **PIPING ELEMENTS**
   - **VALVE SYMBOLS**
8. Builds each section crop box from nearby line borders with word-based bottom estimation
9. Saves one debug crop image per detected section
10. Parses section records in the existing legend path
11. Runs a separate valve extraction test flow from drawing symbol bboxes

## New Valve Extraction Path (Drawing Symbols)

This phase adds a new, separate path for valve extraction from the **actual drawing symbols** (not legend parsing).

### Currently Supported Valve Types

- **BALL VALVE**
- **BUTTERFLY VALVE**

### Current Valve ID Rule

Valve IDs are searched relative to symbol position:

- **BALL VALVE**: search text **above** the symbol bbox
- **BUTTERFLY VALVE**: search text **below** the symbol bbox

### Current Output Shape

Each extracted valve is returned as:

```json
{
  "valve_id": "",
  "valve_type": "BALL VALVE",
  "drawing_number": ""
}
```

`drawing_number` is a placeholder in this phase and will be extracted later.

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
- `debug/fixture_symbols.png` (if detected)
- `debug/piping_elements.png` (if detected)
- `debug/valve_symbols.png` (if detected)

The script also ensures these folders exist:

- `debug/`
- `data/output/`

## Status Note

- Section detection and cropping are implemented for Fixture Symbols, Piping Elements, and Valve Symbols.
- The new valve extraction workflow is now present:
  `symbol bbox -> valve type -> nearby ID text -> structured record`.
- This phase does **not** add OCR, machine learning, or broad symbol automation.
