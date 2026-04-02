# P&ID Legend Reader

This repository is currently in **Phase 2**.

## What This Phase Does

This phase is a baby-step workflow focused only on dynamically locating and cropping the **Fixture Symbols** section.

The script now:

1. Opens the PDF
2. Reads page 1
3. Saves a full-page debug image
4. Extracts word-level data from the page
5. Searches for the **"FIXTURE SYMBOLS"** heading text dynamically
6. Uses the heading coordinates as an anchor
7. Builds a **tight local search window** around that heading anchor
8. Collects only words inside that local window
9. Builds the crop box from only those local words (while keeping the heading included)
10. Saves the cropped section image
11. Extracts and prints text from the cropped region

This tighter local-window approach helps avoid pulling in nearby notes/specs columns and adjacent legend boxes that are outside the Fixture Symbols section.

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
The current goal is only accurate heading-anchored local section cropping for **Fixture Symbols**.
