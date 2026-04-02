# P&ID Legend Reader

Phase 1 project for opening and inspecting P&ID PDF files, with focus on preparing a clean foundation for legend-box extraction and parsing.

## Setup

1. Create and activate a virtual environment:

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

## Run

From the `pid-legend-reader` directory:

```bash
python src/main.py
```

Expected PDF input path:

- `data/input/sample_pid.pdf`

## Future Phases

- Phase 2: Crop candidate legend regions from page coordinates.
- Phase 3: Parse legend entries into structured symbol-description pairs.
- Phase 4: Export parsed legend data to machine-readable outputs.
