"""
utils.py
Shared helper functions used by build.py and suggest.py.
"""

import json
from pathlib import Path

ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT / "docs" / "data"


def load_json(filename: str) -> dict | list:
    """Load a processed JSON file from docs/data/."""
    path = DATA_DIR / filename
    if not path.exists():
        raise FileNotFoundError(
            f"Data file not found: {path}\n"
            "Run 'python src/fetch.py' first to generate data files."
        )
    with open(path) as f:
        return json.load(f)


def fdr_label(fdr: int) -> str:
    """Return a human-readable label for a Fixture Difficulty Rating."""
    return {1: "Very Easy", 2: "Easy", 3: "Medium", 4: "Hard", 5: "Very Hard"}.get(fdr, "Unknown")


def fdr_color(fdr: int) -> str:
    """Return a CSS class name for a given FDR value."""
    return {1: "fdr-1", 2: "fdr-2", 3: "fdr-3", 4: "fdr-4", 5: "fdr-5"}.get(fdr, "fdr-3")


def position_label(element_type: int) -> str:
    """Return a short position label."""
    return {1: "GKP", 2: "DEF", 3: "MID", 4: "FWD"}.get(element_type, "???")


def format_cost(raw_cost: int) -> str:
    """Convert FPL raw cost (e.g. 142) to display format (e.g. '£14.2m')."""
    return f"£{raw_cost / 10:.1f}m"


def safe_float(value, default: float = 0.0) -> float:
    """Safely convert a value to float, returning default on failure."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def top_n(items: list, key: str, n: int = 10, reverse: bool = True) -> list:
    """Return top N items from a list sorted by a key."""
    return sorted(items, key=lambda x: safe_float(x.get(key, 0)), reverse=reverse)[:n]


def build_team_map(teams: list) -> dict:
    """Build a dict of team_id → team dict for fast lookups."""
    return {t["id"]: t for t in teams}


def recent_form_score(player: dict) -> float:
    """
    Calculate a composite form score for wildcard suggestions.
    Weights recent form (60%) and points per game (40%).
    """
    form = safe_float(player.get("form", 0))
    ppg = safe_float(player.get("points_per_game", 0))
    return round(form * 0.6 + ppg * 0.4, 2)
