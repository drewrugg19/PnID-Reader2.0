# P&ID Reader - Manual Valve Extraction Test (Actual Drawing Phase)

This phase is focused on debugging valve ID extraction against the **actual P&ID drawing PDF**, not the legend PDF.

## Scope of This Phase

- Uses `data/input/CYW111234640.pdf` (page 1)
- Uses **manual valve test bounding boxes** only
- Does **not** auto-detect valve symbols yet
- Does **not** modify legend parsing logic
- Keeps this valve extraction test path isolated

## Supported Valve Types

- **BALL VALVE**
- **BUTTERFLY VALVE**

## Valve ID Search Direction Rules

- **BALL VALVE** IDs are searched **above** the valve symbol bbox
- **BUTTERFLY VALVE** IDs are searched **below** the valve symbol bbox

## Workflow Being Proven

`valve bbox -> valve type -> nearby ID text -> structured valve record`

## Debugging Objective

The goal of this phase is to tune manual valve bboxes on the real drawing:

1. Print all page words containing `BV`
2. Inspect coordinates from debug output
3. Adjust `TEST_VALVES` bbox values in `src/main.py`
4. Re-run and verify extracted valve IDs

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

- `src/main.py` contains a dedicated valve extraction debug flow for the actual drawing.
- Use the `--- BV WORD DEBUG ---` output to tune manual test bounding boxes.
- Keep this phase simple and manual before adding any auto-detection.
