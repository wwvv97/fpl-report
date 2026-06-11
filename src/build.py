"""
build.py
Reads processed JSON from docs/data/ and generates the full static HTML site.
Run after fetch.py has populated docs/data/.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from utils import (
    load_json, build_team_map, top_n, fdr_label, fdr_color,
    format_cost, position_label, safe_float
)
from suggest import run as build_suggestion

ROOT = Path(__file__).parent.parent
DOCS = ROOT / "docs"
ASSETS = DOCS / "assets"


# ── HTML shell ────────────────────────────────────────────────────────────────

def html_shell(title: str, active_page: str, body: str, meta: dict) -> str:
    source_badge = (
        '<span class="badge badge-mock">Mock data</span>'
        if meta.get("source") == "mock"
        else '<span class="badge badge-live">Live data</span>'
    )
    gw = meta.get("current_gameweek", "—")
    updated = meta.get("last_updated", "")[:10]

    nav_items = [
        ("index.html",    "Overview",  "overview"),
        ("players.html",  "Players",   "players"),
        ("teams.html",    "Teams",     "teams"),
        ("fixtures.html", "Fixtures",  "fixtures"),
        ("gameweek.html", "Gameweek",  "gameweek"),
        ("wildcard.html", "Wildcard",  "wildcard"),
    ]
    nav_html = "\n".join(
        f'<a href="{href}" class="nav-link{" active" if key == active_page else ""}">{label}</a>'
        for href, label, key in nav_items
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title} — FPL Report</title>
  <link rel="stylesheet" href="assets/style.css">
</head>
<body>
  <header class="site-header">
    <div class="header-inner">
      <div class="header-brand">
        <span class="brand-logo">FPL</span>
        <span class="brand-sub">Report</span>
      </div>
      <div class="header-meta">
        {source_badge}
        <span class="meta-info">GW{gw} · {updated}</span>
      </div>
    </div>
    <nav class="site-nav">
      {nav_html}
    </nav>
  </header>
  <main class="site-main">
    {body}
  </main>
  <footer class="site-footer">
    <p>Built with Python + GitHub Actions · Data: FPL API · Hosted on GitHub Pages</p>
    <p>For personal use only. Not affiliated with the Premier League or Fantasy Premier League.</p>
  </footer>
  <script src="assets/main.js"></script>
</body>
</html>"""


# ── Page builders ─────────────────────────────────────────────────────────────

def build_overview(bootstrap: dict, meta: dict) -> str:
    players = bootstrap["elements"]
    teams = build_team_map(bootstrap["teams"])

    top_players = top_n(players, "total_points", 5)
    top_form = top_n(players, "form", 5)

    def player_row(p: dict, rank: int) -> str:
        team = teams.get(p["team"], {})
        return f"""
        <tr>
          <td class="rank">{rank}</td>
          <td class="player-name">
            <span class="name">{p['web_name']}</span>
            <span class="pos-badge pos-{p['element_type']}">{position_label(p['element_type'])}</span>
          </td>
          <td>{team.get('short_name', '—')}</td>
          <td>{format_cost(p['now_cost'])}</td>
          <td class="pts">{p['total_points']}</td>
        </tr>"""

    top_pts_rows = "".join(player_row(p, i+1) for i, p in enumerate(top_players))
    top_form_rows = "".join(player_row(p, i+1) for i, p in enumerate(top_form))

    # Team stats
    team_pts = []
    for t in bootstrap["teams"]:
        team_players = [p for p in players if p["team"] == t["id"]]
        if team_players:
            avg = sum(p["total_points"] for p in team_players) / len(team_players)
            team_pts.append({"name": t["name"], "short": t["short_name"],
                              "avg": round(avg, 1), "count": len(team_players)})
    team_pts.sort(key=lambda x: x["avg"], reverse=True)

    team_rows = "".join(f"""
        <tr>
          <td class="rank">{i+1}</td>
          <td>{t['name']}</td>
          <td>{t['avg']}</td>
          <td>{t['count']}</td>
        </tr>""" for i, t in enumerate(team_pts[:5]))

    gw_info = next((e for e in bootstrap["events"] if e.get("is_current")), {})
    prev_gw = next((e for e in bootstrap["events"] if e.get("is_previous")), {})

    body = f"""
    <div class="page-header">
      <h1>Overview</h1>
      <p class="page-desc">Season snapshot — top performers, form leaders, and team averages.</p>
    </div>

    <div class="stat-cards">
      <div class="stat-card">
        <div class="stat-label">Current gameweek</div>
        <div class="stat-value">{gw_info.get('name', '—')}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Last GW average</div>
        <div class="stat-value">{prev_gw.get('average_entry_score', '—')} pts</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Last GW highest</div>
        <div class="stat-value">{prev_gw.get('highest_score', '—')} pts</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Total players tracked</div>
        <div class="stat-value">{len(players)}</div>
      </div>
    </div>

    <div class="two-col">
      <section class="card">
        <h2>Top points scorers</h2>
        <table class="data-table">
          <thead><tr><th>#</th><th>Player</th><th>Team</th><th>Cost</th><th>Pts</th></tr></thead>
          <tbody>{top_pts_rows}</tbody>
        </table>
      </section>
      <section class="card">
        <h2>Best current form</h2>
        <table class="data-table">
          <thead><tr><th>#</th><th>Player</th><th>Team</th><th>Cost</th><th>Form</th></tr></thead>
          <tbody>{top_form_rows}</tbody>
        </table>
      </section>
    </div>

    <section class="card">
      <h2>Top teams by average player points</h2>
      <table class="data-table">
        <thead><tr><th>#</th><th>Team</th><th>Avg pts/player</th><th>Players</th></tr></thead>
        <tbody>{team_rows}</tbody>
      </table>
    </section>"""

    return html_shell("Overview", "overview", body, meta)


def build_players(bootstrap: dict, meta: dict) -> str:
    players = bootstrap["elements"]
    teams = build_team_map(bootstrap["teams"])

    rows = ""
    for p in sorted(players, key=lambda x: x["total_points"], reverse=True):
        team = teams.get(p["team"], {})
        rows += f"""
        <tr data-pos="{p['element_type']}" data-team="{p['team']}">
          <td class="player-name">
            <span class="name">{p['web_name']}</span>
            <span class="pos-badge pos-{p['element_type']}">{position_label(p['element_type'])}</span>
          </td>
          <td>{team.get('short_name', '—')}</td>
          <td>{format_cost(p['now_cost'])}</td>
          <td>{p['total_points']}</td>
          <td>{p['form']}</td>
          <td>{p['points_per_game']}</td>
          <td>{p['goals_scored']}</td>
          <td>{p['assists']}</td>
          <td>{p['clean_sheets']}</td>
          <td>{p['selected_by_percent']}%</td>
        </tr>"""

    # Player comparison options
    player_opts = "".join(
        f'<option value="{p["id"]}">{p["web_name"]} ({teams.get(p["team"], {}).get("short_name","—")}) — {format_cost(p["now_cost"])}</option>'
        for p in sorted(players, key=lambda x: x["total_points"], reverse=True)
    )

    # Embed player data for JS comparison
    player_data_js = json.dumps({
        str(p["id"]): {
            "name": p["web_name"],
            "team": teams.get(p["team"], {}).get("name", "—"),
            "position": position_label(p["element_type"]),
            "cost": format_cost(p["now_cost"]),
            "total_points": p["total_points"],
            "form": p["form"],
            "points_per_game": p["points_per_game"],
            "goals_scored": p["goals_scored"],
            "assists": p["assists"],
            "clean_sheets": p["clean_sheets"],
            "minutes": p["minutes"],
            "selected_by_percent": p["selected_by_percent"],
            "bonus": p["bonus"],
        }
        for p in players
    })

    body = f"""
    <div class="page-header">
      <h1>Players</h1>
      <p class="page-desc">Full player stats. Filter by position, sort any column, or compare two players head-to-head.</p>
    </div>

    <section class="card comparison-card">
      <h2>Player comparison</h2>
      <div class="compare-selects">
        <div class="compare-col">
          <label for="player-a">Player A</label>
          <select id="player-a">{player_opts}</select>
        </div>
        <div class="compare-vs">vs</div>
        <div class="compare-col">
          <label for="player-b">Player B</label>
          <select id="player-b">{player_opts}</select>
        </div>
      </div>
      <div id="comparison-result" class="comparison-result"></div>
    </section>

    <section class="card">
      <div class="table-controls">
        <h2>All players</h2>
        <div class="filter-group">
          <button class="filter-btn active" data-filter="0">All</button>
          <button class="filter-btn" data-filter="1">GKP</button>
          <button class="filter-btn" data-filter="2">DEF</button>
          <button class="filter-btn" data-filter="3">MID</button>
          <button class="filter-btn" data-filter="4">FWD</button>
        </div>
      </div>
      <div class="table-wrap">
        <table class="data-table sortable" id="players-table">
          <thead>
            <tr>
              <th>Player</th><th>Team</th><th>Cost</th><th>Pts</th>
              <th>Form</th><th>PPG</th><th>G</th><th>A</th><th>CS</th><th>Sel%</th>
            </tr>
          </thead>
          <tbody>{rows}</tbody>
        </table>
      </div>
    </section>

    <script>
    const PLAYERS = {player_data_js};
    </script>"""

    return html_shell("Players", "players", body, meta)


def build_teams(bootstrap: dict, meta: dict) -> str:
    players = bootstrap["elements"]
    team_map = build_team_map(bootstrap["teams"])

    stats = []
    for t in bootstrap["teams"]:
        tp = [p for p in players if p["team"] == t["id"]]
        if not tp:
            continue
        avg_pts = sum(p["total_points"] for p in tp) / len(tp)
        high_scorers = sum(1 for p in tp if p["total_points"] >= 150)
        blank_risk = sum(1 for p in tp if safe_float(p.get("form", 0)) < 3.0)
        stats.append({
            "id": t["id"],
            "name": t["name"],
            "short": t["short_name"],
            "strength": t["strength"],
            "avg_pts": round(avg_pts, 1),
            "high_scorers": high_scorers,
            "blank_risk": blank_risk,
            "player_count": len(tp),
        })
    stats.sort(key=lambda x: x["avg_pts"], reverse=True)

    rows = "".join(f"""
      <tr>
        <td class="rank">{i+1}</td>
        <td><strong>{s['name']}</strong></td>
        <td>{'★' * s['strength']}</td>
        <td>{s['avg_pts']}</td>
        <td>{s['high_scorers']}</td>
        <td>{s['player_count']}</td>
      </tr>""" for i, s in enumerate(stats))

    body = f"""
    <div class="page-header">
      <h1>Teams</h1>
      <p class="page-desc">Team-level stats — average player points, high scorers, and squad depth.</p>
    </div>
    <section class="card">
      <h2>All teams ranked by average player points</h2>
      <table class="data-table">
        <thead>
          <tr>
            <th>#</th><th>Team</th><th>Strength</th>
            <th>Avg pts/player</th><th>High scorers (150+ pts)</th><th>Squad size</th>
          </tr>
        </thead>
        <tbody>{rows}</tbody>
      </table>
    </section>"""

    return html_shell("Teams", "teams", body, meta)


def build_fixtures(bootstrap: dict, fixtures: list, meta: dict) -> str:
    team_map = build_team_map(bootstrap["teams"])
    events = {e["id"]: e["name"] for e in bootstrap["events"]}
    current_gw = meta.get("current_gameweek") or next(
        (e["id"] for e in bootstrap["events"] if e.get("is_current")), 37
    )

    # Group fixtures by gameweek
    gws = {}
    for f in fixtures:
        gw = f["event"]
        gws.setdefault(gw, []).append(f)

    sections = ""
    for gw_id in sorted(gws.keys()):
        gw_fixtures = gws[gw_id]
        gw_name = events.get(gw_id, f"Gameweek {gw_id}")
        is_current = gw_id == current_gw
        label = f' <span class="badge badge-current">current</span>' if is_current else ""

        rows = ""
        for f in gw_fixtures:
            h = team_map.get(f["team_h"], {})
            a = team_map.get(f["team_a"], {})
            h_fdr = f.get("team_h_difficulty", 3)
            a_fdr = f.get("team_a_difficulty", 3)
            score = f"{f['team_h_score']}–{f['team_a_score']}" if f.get("finished") else "vs"
            date = f.get("kickoff_time", "")[:10]
            rows += f"""
            <tr>
              <td>
                <span class="team-name">{h.get('name','?')}</span>
                <span class="fdr-pill {fdr_color(h_fdr)}">{h_fdr}</span>
              </td>
              <td class="score-cell">{score}</td>
              <td>
                <span class="fdr-pill {fdr_color(a_fdr)}">{a_fdr}</span>
                <span class="team-name">{a.get('name','?')}</span>
              </td>
              <td class="fixture-date">{date}</td>
            </tr>"""

        sections += f"""
        <section class="card fixture-gw{"  fixture-gw--current" if is_current else ""}">
          <h2>{gw_name}{label}</h2>
          <table class="data-table fixtures-table">
            <thead><tr><th>Home</th><th>Score</th><th>Away</th><th>Date</th></tr></thead>
            <tbody>{rows}</tbody>
          </table>
        </section>"""

    fdr_legend = "".join(
        f'<span class="fdr-pill {fdr_color(i)}">{i} — {fdr_label(i)}</span>'
        for i in range(1, 6)
    )

    body = f"""
    <div class="page-header">
      <h1>Fixtures</h1>
      <p class="page-desc">Upcoming and recent fixtures with Fixture Difficulty Ratings (FDR). Lower FDR = easier match.</p>
    </div>
    <div class="fdr-legend card">{fdr_legend}</div>
    {sections}"""

    return html_shell("Fixtures", "fixtures", body, meta)


def build_gameweek(bootstrap: dict, meta: dict) -> str:
    players = bootstrap["elements"]
    teams = build_team_map(bootstrap["teams"])
    prev_gw = next((e for e in bootstrap["events"] if e.get("is_previous")), {})

    standouts = [p for p in players if p.get("event_points", 0) >= 10]
    standouts.sort(key=lambda x: x.get("event_points", 0), reverse=True)

    blanks = [p for p in players
              if safe_float(p.get("points_per_game", 0)) >= 6.0
              and p.get("event_points", 0) <= 2]

    def gw_row(p: dict) -> str:
        team = teams.get(p["team"], {})
        return f"""
        <tr>
          <td class="player-name">
            <span class="name">{p['web_name']}</span>
            <span class="pos-badge pos-{p['element_type']}">{position_label(p['element_type'])}</span>
          </td>
          <td>{team.get('short_name','—')}</td>
          <td class="pts">{p.get('event_points', 0)}</td>
          <td>{p['form']}</td>
          <td>{p['points_per_game']}</td>
        </tr>"""

    standout_rows = "".join(gw_row(p) for p in standouts[:8])
    blank_rows = "".join(gw_row(p) for p in blanks[:8])

    body = f"""
    <div class="page-header">
      <h1>Gameweek summary</h1>
      <p class="page-desc">What happened in {prev_gw.get('name','the last gameweek')} — standout performers, blanking differentials, and short-term momentum.</p>
    </div>

    <div class="stat-cards">
      <div class="stat-card">
        <div class="stat-label">Average score</div>
        <div class="stat-value">{prev_gw.get('average_entry_score','—')} pts</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Highest score</div>
        <div class="stat-value">{prev_gw.get('highest_score','—')} pts</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Standout players (10+ pts)</div>
        <div class="stat-value">{len(standouts)}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Differentials that blanked</div>
        <div class="stat-value">{len(blanks)}</div>
      </div>
    </div>

    <div class="two-col">
      <section class="card">
        <h2>Standout performers (10+ pts)</h2>
        <table class="data-table">
          <thead><tr><th>Player</th><th>Team</th><th>GW pts</th><th>Form</th><th>PPG</th></tr></thead>
          <tbody>{standout_rows if standout_rows else '<tr><td colspan="5" class="empty">No standout scores this gameweek</td></tr>'}</tbody>
        </table>
      </section>
      <section class="card">
        <h2>Good form players who blanked (≤2 pts)</h2>
        <table class="data-table">
          <thead><tr><th>Player</th><th>Team</th><th>GW pts</th><th>Form</th><th>PPG</th></tr></thead>
          <tbody>{blank_rows if blank_rows else '<tr><td colspan="5" class="empty">No notable blanks this gameweek</td></tr>'}</tbody>
        </table>
      </section>
    </div>"""

    return html_shell("Gameweek", "gameweek", body, meta)


def build_wildcard(bootstrap: dict, meta: dict) -> str:
    suggestion = build_suggestion()
    by_pos = {"GKP": [], "DEF": [], "MID": [], "FWD": []}
    for p in suggestion["players"]:
        by_pos[p["position"]].append(p)

    pos_num = {"GKP": 1, "DEF": 2, "MID": 3, "FWD": 4}

    def squad_rows(pos: str) -> str:
        pn = pos_num[pos]
        return "".join(f"""
        <tr>
          <td class="player-name">
            <span class="name">{p['name']}</span>
            <span class="pos-badge pos-{pn}">{pos}</span>
          </td>
          <td>{p['team_name']}</td>
          <td>{p['cost']}</td>
          <td>{p['total_points']}</td>
          <td>{p['form']}</td>
          <td>{p['points_per_game']}</td>
          <td>{p['score']:.2f}</td>
        </tr>""" for p in by_pos[pos])

    all_rows = "".join(squad_rows(pos) for pos in ["GKP", "DEF", "MID", "FWD"])
    budget_class = "over-budget" if suggestion["over_budget"] else "in-budget"

    body = f"""
    <div class="page-header">
      <h1>Wildcard suggestion</h1>
      <p class="page-desc">A suggested 15-player squad built on season-long points, recent form, and value for money. Use as a starting point, not gospel.</p>
    </div>

    <div class="stat-cards">
      <div class="stat-card">
        <div class="stat-label">Total cost</div>
        <div class="stat-value {budget_class}">{suggestion['total_cost']}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Budget remaining</div>
        <div class="stat-value">{suggestion['budget_remaining']}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Budget</div>
        <div class="stat-value">£100.0m</div>
      </div>
    </div>

    <section class="card">
      <h2>Suggested squad</h2>
      <p class="card-desc">Score = weighted form (60%) + value-for-money (40%). Only players with 450+ minutes considered.</p>
      <table class="data-table">
        <thead>
          <tr><th>Player</th><th>Team</th><th>Cost</th><th>Total pts</th><th>Form</th><th>PPG</th><th>Score</th></tr>
        </thead>
        <tbody>{all_rows}</tbody>
      </table>
    </section>"""

    return html_shell("Wildcard", "wildcard", body, meta)


# ── CSS + JS ──────────────────────────────────────────────────────────────────

CSS = """
:root {
  --pitch: #2d7a3a;
  --pitch-light: #38964a;
  --ink: #1a1a2e;
  --ink-muted: #4a4a6a;
  --ink-faint: #8888aa;
  --surface: #ffffff;
  --surface-alt: #f7f7fb;
  --border: #e2e2ee;
  --accent: #37003c;
  --accent-bright: #00ff85;
  --fdr1: #00cc44; --fdr1-text: #003311;
  --fdr2: #88dd44; --fdr2-text: #1a3300;
  --fdr3: #ffcc00; --fdr3-text: #332200;
  --fdr4: #ff6644; --fdr4-text: #330000;
  --fdr5: #cc0000; --fdr5-text: #fff;
  --pos1: #f8c12b; --pos2: #00c853; --pos3: #29b6f6; --pos4: #ef5350;
  --radius: 8px; --radius-lg: 14px;
  --shadow: 0 1px 4px rgba(26,26,46,0.08);
}

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

body {
  font-family: 'Inter', system-ui, -apple-system, sans-serif;
  font-size: 15px; line-height: 1.6;
  background: var(--surface-alt); color: var(--ink);
  min-height: 100vh;
}

/* Header */
.site-header {
  background: var(--accent);
  color: white;
  position: sticky; top: 0; z-index: 100;
}
.header-inner {
  display: flex; align-items: center; justify-content: space-between;
  padding: 12px 24px;
}
.header-brand { display: flex; align-items: baseline; gap: 6px; }
.brand-logo {
  font-size: 22px; font-weight: 800; letter-spacing: -0.5px;
  color: var(--accent-bright);
}
.brand-sub { font-size: 14px; color: rgba(255,255,255,0.6); }
.header-meta { display: flex; align-items: center; gap: 10px; font-size: 12px; }
.meta-info { color: rgba(255,255,255,0.5); }

/* Nav */
.site-nav {
  display: flex; gap: 2px;
  padding: 0 16px;
  border-top: 1px solid rgba(255,255,255,0.1);
  overflow-x: auto;
}
.nav-link {
  display: inline-block; padding: 10px 14px;
  font-size: 13px; font-weight: 500; color: rgba(255,255,255,0.65);
  text-decoration: none; white-space: nowrap;
  border-bottom: 2px solid transparent;
  transition: color 0.15s, border-color 0.15s;
}
.nav-link:hover { color: white; }
.nav-link.active { color: var(--accent-bright); border-bottom-color: var(--accent-bright); }

/* Main */
.site-main { max-width: 1100px; margin: 0 auto; padding: 28px 20px 60px; }
.page-header { margin-bottom: 24px; }
.page-header h1 { font-size: 26px; font-weight: 700; color: var(--ink); }
.page-header .page-desc { color: var(--ink-muted); margin-top: 4px; font-size: 14px; }

/* Cards */
.card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 20px 22px;
  margin-bottom: 20px;
  box-shadow: var(--shadow);
}
.card h2 { font-size: 16px; font-weight: 600; margin-bottom: 14px; color: var(--ink); }
.card-desc { font-size: 13px; color: var(--ink-muted); margin-bottom: 12px; margin-top: -8px; }

/* Stat cards */
.stat-cards {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 14px;
  margin-bottom: 20px;
}
.stat-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 16px 18px;
  box-shadow: var(--shadow);
}
.stat-label { font-size: 12px; color: var(--ink-faint); text-transform: uppercase; letter-spacing: 0.04em; margin-bottom: 6px; }
.stat-value { font-size: 24px; font-weight: 700; color: var(--ink); }

/* Tables */
.table-wrap { overflow-x: auto; }
.data-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.data-table th {
  text-align: left; padding: 8px 10px;
  font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.04em;
  color: var(--ink-faint); border-bottom: 1px solid var(--border);
}
.data-table td { padding: 9px 10px; border-bottom: 1px solid var(--border); }
.data-table tr:last-child td { border-bottom: none; }
.data-table tr:hover td { background: var(--surface-alt); }
.data-table .rank { color: var(--ink-faint); font-size: 12px; width: 28px; }
.data-table .pts { font-weight: 600; }
.empty { text-align: center; color: var(--ink-faint); padding: 20px; }

/* Badges */
.badge { display: inline-block; font-size: 11px; font-weight: 600; padding: 2px 8px; border-radius: 999px; }
.badge-mock { background: #fff3e0; color: #e65100; }
.badge-live { background: #e8f5e9; color: #2e7d32; }
.badge-current { background: var(--accent-bright); color: var(--accent); font-size: 10px; vertical-align: middle; }

/* Position badges */
.pos-badge { display: inline-block; font-size: 10px; font-weight: 700; padding: 1px 5px; border-radius: 4px; margin-left: 5px; vertical-align: middle; }
.pos-1 { background: var(--pos1); color: #332200; }
.pos-2 { background: var(--pos2); color: #003311; }
.pos-3 { background: var(--pos3); color: #003366; }
.pos-4 { background: var(--pos4); color: white; }

/* FDR pills */
.fdr-pill { display: inline-block; font-size: 11px; font-weight: 700; padding: 2px 7px; border-radius: 6px; margin: 1px; }
.fdr-1 { background: var(--fdr1); color: var(--fdr1-text); }
.fdr-2 { background: var(--fdr2); color: var(--fdr2-text); }
.fdr-3 { background: var(--fdr3); color: var(--fdr3-text); }
.fdr-4 { background: var(--fdr4); color: var(--fdr4-text); }
.fdr-5 { background: var(--fdr5); color: var(--fdr5-text); }
.fdr-legend { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; padding: 14px 18px; margin-bottom: 20px; }

/* Fixtures */
.fixtures-table .score-cell { text-align: center; font-weight: 700; color: var(--ink); }
.fixtures-table .team-name { font-weight: 500; }
.fixtures-table .fixture-date { font-size: 12px; color: var(--ink-faint); }
.fixture-gw--current { border-color: var(--accent); }

/* Two-col layout */
.two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
@media (max-width: 700px) { .two-col { grid-template-columns: 1fr; } }

/* Table controls */
.table-controls { display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px; flex-wrap: wrap; gap: 10px; }
.table-controls h2 { margin-bottom: 0; }
.filter-group { display: flex; gap: 6px; }
.filter-btn {
  font-size: 12px; font-weight: 600; padding: 4px 12px;
  border: 1px solid var(--border); border-radius: 999px;
  background: var(--surface); color: var(--ink-muted); cursor: pointer;
  transition: all 0.15s;
}
.filter-btn.active, .filter-btn:hover { background: var(--accent); color: white; border-color: var(--accent); }

/* Player comparison */
.comparison-card { }
.compare-selects { display: grid; grid-template-columns: 1fr auto 1fr; align-items: end; gap: 14px; margin-bottom: 16px; }
.compare-selects label { font-size: 12px; color: var(--ink-faint); display: block; margin-bottom: 4px; }
.compare-selects select { width: 100%; padding: 8px 10px; border: 1px solid var(--border); border-radius: var(--radius); font-size: 13px; background: var(--surface); }
.compare-vs { font-weight: 700; color: var(--ink-faint); padding-bottom: 8px; text-align: center; }
.comparison-result { display: none; }
.comparison-result.visible { display: block; }
.compare-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.compare-table th { padding: 8px 12px; text-align: center; font-size: 12px; font-weight: 600; color: var(--ink-faint); border-bottom: 1px solid var(--border); }
.compare-table th:first-child { text-align: left; }
.compare-table td { padding: 9px 12px; text-align: center; border-bottom: 1px solid var(--border); }
.compare-table td:first-child { text-align: left; color: var(--ink-muted); font-size: 12px; }
.compare-table .winner { font-weight: 700; color: var(--pitch); }
.compare-table .header-a, .compare-table .header-b { font-weight: 700; font-size: 14px; color: var(--ink); }

/* Wildcard */
.in-budget { color: #2e7d32; }
.over-budget { color: #c62828; }

/* Footer */
.site-footer { text-align: center; padding: 24px; font-size: 12px; color: var(--ink-faint); border-top: 1px solid var(--border); background: var(--surface); }
.site-footer p + p { margin-top: 4px; }
"""

JS = """
// ── Position filter ──────────────────────────────────────────────────────────
document.querySelectorAll('.filter-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    const pos = btn.dataset.filter;
    document.querySelectorAll('#players-table tbody tr').forEach(row => {
      row.style.display = (pos === '0' || row.dataset.pos === pos) ? '' : 'none';
    });
  });
});

// ── Sortable tables ───────────────────────────────────────────────────────────
document.querySelectorAll('th').forEach((th, i) => {
  th.style.cursor = 'pointer';
  th.addEventListener('click', () => {
    const table = th.closest('table');
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    const asc = th.dataset.sort !== 'asc';
    th.dataset.sort = asc ? 'asc' : 'desc';
    rows.sort((a, b) => {
      const av = a.querySelectorAll('td')[i]?.textContent.replace(/[^0-9.-]/g,'') || '';
      const bv = b.querySelectorAll('td')[i]?.textContent.replace(/[^0-9.-]/g,'') || '';
      const an = parseFloat(av), bn = parseFloat(bv);
      if (!isNaN(an) && !isNaN(bn)) return asc ? an - bn : bn - an;
      return asc ? av.localeCompare(bv) : bv.localeCompare(av);
    });
    rows.forEach(r => tbody.appendChild(r));
  });
});

// ── Player comparison ─────────────────────────────────────────────────────────
const selA = document.getElementById('player-a');
const selB = document.getElementById('player-b');
const resultEl = document.getElementById('comparison-result');

function compare() {
  if (!selA || !selB || typeof PLAYERS === 'undefined') return;
  const a = PLAYERS[selA.value];
  const b = PLAYERS[selB.value];
  if (!a || !b) return;

  const metrics = [
    ['Total points', 'total_points', true],
    ['Form', 'form', true],
    ['Points per game', 'points_per_game', true],
    ['Goals', 'goals_scored', true],
    ['Assists', 'assists', true],
    ['Clean sheets', 'clean_sheets', true],
    ['Minutes played', 'minutes', true],
    ['Bonus points', 'bonus', true],
    ['Selected by', 'selected_by_percent', true],
    ['Cost', 'cost', false],
  ];

  const rows = metrics.map(([label, key, higherIsBetter]) => {
    const av = parseFloat(a[key]) || 0;
    const bv = parseFloat(b[key]) || 0;
    const aWins = higherIsBetter ? av > bv : av < bv;
    const bWins = higherIsBetter ? bv > av : bv < av;
    return `<tr>
      <td>${label}</td>
      <td class="${aWins ? 'winner' : ''}">${a[key]}</td>
      <td class="${bWins ? 'winner' : ''}">${b[key]}</td>
    </tr>`;
  }).join('');

  resultEl.innerHTML = `
    <table class="compare-table">
      <thead><tr>
        <th>Metric</th>
        <th class="header-a">${a.name}<br><small>${a.team} · ${a.position} · ${a.cost}</small></th>
        <th class="header-b">${b.name}<br><small>${b.team} · ${b.position} · ${b.cost}</small></th>
      </tr></thead>
      <tbody>${rows}</tbody>
    </table>`;
  resultEl.classList.add('visible');
}

if (selA && selB) {
  // Default second player to something different
  if (selB.options.length > 1) selB.selectedIndex = 1;
  selA.addEventListener('change', compare);
  selB.addEventListener('change', compare);
  compare();
}
"""


# ── Write assets ──────────────────────────────────────────────────────────────

def write_assets() -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    (ASSETS / "style.css").write_text(CSS)
    (ASSETS / "main.js").write_text(JS)
    print("  saved → docs/assets/style.css")
    print("  saved → docs/assets/main.js")


# ── Main ──────────────────────────────────────────────────────────────────────

def run() -> None:
    print("Loading data...")
    bootstrap = load_json("bootstrap-static.json")
    fixtures = load_json("fixtures.json")
    meta = load_json("meta.json")

    print("Writing assets...")
    write_assets()

    pages = [
        ("index.html",    build_overview(bootstrap, meta)),
        ("players.html",  build_players(bootstrap, meta)),
        ("teams.html",    build_teams(bootstrap, meta)),
        ("fixtures.html", build_fixtures(bootstrap, fixtures, meta)),
        ("gameweek.html", build_gameweek(bootstrap, meta)),
        ("wildcard.html", build_wildcard(bootstrap, meta)),
    ]

    print("Building pages...")
    for filename, html in pages:
        path = DOCS / filename
        path.write_text(html)
        print(f"  saved → docs/{filename}")

    print(f"\nSite built. {len(pages)} pages written to docs/")


if __name__ == "__main__":
    run()
