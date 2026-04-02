from __future__ import annotations

from pathlib import Path

from pdf_reader import extract_text, get_page, open_pdf
from utils import input_path, log


def main() -> None:
    pdf_path: Path = input_path("sample_pid.pdf")

    if not pdf_path.exists():
        log(f"PDF not found: {pdf_path}")
        return

    with open_pdf(pdf_path) as pdf:
        page_count = len(pdf.pages)
        log(f"Pages: {page_count}")

        if page_count == 0:
            log("PDF has no pages.")
            return

        first_page = get_page(pdf, 0)
        log(f"Page 1 size: width={first_page.width}, height={first_page.height}")

        text = extract_text(first_page)
        log("First 1000 characters of extracted text:")
        print(text[:1000])


if __name__ == "__main__":
    main()
