from __future__ import annotations

from pathlib import Path

from pdf_reader import extract_words, get_page, open_pdf
from valve_extractor import build_valve_record, extract_nearby_valve_id

PDF_PATH = Path("data/input/CYW111234640.pdf")


def run_manual_valve_extraction_test() -> list[dict[str, str]]:
    if not PDF_PATH.exists():
        print(f"ERROR: Missing PDF file at '{PDF_PATH}'")
        return []

    with open_pdf(str(PDF_PATH)) as pdf:
        if not pdf.pages:
            print("ERROR: PDF has no pages")
            return []

        page = get_page(pdf, 0)
        words = extract_words(page)

        drawing_number = "CYW111234640"

        print("\n--- BV WORD DEBUG ---")
        for word in words:
            if "BV" in word.get("text", ""):
                print(word)

        TEST_VALVES = [
            {
                "type": "BALL VALVE",
                "bbox": (100.0, 100.0, 160.0, 140.0),
            },
            {
                "type": "BUTTERFLY VALVE",
                "bbox": (220.0, 220.0, 280.0, 260.0),
            },
        ]

        valve_records: list[dict[str, str]] = []

        for valve in TEST_VALVES:
            valve_type = valve["type"]
            valve_bbox = valve["bbox"]

            valve_id = extract_nearby_valve_id(
                words=words,
                valve_bbox=valve_bbox,
                valve_type=valve_type,
                debug=True,
            )
            record = build_valve_record(
                valve_id=valve_id,
                valve_type=valve_type,
                drawing_number=drawing_number,
            )
            valve_records.append(record)

            print("\n--- VALVE EXTRACTION TEST ---")
            print(f"TYPE: {valve_type}")
            print(f"ID: {valve_id}")
            print(f"DRAWING: {drawing_number}")

        print("\n--- FINAL VALVE RECORDS ---")
        print(valve_records)

        return valve_records


def main() -> None:
    run_manual_valve_extraction_test()


if __name__ == "__main__":
    main()
