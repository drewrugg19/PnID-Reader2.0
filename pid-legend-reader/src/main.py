from __future__ import annotations

from pathlib import Path

from legend_cropper import (
    build_section_bbox_from_lines,
    crop_region,
    find_section_anchor,
    save_cropped_image,
)
from legend_parser import parse_fixture_records
from pdf_reader import (
    combine_line_like_objects,
    extract_lines,
    extract_rects,
    extract_words,
    get_page,
    open_pdf,
    save_page_image,
)
from section_config import SECTION_NAMES, normalize_section_name
from utils import ensure_directory, log_step

PDF_PATH = Path("data/input/sample_pid.pdf")
DEBUG_DIR = Path("debug")
OUTPUT_DIR = Path("data/output")
FULL_PAGE_IMAGE_PATH = DEBUG_DIR / "page_1_full.png"


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
            for section_name in SECTION_NAMES:
                anchor = find_section_anchor(words, section_name)
                if anchor is not None:
                    found_sections.append({"section_name": section_name, "anchor": anchor})

            found_sections.sort(key=lambda item: float(item["anchor"]["top"]))

            for i, current in enumerate(found_sections):
                section_name = current["section_name"]
                anchor = current["anchor"]
                next_anchor = found_sections[i + 1]["anchor"] if i + 1 < len(found_sections) else None

                print(f"\n--- SECTION: {section_name} ---")

                bbox, debug_info = build_section_bbox_from_lines(
                    anchor,
                    next_anchor,
                    section_name,
                    line_segments,
                    words,
                    page.width,
                    page.height,
                )

                normalized_name = normalize_section_name(section_name)
                debug_image_path = DEBUG_DIR / f"{normalized_name}.png"

                cropped_page = crop_region(page, bbox)
                save_cropped_image(cropped_page, str(debug_image_path))

                print(f"{section_name}: found")
                print(f"Anchor: {anchor}")
                print(f"Top line: {debug_info.get('top_line')}")
                print(f"Bottom line: {debug_info.get('bottom_line')}")
                print(f"BBox: {bbox}")
                print(f"Output image: {debug_image_path}")
                print("Nearby line segments considered:", debug_info.get("nearby_line_segments_count", 0))

                section_results[section_name] = {
                    "found": True,
                    "anchor": anchor,
                    "bbox": bbox,
                    "debug_path": str(debug_image_path),
                    "crop": cropped_page,
                    "top_line": debug_info.get("top_line"),
                    "bottom_line": debug_info.get("bottom_line"),
                }

            for section_name in SECTION_NAMES:
                if section_name not in section_results:
                    print(f"\n--- SECTION: {section_name} ---")
                    print(f"{section_name}: not found")
                    section_results[section_name] = {
                        "found": False,
                        "anchor": None,
                        "bbox": None,
                        "debug_path": None,
                        "crop": None,
                        "top_line": None,
                        "bottom_line": None,
                    }

            fixture_result = section_results.get("FIXTURE SYMBOLS")
            if not fixture_result or not fixture_result.get("found"):
                print("\nFixture Symbols not available for parsing.")
                return

            fixture_crop = fixture_result.get("crop")
            if fixture_crop is None:
                print("\nFixture Symbols crop is missing.")
                return

            fixture_bbox = fixture_result.get("bbox")
            cropped_words = fixture_crop.extract_words() or []
            fixture_records = parse_fixture_records(cropped_words, fixture_bbox)

            print("\n--- FIXTURE RECORDS ---\n")
            for record in fixture_records:
                side = str(record.get("side", "")).upper() or "UNKNOWN"
                tag = str(record.get("tag") or "UNKNOWN")
                description = " ".join(str(record.get("description") or "").split()).strip()
                print(f"[{side}] {tag} -> {description}")

            if not fixture_records:
                print("(no fixture records)")

            print("\n--- SECTION SUMMARY ---")
            for section_name in SECTION_NAMES:
                result = section_results.get(section_name, {})
                if not result.get("found"):
                    print(f"{section_name}: NOT FOUND")
                    continue

                print(
                    f"{section_name}: FOUND | anchor={result.get('anchor')} | "
                    f"top_line={result.get('top_line')} | bottom_line={result.get('bottom_line')} | "
                    f"bbox={result.get('bbox')} | output={result.get('debug_path')}"
                )

    except FileNotFoundError:
        log_step(f"ERROR: PDF file not found: {PDF_PATH}")
    except IndexError:
        log_step("ERROR: Could not access page 1")
    except Exception as error:
        log_step(f"ERROR: Runtime failure - {error}")


if __name__ == "__main__":
    main()
