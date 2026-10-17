"""
utils.py
Shared helper functions used by build.py and suggest.py.
"""

import json
from datetime import date, datetime
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


def calculate_age(birth_date: str | None, as_of: date | None = None) -> int | None:
    """Return a player's age in years from their birth_date (YYYY-MM-DD), or None if unknown."""
    if not birth_date:
        return None
    try:
        bd = datetime.strptime(birth_date, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None
    ref = as_of or date.today()
    return ref.year - bd.year - ((ref.month, ref.day) < (bd.month, bd.day))


def ordinal(n: int) -> str:
    """Return the ordinal form of an integer, e.g. 1 -> '1st', 3 -> '3rd', 12 -> '12th'."""
    if 10 <= n % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def compute_team_records(teams: list, fixtures: list) -> dict:
    """
    Compute matches played, wins, draws, losses, goals for/against per team
    from finished fixtures. The bootstrap `teams` payload's own played/win/
    draw/loss fields are unreliable (observed stuck at 0 all season), so
    fixtures are the source of truth here.
    """
    records = {
        t["id"]: {"played": 0, "win": 0, "draw": 0, "loss": 0, "gf": 0, "ga": 0}
        for t in teams
    }
    for f in fixtures:
        if not f.get("finished"):
            continue
        h, a = f.get("team_h"), f.get("team_a")
        hs, as_ = f.get("team_h_score"), f.get("team_a_score")
        if h not in records or a not in records or hs is None or as_ is None:
            continue
        records[h]["played"] += 1
        records[a]["played"] += 1
        records[h]["gf"] += hs
        records[h]["ga"] += as_
        records[a]["gf"] += as_
        records[a]["ga"] += hs
        if hs > as_:
            records[h]["win"] += 1
            records[a]["loss"] += 1
        elif hs < as_:
            records[a]["win"] += 1
            records[h]["loss"] += 1
        else:
            records[h]["draw"] += 1
            records[a]["draw"] += 1
    return records


def recent_form_score(player: dict) -> float:
    """
    Calculate a composite form score for wildcard suggestions.
    Weights recent form (60%) and points per game (40%).
    """
    form = safe_float(player.get("form", 0))
    ppg = safe_float(player.get("points_per_game", 0))
    return round(form * 0.6 + ppg * 0.4, 2)
