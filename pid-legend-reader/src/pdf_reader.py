from __future__ import annotations

from pathlib import Path

import pdfplumber


def open_pdf(path: str | Path) -> pdfplumber.PDF:
    """Open and return a PDF document."""
    return pdfplumber.open(str(path))


def get_page(pdf: pdfplumber.PDF, index: int) -> pdfplumber.page.Page:
    """Return a page by index from an open PDF."""
    return pdf.pages[index]


def extract_text(page: pdfplumber.page.Page) -> str:
    """Extract text from a PDF page."""
    return page.extract_text() or ""
