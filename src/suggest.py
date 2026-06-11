"""
suggest.py
Wildcard suggestion algorithm.
Picks the best 15-player squad (GKP×2, DEF×5, MID×5, FWD×3)
within the £100m FPL budget, based on recent form and value.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from utils import load_json, safe_float, recent_form_score, format_cost, position_label

BUDGET = 1000  # FPL stores costs as integers (£100.0m = 1000)

SQUAD_RULES = {
    1: {"min": 2, "max": 2, "label": "GKP"},  # Goalkeepers
    2: {"min": 5, "max": 5, "label": "DEF"},  # Defenders
    3: {"min": 5, "max": 5, "label": "MID"},  # Midfielders
    4: {"min": 3, "max": 3, "label": "FWD"},  # Forwards
}

MAX_PER_TEAM = 3


def score_player(player: dict) -> float:
    """
    Score a player for wildcard selection.
    Combines form score with a value-for-money multiplier.
    """
    form = recent_form_score(player)
    cost = player.get("now_cost", 100)
    value = (form / (cost / 100)) if cost > 0 else 0
    return round(form * 0.7 + value * 0.3, 3)


def suggest_squad(players: list) -> dict:
    """
    Build a suggested 15-player squad.
    Returns a dict with picks per position and total cost.
    """
    # Apply a minutes threshold; fall back to all players if pool is too small
    MIN_MINUTES = 450
    eligible = [p for p in players if safe_float(p.get("minutes", 0)) > MIN_MINUTES]

    # If any position doesn't have enough candidates, relax the filter
    for pos_type, rules in SQUAD_RULES.items():
        pos_eligible = [p for p in eligible if p["element_type"] == pos_type]
        if len(pos_eligible) < rules["min"]:
            eligible = players
            break

    scored = [
        {**p, "_score": score_player(p), "_form_score": recent_form_score(p)}
        for p in eligible
    ]
    scored.sort(key=lambda x: x["_score"], reverse=True)

    squad = []
    team_counts: dict[int, int] = {}

    for pos_type, rules in SQUAD_RULES.items():
        needed = rules["min"]
        picked = []

        for player in scored:
            if len(picked) >= needed:
                break
            if player["element_type"] != pos_type:
                continue
            team_id = player["team"]
            if team_counts.get(team_id, 0) >= MAX_PER_TEAM:
                continue
            if any(p["id"] == player["id"] for p in squad):
                continue
            picked.append(player)
            team_counts[team_id] = team_counts.get(team_id, 0) + 1

        squad.extend(picked)

    total_cost = sum(p["now_cost"] for p in squad)
    over_budget = total_cost > BUDGET

    return {
        "players": [
            {
                "id": p["id"],
                "name": p["web_name"],
                "team_id": p["team"],
                "position": position_label(p["element_type"]),
                "cost": format_cost(p["now_cost"]),
                "raw_cost": p["now_cost"],
                "total_points": p["total_points"],
                "form": p["form"],
                "points_per_game": p["points_per_game"],
                "score": p["_score"],
            }
            for p in squad
        ],
        "total_cost": format_cost(total_cost),
        "raw_total": total_cost,
        "over_budget": over_budget,
        "budget_remaining": format_cost(max(0, BUDGET - total_cost)),
    }


def run() -> dict:
    bootstrap = load_json("bootstrap-static.json")
    players = bootstrap.get("elements", [])
    teams = {t["id"]: t["name"] for t in bootstrap.get("teams", [])}

    suggestion = suggest_squad(players)

    # Enrich with team names
    for p in suggestion["players"]:
        p["team_name"] = teams.get(p["team_id"], "Unknown")

    return suggestion


if __name__ == "__main__":
    import json
    result = run()
    print(json.dumps(result, indent=2))
