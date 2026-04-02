# P&ID Legend Reader

This repository is currently in **Phase 2**.

## What This Phase Does

This phase is focused on dynamically locating and cropping only the **Fixture Symbols** section.

The script now:

1. Opens the PDF
2. Reads page 1
3. Saves a full-page debug image
4. Extracts word-level data
5. Extracts structural line and rectangle data from `pdfplumber`
6. Combines line + rectangle edges into normalized line-like segments
7. Finds the **"FIXTURE SYMBOLS"** heading anchor
8. Searches for nearby table borders around that anchor (left, right, and top)
9. Builds the crop box primarily from those detected table borders
10. Uses words only to estimate the lower content extent (bottom)
11. Saves the cropped section image
12. Extracts and prints text from the cropped region

This line-based approach is more reliable than broad word-only bounds because it is anchored to the visible table box around the Fixture Symbols section.

This phase does **not** include OCR, OpenCV, symbol recognition, machine learning, row parsing, symbol/text column splitting, or full legend parsing.

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
- `debug/fixture_symbols_section.png`

The script also ensures these folders exist:

- `debug/`
- `data/output/`

## Status Note

This is still an intermediate phase before row-by-row legend parsing.
The current goal is only accurate table-border anchored section cropping for **Fixture Symbols**.
