from __future__ import annotations


def crop_region(page, bbox):
    """Crop and return a page region using bbox=(x0, top, x1, bottom)."""
    return page.crop(bbox)


def save_cropped_image(cropped_page, output_path: str, resolution: int = 150):
    """Render and save a cropped page image to disk."""
    cropped_image = cropped_page.to_image(resolution=resolution)
    cropped_image.save(output_path)


def extract_crop_text(cropped_page) -> str:
    """Extract and safely normalize text from a cropped region."""
    text = cropped_page.extract_text()
    if text is None:
        return ""
    return text.strip()
