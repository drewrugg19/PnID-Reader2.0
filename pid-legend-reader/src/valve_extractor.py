from __future__ import annotations


def normalize_text(text: str) -> str:
    return " ".join(str(text).upper().split()).strip()


def _sort_words_reading_order(words: list[dict]) -> list[dict]:
    return sorted(
        words,
        key=lambda word: (
            round(float(word.get("top", 0.0)), 1),
            float(word.get("x0", 0.0)),
        ),
    )


def extract_words_in_region(
    words: list[dict],
    x0: float,
    top: float,
    x1: float,
    bottom: float,
) -> list[dict]:
    region_words: list[dict] = []

    for word in words:
        wx0 = float(word.get("x0", 0.0))
        wx1 = float(word.get("x1", 0.0))
        wtop = float(word.get("top", 0.0))
        wbottom = float(word.get("bottom", 0.0))

        if wx0 >= float(x0) and wx1 <= float(x1) and wtop >= float(top) and wbottom <= float(bottom):
            region_words.append(word)

    return region_words


def extract_nearby_valve_id(
    words: list[dict],
    valve_bbox: tuple[float, float, float, float],
    valve_type: str,
) -> str:
    x0, top, x1, bottom = valve_bbox

    horizontal_margin = 60.0
    vertical_margin = 6.0
    vertical_window = 42.0

    search_x0 = float(x0) - horizontal_margin
    search_x1 = float(x1) + horizontal_margin

    normalized_type = normalize_text(valve_type)

    if normalized_type == "BALL VALVE":
        search_top = max(0.0, float(top) - vertical_window)
        search_bottom = max(0.0, float(top) - vertical_margin)
    elif normalized_type == "BUTTERFLY VALVE":
        search_top = float(bottom) + vertical_margin
        search_bottom = float(bottom) + vertical_window
    else:
        return ""

    nearby_words = extract_words_in_region(words, search_x0, search_top, search_x1, search_bottom)
    sorted_words = _sort_words_reading_order(nearby_words)
    merged = " ".join(str(word.get("text", "")).strip() for word in sorted_words if str(word.get("text", "")).strip())
    return normalize_text(merged)


def build_valve_record(valve_id: str, valve_type: str, drawing_number: str) -> dict[str, str]:
    return {
        "valve_id": valve_id,
        "valve_type": valve_type,
        "drawing_number": drawing_number,
    }
