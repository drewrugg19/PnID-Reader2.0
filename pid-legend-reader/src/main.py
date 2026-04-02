from __future__ import annotations

from pathlib import Path

from legend_cropper import (
    build_fixture_symbols_bbox,
    crop_region,
    extract_crop_text,
    find_fixture_symbols_anchor,
    save_cropped_image,
)
from pdf_reader import (
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
        log_step("Starting Phase 2: dynamic Fixture Symbols heading anchor and crop")

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
            heading_matches = find_heading_words(words, "FIXTURE SYMBOLS")
            anchor = find_fixture_symbols_anchor(heading_matches or words)

            if anchor is None:
                print("Fixture Symbols heading not found.")
                return

            print(f"Fixture Symbols anchor: {anchor}")

            local_window = {
                "x0": max(0.0, float(anchor["x0"]) - 450.0),
                "x1": min(float(page.width), float(anchor["x1"]) + 550.0),
                "top": max(0.0, float(anchor["top"]) - 40.0),
                "bottom": min(float(page.height), float(anchor["bottom"]) + 700.0),
            }
            print(f"Local search window: {local_window}")

            bbox, section_words = build_fixture_symbols_bbox(
                anchor,
                words,
                page.width,
                page.height,
            )

            if bbox is None:
                print("Unable to build Fixture Symbols section bbox from detected words.")
                return

            print(f"Words used to build section bbox: {len(section_words)}")
            print(f"Fixture Symbols bbox: {bbox}")

            cropped_page = crop_region(page, bbox)
            save_cropped_image(cropped_page, str(FIXTURE_SECTION_IMAGE_PATH))
            log_step(f"Saved fixture symbols section image: {FIXTURE_SECTION_IMAGE_PATH}")

            cropped_text = extract_crop_text(cropped_page)
            print("Extracted text from fixture symbols crop:")
            if cropped_text:
                print(cropped_text)
            else:
                print("(no text found)")

    except FileNotFoundError:
        log_step(f"ERROR: PDF file not found: {PDF_PATH}")
    except IndexError:
        log_step("ERROR: Could not access page 1")
    except Exception as error:
        log_step(f"ERROR: Runtime failure - {error}")


if __name__ == "__main__":
    main()
