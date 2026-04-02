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

    rx0 = float(x0)
    rx1 = float(x1)
    rtop = float(top)
    rbottom = float(bottom)

    for word in words:
        wx0 = float(word.get("x0", 0.0))
        wx1 = float(word.get("x1", 0.0))
        wtop = float(word.get("top", 0.0))
        wbottom = float(word.get("bottom", 0.0))

        overlaps_horizontally = wx0 <= rx1 and wx1 >= rx0
        overlaps_vertically = wtop <= rbottom and wbottom >= rtop

        if overlaps_horizontally and overlaps_vertically:
            region_words.append(word)

    return region_words


def extract_nearby_valve_id(
    words: list[dict],
    valve_bbox: tuple[float, float, float, float],
    valve_type: str,
    debug: bool = False,
) -> str:
    x0, top, x1, bottom = valve_bbox

    normalized_type = normalize_text(valve_type)

    if normalized_type == "BALL VALVE":
        search_x0 = float(x0) - 80.0
        search_x1 = float(x1) + 80.0
        search_top = float(top) - 120.0
        search_bottom = float(top) - 5.0
    elif normalized_type == "BUTTERFLY VALVE":
        search_x0 = float(x0) - 80.0
        search_x1 = float(x1) + 80.0
        search_top = float(bottom) + 5.0
        search_bottom = float(bottom) + 140.0
    else:
        if debug:
            print("\n--- VALVE ID DEBUG ---")
            print(f"Valve Type: {valve_type}")
            print(f"Valve BBox: {valve_bbox}")
            print("Search Region: (unsupported valve type)")
            print("Words Found: 0")
            print("Final Joined ID: ")
        return ""

    nearby_words = extract_words_in_region(words, search_x0, search_top, search_x1, search_bottom)
    sorted_words = _sort_words_reading_order(nearby_words)

    joined = " ".join(
        str(word.get("text", "")).strip()
        for word in sorted_words
        if str(word.get("text", "")).strip()
    )
    normalized_id = normalize_text(joined)

    if debug:
        print("\n--- VALVE ID DEBUG ---")
        print(f"Valve Type: {normalized_type}")
        print(f"Valve BBox: ({x0}, {top}, {x1}, {bottom})")
        print(f"Search Region: ({search_x0}, {search_top}, {search_x1}, {search_bottom})")
        print(f"Words Found: {len(sorted_words)}")

        for word in sorted_words:
            print(word)

        print(f"Final Joined ID: {normalized_id}")

    return normalized_id


def build_valve_record(
    valve_id: str,
    valve_type: str,
    drawing_number: str = "",
) -> dict[str, str]:
    return {
        "valve_id": valve_id,
        "valve_type": valve_type,
        "drawing_number": drawing_number,
    }
