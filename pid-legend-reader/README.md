# P&ID Legend Reader

This repository is currently in **Phase 2**.

## What This Phase Does

This phase now supports reusable multi-section legend detection and cropping from page 1.

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
10. Continues full parsing only for **Fixture Symbols** records

This phase does **not** include OCR, OpenCV, symbol recognition, machine learning, full Piping Elements parsing, or full Valve Symbols parsing.

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
- **Only Fixture Symbols is fully parsed** at this stage.
- Piping Elements and Valve Symbols are currently cropped/debugged for the next phase.
