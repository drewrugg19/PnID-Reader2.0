# P&ID Reader - Manual Valve Extraction Test (Actual Drawing Phase)

This phase is focused on debugging valve ID extraction against the **actual P&ID drawing PDF**, not the legend PDF.

## Scope of This Phase

- Uses `data/input/CYW111234640.pdf` (page 1)
- Uses **manual valve test bounding boxes** only
- Does **not** auto-detect valve symbols yet
- Does **not** modify legend parsing logic
- Keeps this valve extraction test path isolated

## Calibration Goal (Manual BBox Tuning)

This step is strictly for calibrating manual valve bounding boxes on the actual P&ID page.

1. Run `python src/main.py`
2. Review the `--- BV WORD DEBUG ---` output to locate real valve ID words and their coordinates
3. (Optional) Review `--- SAMPLE WORD DEBUG ---` output for additional page coordinate context
4. Update `TEST_VALVES` bbox values in `src/main.py` so each valve symbol is positioned correctly relative to nearby ID text
5. Re-run until the valve ID extraction debug output returns expected IDs

## Valve ID Search Direction Rules

- **BALL VALVE** IDs are searched **above** the valve symbol bbox
- **BUTTERFLY VALVE** IDs are searched **below** the valve symbol bbox

## Workflow Being Proven

`manual valve bbox -> valve type -> nearby ID text in search region -> structured valve record`

## Output Record Shape

```json
{
  "valve_id": "...",
  "valve_type": "BALL VALVE",
  "drawing_number": "CYW111234640"
}
```

## Run

From the `pid-legend-reader` directory:

```bash
python src/main.py
```

## Notes

- `src/main.py` contains a dedicated valve extraction debug flow for the actual drawing only.
- The valve flow intentionally avoids legend parsing in this phase.
- Keep this phase simple and manual before adding any valve auto-detection.
