"""
fetch.py
Pulls data from the FPL API and saves it to docs/data/.
Falls back to mock data automatically when the API is unavailable.
"""

import json
import os
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

# ── Paths ────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent.parent
MOCK_DIR = ROOT / "mock"
DATA_DIR = ROOT / "docs" / "data"

# ── API config ────────────────────────────────────────────────────────────────
BASE_URL = "https://fantasy.premierleague.com/api"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
}
TIMEOUT = 15  # seconds


def _fetch_url(url: str) -> dict | list:
    """Make a single HTTP GET request and return parsed JSON."""
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _load_mock(filename: str) -> dict | list:
    """Load a mock JSON file from the mock/ directory."""
    path = MOCK_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Mock file not found: {path}")
    with open(path) as f:
        return json.load(f)


def _save(filename: str, data: dict | list) -> None:
    """Save data as JSON to docs/data/."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    path = DATA_DIR / filename
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    print(f"  saved → docs/data/{filename}")


# ── Public fetch functions ────────────────────────────────────────────────────

def fetch_bootstrap(use_mock: bool = False) -> dict:
    """
    Fetch the main bootstrap-static endpoint.
    Contains players, teams, gameweeks, and element types.
    """
    if use_mock:
        print("  [mock] bootstrap-static.json")
        return _load_mock("bootstrap-static.json")
    return _fetch_url(f"{BASE_URL}/bootstrap-static/")


def fetch_fixtures(use_mock: bool = False) -> list:
    """Fetch all fixtures for the season."""
    if use_mock:
        print("  [mock] fixtures.json")
        return _load_mock("fixtures.json")
    return _fetch_url(f"{BASE_URL}/fixtures/")


def _api_is_available() -> bool:
    """Quick probe to check if the FPL API is reachable."""
    try:
        _fetch_url(f"{BASE_URL}/bootstrap-static/")
        return True
    except Exception:
        return False


# ── Main pipeline ─────────────────────────────────────────────────────────────

def run(force_mock: bool = False) -> None:
    """
    Main entry point.
    Automatically uses mock data if the API is unreachable,
    or if force_mock=True is passed.
    """
    use_mock = force_mock

    if not force_mock:
        print("Checking FPL API availability...")
        if _api_is_available():
            print("  API is available — using live data")
        else:
            print("  API unavailable — falling back to mock data")
            use_mock = True

    print("\nFetching bootstrap data...")
    bootstrap = fetch_bootstrap(use_mock)
    _save("bootstrap-static.json", bootstrap)

    print("Fetching fixtures...")
    fixtures = fetch_fixtures(use_mock)
    _save("fixtures.json", fixtures)

    # Write a small metadata file so the site knows when data was last refreshed
    meta = {
        "last_updated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "source": "mock" if use_mock else "live",
        "current_gameweek": next(
            (e["id"] for e in bootstrap.get("events", []) if e.get("is_current")),
            None
        ),
        "next_gameweek": next(
            (e["id"] for e in bootstrap.get("events", []) if e.get("is_next")),
            None
        ),
    }
    _save("meta.json", meta)
    print(f"\nDone. Source: {'mock' if use_mock else 'live'}")
    print(f"Current GW: {meta['current_gameweek']} | Next GW: {meta['next_gameweek']}")


if __name__ == "__main__":
    force_mock = "--mock" in sys.argv
    run(force_mock=force_mock)
