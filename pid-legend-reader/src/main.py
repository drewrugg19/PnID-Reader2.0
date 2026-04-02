from __future__ import annotations

from pathlib import Path

from legend_cropper import crop_region, extract_crop_text, save_cropped_image
from pdf_reader import get_page, open_pdf, save_page_image
from utils import ensure_directory, log_step

PDF_PATH = Path("data/input/sample_pid.pdf")
DEBUG_DIR = Path("debug")
OUTPUT_DIR = Path("data/output")
FULL_PAGE_IMAGE_PATH = DEBUG_DIR / "page_1_full.png"
CROPPED_IMAGE_PATH = DEBUG_DIR / "page_1_crop.png"
TEST_BBOX = (100, 100, 350, 250)


def main() -> None:
    try:
        log_step("Starting Phase 2: manual crop and inspect one legend box")

        ensure_directory(str(DEBUG_DIR))
        ensure_directory(str(OUTPUT_DIR))
        log_step(f"Ensured output directories: {DEBUG_DIR} and {OUTPUT_DIR}")

        if not PDF_PATH.exists():
            log_step(f"ERROR: Missing PDF file at '{PDF_PATH}'")
            return

        with open_pdf(str(PDF_PATH)) as pdf:
            page_count = len(pdf.pages)
            print(f"Page count: {page_count}")

            if page_count == 0:
                log_step("ERROR: PDF has no pages")
                return

            try:
                page = get_page(pdf, 0)
            except IndexError:
                log_step("ERROR: Could not access page index 0")
                return

            print(f"Page width: {page.width}")
            print(f"Page height: {page.height}")

            save_page_image(page, str(FULL_PAGE_IMAGE_PATH))
            log_step(f"Saved full-page debug image: {FULL_PAGE_IMAGE_PATH}")

            cropped_page = crop_region(page, TEST_BBOX)
            save_cropped_image(cropped_page, str(CROPPED_IMAGE_PATH))
            log_step(f"Saved cropped debug image: {CROPPED_IMAGE_PATH}")

            cropped_text = extract_crop_text(cropped_page)

            print(f"BBox used: {TEST_BBOX}")
            if cropped_text:
                print("Cropped text:")
                print(cropped_text)
            else:
                print("Cropped text: No text found in the selected region.")

    except Exception as error:
        log_step(f"ERROR: Runtime failure - {error}")


if __name__ == "__main__":
    main()
