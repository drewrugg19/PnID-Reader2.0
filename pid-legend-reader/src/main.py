from __future__ import annotations

from pathlib import Path

from legend_cropper import (
    build_fixture_symbols_bbox_from_lines,
    crop_region,
    find_fixture_symbols_anchor,
    save_cropped_image,
)
from legend_parser import parse_fixture_records
from pdf_reader import (
    combine_line_like_objects,
    extract_lines,
    extract_rects,
    extract_words,
    find_heading_words,
    get_page,
    open_pdf,
    save_page_image,
)
from utils import ensure_directory, log_step

PDF_PATH = Path("data/input/sample_pid.pdf")
DEBUG_DIR = Path("debug")
OUTPUT_DIR = Path("data/output")
FULL_PAGE_IMAGE_PATH = DEBUG_DIR / "page_1_full.png"
FIXTURE_SECTION_IMAGE_PATH = DEBUG_DIR / "fixture_symbols_section.png"


def main() -> None:
    try:
        log_step("Starting Phase 2: fixture symbols box-line anchored crop")

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

            heading_matches = find_heading_words(words, "FIXTURE SYMBOLS")
            anchor = find_fixture_symbols_anchor(heading_matches or words)

            if anchor is None:
                print("Fixture Symbols heading not found.")
                return

            print(f"Fixture Symbols anchor: {anchor}")

            bbox, debug_info = build_fixture_symbols_bbox_from_lines(
                anchor,
                line_segments,
                words,
                page.width,
                page.height,
            )

            if bbox is None:
                print("Unable to build Fixture Symbols section bbox from nearby table lines.")
                return

            print(
                "Nearby line segments considered:",
                debug_info.get("nearby_line_segments_count", 0),
            )
            print("Chosen boundaries:", debug_info.get("chosen_boundaries", {}))
            print(f"Fixture Symbols bbox: {bbox}")

            cropped_page = crop_region(page, bbox)
            save_cropped_image(cropped_page, str(FIXTURE_SECTION_IMAGE_PATH))
            log_step(f"Saved fixture symbols section image: {FIXTURE_SECTION_IMAGE_PATH}")

            cropped_words = cropped_page.extract_words() or []
            fixture_records = parse_fixture_records(cropped_words, bbox)

            print("\n--- FIXTURE RECORDS ---\n")
            for record in fixture_records:
                side = str(record.get("side", "")).upper() or "UNKNOWN"
                tag = str(record.get("tag") or "UNKNOWN")
                description = " ".join(str(record.get("description") or "").split()).strip()
                print(f"[{side}] {tag} -> {description}")

            if not fixture_records:
                print("(no fixture records)")

    except FileNotFoundError:
        log_step(f"ERROR: PDF file not found: {PDF_PATH}")
    except IndexError:
        log_step("ERROR: Could not access page 1")
    except Exception as error:
        log_step(f"ERROR: Runtime failure - {error}")


if __name__ == "__main__":
    main()
