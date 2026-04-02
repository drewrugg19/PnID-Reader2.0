from __future__ import annotations

from pathlib import Path

from legend_cropper import (
    build_section_bbox_from_lines,
    crop_region,
    find_section_anchor_record,
    save_cropped_image,
)
from legend_parser import parse_section
from pdf_reader import (
    combine_line_like_objects,
    extract_lines,
    extract_rects,
    extract_words,
    get_page,
    open_pdf,
    save_page_image,
)
from utils import ensure_directory, log_step

PDF_PATH = Path("data/input/sample_pid.pdf")
DEBUG_DIR = Path("debug")
OUTPUT_DIR = Path("data/output")
FULL_PAGE_IMAGE_PATH = DEBUG_DIR / "page_1_full.png"

SECTIONS = [
    {"key": "valve_symbols", "label": "VALVE SYMBOLS", "output": "debug/valve_symbols.png"},
    {"key": "piping_elements", "label": "PIPING ELEMENT", "output": "debug/piping_elements.png"},
    {"key": "fixture_symbols", "label": "FIXTURE SYMBOLS", "output": "debug/fixture_symbols.png"},
]

SECTION_SETTINGS_NAMES = {
    "valve_symbols": "VALVE SYMBOLS",
    "piping_elements": "PIPING ELEMENTS",
    "fixture_symbols": "FIXTURE SYMBOLS",
}


def main() -> None:
    try:
        log_step("Starting Phase 2: multi-section legend detection and cropping")

        ensure_directory(str(DEBUG_DIR))
        ensure_directory(str(OUTPUT_DIR))

        if not PDF_PATH.exists():
            log_step(f"ERROR: Missing PDF file at '{PDF_PATH}'")
            return

        with open_pdf(str(PDF_PATH)) as pdf:
            if not pdf.pages:
                log_step("ERROR: PDF has no pages")
                return

            page = get_page(pdf, 0)
            save_page_image(page, str(FULL_PAGE_IMAGE_PATH))
            log_step(f"Saved full-page debug image: {FULL_PAGE_IMAGE_PATH}")

            words = extract_words(page)
            lines = extract_lines(page)
            rects = extract_rects(page)
            line_segments = combine_line_like_objects(page)

            print(f"Extracted words: {len(words)}")
            print(f"Extracted lines: {len(lines)}")
            print(f"Extracted rects: {len(rects)}")
            print(f"Combined line-like segments: {len(line_segments)}")

            section_results: dict[str, dict] = {}

            found_sections: list[dict] = []
            for section in SECTIONS:
                record = find_section_anchor_record(words, section["key"], section["label"])
                if record is None:
                    continue

                found_record = {
                    "section_key": section["key"],
                    "target_label": section["label"],
                    "matched_text": record["matched_text"],
                    "anchor": record["anchor"],
                    "output": section["output"],
                    "settings_name": SECTION_SETTINGS_NAMES.get(section["key"], section["label"]),
                }
                found_sections.append(found_record)

                print("\nSECTION KEY:", found_record["section_key"])
                print("TARGET LABEL:", found_record["target_label"])
                print("MATCHED TEXT:", found_record["matched_text"])
                print("ANCHOR:", found_record["anchor"])

            found_sections.sort(key=lambda item: float(item["anchor"]["top"]))

            for i, current in enumerate(found_sections):
                next_record = found_sections[i + 1] if i + 1 < len(found_sections) else None
                next_anchor = next_record["anchor"] if next_record else None

                bbox, debug_info = build_section_bbox_from_lines(
                    current["anchor"],
                    next_anchor,
                    current["settings_name"],
                    line_segments,
                    words,
                    page.width,
                    page.height,
                )

                output_path = Path(current["output"])
                cropped_page = crop_region(page, bbox)
                save_cropped_image(cropped_page, str(output_path))

                print("\nSECTION KEY:", current["section_key"])
                print("BBOX:", bbox)
                print("OUTPUT:", current["output"])

                section_results[current["section_key"]] = {
                    "found": True,
                    "target_label": current["target_label"],
                    "matched_text": current["matched_text"],
                    "anchor": current["anchor"],
                    "bbox": bbox,
                    "debug_path": current["output"],
                    "crop": cropped_page,
                    "top_line": debug_info.get("top_line"),
                    "bottom_line": debug_info.get("bottom_line"),
                }

            for section in SECTIONS:
                key = section["key"]
                if key not in section_results:
                    print("\nSECTION KEY:", key)
                    print("TARGET LABEL:", section["label"])
                    print("MATCHED TEXT:", None)
                    print("ANCHOR:", None)
                    section_results[key] = {
                        "found": False,
                        "target_label": section["label"],
                        "matched_text": None,
                        "anchor": None,
                        "bbox": None,
                        "debug_path": None,
                        "crop": None,
                        "top_line": None,
                        "bottom_line": None,
                    }

            all_section_records: list[dict[str, str]] = []

            fixture_result = section_results.get("fixture_symbols")
            fixture_records: list[dict[str, str]] = []
            if fixture_result and fixture_result.get("found") and fixture_result.get("crop") is not None:
                fixture_words = fixture_result["crop"].extract_words() or []
                fixture_records = parse_section(fixture_words, "fixture")
                all_section_records.extend(fixture_records)

            print("\n--- FIXTURE RECORDS ---\n")
            for record in fixture_records:
                print(f"[L] {record['left']} -> {record['right']}")
            if not fixture_records:
                print("(no fixture records)")

            piping_result = section_results.get("piping_elements")
            piping_records: list[dict[str, str]] = []
            if piping_result and piping_result.get("found") and piping_result.get("crop") is not None:
                piping_words = piping_result["crop"].extract_words() or []
                piping_records = parse_section(piping_words, "piping")
                all_section_records.extend(piping_records)

            print("\n--- PIPING RECORDS ---\n")
            for record in piping_records:
                print(f"[L] {record['left']} -> {record['right']}")
            if not piping_records:
                print("(no piping records)")

            valve_result = section_results.get("valve_symbols")
            valve_records: list[dict[str, str]] = []
            if valve_result and valve_result.get("found") and valve_result.get("crop") is not None:
                valve_words = valve_result["crop"].extract_words() or []
                valve_records = parse_section(valve_words, "valve")
                all_section_records.extend(valve_records)

            print("\n--- VALVE RECORDS ---\n")
            for record in valve_records:
                print(f"[L] {record['left']} -> {record['right']}")
            if not valve_records:
                print("(no valve records)")

            print("\n--- ALL SECTION RECORDS ---\n")
            for record in all_section_records:
                print(record)
            if not all_section_records:
                print("(no records)")

            print("\n--- SECTION SUMMARY ---")
            for section in SECTIONS:
                key = section["key"]
                result = section_results.get(key, {})
                if not result.get("found"):
                    print(f"{key}: NOT FOUND")
                    continue

                print(
                    f"{key}: FOUND | target={result.get('target_label')} | matched={result.get('matched_text')} | "
                    f"anchor={result.get('anchor')} | top_line={result.get('top_line')} | "
                    f"bottom_line={result.get('bottom_line')} | bbox={result.get('bbox')} | "
                    f"output={result.get('debug_path')}"
                )

    except FileNotFoundError:
        log_step(f"ERROR: PDF file not found: {PDF_PATH}")
    except IndexError:
        log_step("ERROR: Could not access page 1")
    except Exception as error:
        log_step(f"ERROR: Runtime failure - {error}")


if __name__ == "__main__":
    main()
