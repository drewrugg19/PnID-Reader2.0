from __future__ import annotations

SECTION_NAMES = [
    "FIXTURE SYMBOLS",
    "PIPING ELEMENTS",
    "VALVE SYMBOLS",
]

SECTION_CONFIG = {
    "FIXTURE SYMBOLS": {
        "anchor_padding": {"left": 350.0, "right": 450.0, "top": 120.0, "bottom": 900.0},
        "word_padding": {"left": 450.0, "right": 550.0, "top": 10.0, "bottom": 900.0},
        "fallback_width": 320.0,
        "bottom_padding": 12.0,
        "fallback_bottom": 200.0,
    },
    "PIPING ELEMENTS": {
        "anchor_padding": {"left": 380.0, "right": 500.0, "top": 140.0, "bottom": 950.0},
        "word_padding": {"left": 500.0, "right": 600.0, "top": 10.0, "bottom": 950.0},
        "fallback_width": 340.0,
        "bottom_padding": 12.0,
        "fallback_bottom": 220.0,
    },
    "VALVE SYMBOLS": {
        "anchor_padding": {"left": 380.0, "right": 500.0, "top": 140.0, "bottom": 950.0},
        "word_padding": {"left": 500.0, "right": 600.0, "top": 10.0, "bottom": 950.0},
        "fallback_width": 340.0,
        "bottom_padding": 12.0,
        "fallback_bottom": 220.0,
    },
}

DEFAULT_SECTION_SETTINGS = {
    "anchor_padding": {"left": 350.0, "right": 450.0, "top": 120.0, "bottom": 900.0},
    "word_padding": {"left": 450.0, "right": 550.0, "top": 10.0, "bottom": 900.0},
    "fallback_width": 320.0,
    "bottom_padding": 12.0,
    "fallback_bottom": 200.0,
}


def get_section_settings(section_name: str) -> dict:
    return SECTION_CONFIG.get(section_name.upper(), DEFAULT_SECTION_SETTINGS)


def normalize_section_name(section_name: str) -> str:
    return "_".join(section_name.strip().lower().split())
