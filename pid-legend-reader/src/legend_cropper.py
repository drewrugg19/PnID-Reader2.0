from __future__ import annotations


def crop_region(page, bbox):
    """Return a cropped region from a page using the provided bounding box."""
    return page.crop(bbox)
