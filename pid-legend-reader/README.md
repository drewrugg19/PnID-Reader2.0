# P&ID Reader - Manual Valve Extraction Test (Phase)

This phase focuses on proving valve extraction workflow on an **actual P&ID drawing page**, not on legend parsing.

## Scope of This Phase

- Uses `data/input/CYW111234640.pdf` (page 1)
- Uses **manual valve bounding boxes** only
- Does **not** auto-detect valve symbols
- Keeps legend parsing logic untouched

## Supported Valve Types

- **BALL VALVE**
- **BUTTERFLY VALVE**

## Expected Valve ID Direction

- **BALL VALVE**: valve ID is searched **above** the symbol bbox
- **BUTTERFLY VALVE**: valve ID is searched **below** the symbol bbox

## Workflow Being Proven

`symbol bbox -> valve type -> nearby ID -> structured record`

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

- `src/main.py` contains a dedicated, isolated manual valve test flow.
- Update the manual `TEST_VALVES` bounding boxes with real coordinates from your target page as needed.
