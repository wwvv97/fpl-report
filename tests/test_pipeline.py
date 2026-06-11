"""
Tests for the FPL Report pipeline.
Run with: pytest tests/
"""

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "src"))


# ── Fixtures (pytest) ─────────────────────────────────────────────────────────

@pytest.fixture
def mock_bootstrap():
    path = ROOT / "mock" / "bootstrap-static.json"
    with open(path) as f:
        return json.load(f)


@pytest.fixture
def mock_fixtures():
    path = ROOT / "mock" / "fixtures.json"
    with open(path) as f:
        return json.load(f)


# ── fetch.py tests ────────────────────────────────────────────────────────────

class TestFetch:
    def test_mock_bootstrap_loads(self, mock_bootstrap):
        assert "elements" in mock_bootstrap
        assert "teams" in mock_bootstrap
        assert "events" in mock_bootstrap
        assert len(mock_bootstrap["elements"]) > 0

    def test_mock_has_required_player_fields(self, mock_bootstrap):
        required = ["id", "web_name", "team", "element_type", "now_cost",
                    "total_points", "form", "points_per_game", "minutes"]
        for player in mock_bootstrap["elements"]:
            for field in required:
                assert field in player, f"Player {player.get('web_name')} missing field: {field}"

    def test_mock_teams_count(self, mock_bootstrap):
        assert len(mock_bootstrap["teams"]) == 20

    def test_mock_events_has_current(self, mock_bootstrap):
        current = [e for e in mock_bootstrap["events"] if e.get("is_current")]
        assert len(current) == 1, "Expected exactly one current gameweek"

    def test_mock_fixtures_load(self, mock_fixtures):
        assert isinstance(mock_fixtures, list)
        assert len(mock_fixtures) > 0

    def test_fixtures_have_required_fields(self, mock_fixtures):
        required = ["id", "event", "team_h", "team_a", "finished"]
        for f in mock_fixtures:
            for field in required:
                assert field in f, f"Fixture {f.get('id')} missing field: {field}"


# ── utils.py tests ────────────────────────────────────────────────────────────

class TestUtils:
    def test_fdr_label(self):
        from utils import fdr_label
        assert fdr_label(1) == "Very Easy"
        assert fdr_label(5) == "Very Hard"
        assert fdr_label(3) == "Medium"

    def test_format_cost(self):
        from utils import format_cost
        assert format_cost(142) == "£14.2m"
        assert format_cost(55) == "£5.5m"
        assert format_cost(100) == "£10.0m"

    def test_position_label(self):
        from utils import position_label
        assert position_label(1) == "GKP"
        assert position_label(2) == "DEF"
        assert position_label(3) == "MID"
        assert position_label(4) == "FWD"

    def test_safe_float(self):
        from utils import safe_float
        assert safe_float("6.2") == 6.2
        assert safe_float(None) == 0.0
        assert safe_float("bad") == 0.0
        assert safe_float(10) == 10.0

    def test_top_n(self):
        from utils import top_n
        items = [{"pts": i} for i in range(20)]
        result = top_n(items, "pts", 5)
        assert len(result) == 5
        assert result[0]["pts"] == 19

    def test_build_team_map(self, mock_bootstrap):
        from utils import build_team_map
        team_map = build_team_map(mock_bootstrap["teams"])
        assert isinstance(team_map, dict)
        assert 1 in team_map
        assert team_map[1]["name"] == "Arsenal"


# ── suggest.py tests ──────────────────────────────────────────────────────────

class TestSuggest:
    def test_squad_has_15_players(self, mock_bootstrap):
        from suggest import suggest_squad
        players = mock_bootstrap["elements"]
        result = suggest_squad(players)
        assert len(result["players"]) == 15

    def test_squad_position_counts(self, mock_bootstrap):
        from suggest import suggest_squad
        players = mock_bootstrap["elements"]
        result = suggest_squad(players)
        counts = {}
        for p in result["players"]:
            counts[p["position"]] = counts.get(p["position"], 0) + 1
        assert counts.get("GKP", 0) == 2
        assert counts.get("DEF", 0) == 5
        assert counts.get("MID", 0) == 5
        assert counts.get("FWD", 0) == 3

    def test_squad_max_3_per_team(self, mock_bootstrap):
        from suggest import suggest_squad
        players = mock_bootstrap["elements"]
        result = suggest_squad(players)
        team_counts: dict = {}
        for p in result["players"]:
            team_counts[p["team_id"]] = team_counts.get(p["team_id"], 0) + 1
        for team, count in team_counts.items():
            assert count <= 3, f"Team {team} has {count} players — exceeds limit of 3"

    def test_squad_cost_format(self, mock_bootstrap):
        from suggest import suggest_squad
        players = mock_bootstrap["elements"]
        result = suggest_squad(players)
        assert result["total_cost"].startswith("£")
        assert result["budget_remaining"].startswith("£")
