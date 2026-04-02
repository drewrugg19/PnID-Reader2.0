from __future__ import annotations


def _sort_words_reading_order(words: list[dict]) -> list[dict]:
    return sorted(words, key=lambda word: (round(float(word.get("top", 0.0)), 1), float(word.get("x0", 0.0))))


def extract_nearby_valve_id(words: list[dict], valve_bbox: tuple[float, float, float, float], valve_type: str) -> str:
    """
    Extract a valve ID near the symbol bounding box.

    BALL VALVE: searches above the symbol.
    BUTTERFLY VALVE: searches below the symbol.
    """
    x0, top, x1, bottom = valve_bbox

    horizontal_padding = 80.0
    vertical_gap = 4.0
    search_height = 40.0

    search_x0 = float(x0) - horizontal_padding
    search_x1 = float(x1) + horizontal_padding

    upper_type = str(valve_type).strip().upper()
    if upper_type == "BALL VALVE":
        search_top = max(0.0, float(top) - search_height)
        search_bottom = max(0.0, float(top) - vertical_gap)
    elif upper_type == "BUTTERFLY VALVE":
        search_top = float(bottom) + vertical_gap
        search_bottom = float(bottom) + search_height
    else:
        return ""

    nearby_words: list[dict] = []
    for word in words:
        wx0 = float(word.get("x0", 0.0))
        wx1 = float(word.get("x1", 0.0))
        wtop = float(word.get("top", 0.0))
        wbottom = float(word.get("bottom", 0.0))

        if wx1 < search_x0 or wx0 > search_x1:
            continue
        if wbottom < search_top or wtop > search_bottom:
            continue

        nearby_words.append(word)

    sorted_words = _sort_words_reading_order(nearby_words)
    raw_text = " ".join(str(word.get("text", "")).strip() for word in sorted_words if str(word.get("text", "")).strip())

    return " ".join(raw_text.split())


def build_valve_record(valve_id: str, valve_type: str, drawing_number: str = "") -> dict[str, str]:
    return {
        "valve_id": valve_id,
        "valve_type": valve_type,
        "drawing_number": drawing_number,
    }
