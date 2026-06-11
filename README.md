# FPL Report

> A self-updating Fantasy Premier League analytics report built with Python and hosted for free on GitHub Pages. Refreshes automatically every day via GitHub Actions — no manual work required after setup.

---

## What this is

This project turns raw Fantasy Premier League data into a clean, public web report that helps managers make better decisions for their personal leagues. It covers player comparisons, team form, fixture difficulty, gameweek summaries, wildcard suggestions, and mini-league tracking.

The report writes itself. A scheduled robot fetches the latest FPL data each morning, runs it through Python scripts that build the web pages, and publishes the result to the live site automatically.

**Live site:** `https://<your-github-username>.github.io/fpl-report`

---

## What the report covers

| Section | What it shows |
|---|---|
| Overview | Top-scoring players and teams; headline numbers at a glance |
| Players | Full player stats table and a head-to-head comparison tool |
| Teams | Average points per team, clean sheet rates, high-scoring player counts |
| Fixtures | Upcoming gameweeks with Fixture Difficulty Ratings (FDR) colour-coded |
| Gameweek | Summary of the last gameweek — standout performers, blanks, and short-term form |
| Wildcard | Suggested 11-player squad based on overall stats, recent form, and budget |
| League & my team | Personal team trends and mini-league position history (team ID entered in browser) |

---

## How it works

```
FPL API  →  GitHub Actions (daily schedule)  →  Python scripts  →  /docs  →  GitHub Pages  →  Public site
```

1. GitHub Actions wakes up on a schedule (configured in `.github/workflows/refresh.yml`)
2. It runs `src/fetch.py` to pull fresh data from the FPL API
3. `src/build.py` processes the data and generates HTML pages into `/docs`
4. `src/suggest.py` runs the wildcard algorithm and writes its output
5. GitHub Pages serves the updated `/docs` folder to the public URL

No server. No database. No hosting cost.

---

## Repository structure

```
fpl-report/
├── src/
│   ├── fetch.py          # Pulls data from the FPL API
│   ├── build.py          # Generates HTML pages from data
│   ├── suggest.py        # Wildcard suggestion algorithm
│   └── utils.py          # Shared helper functions
│
├── .github/
│   └── workflows/
│       ├── refresh.yml   # Scheduled daily data pipeline
│       ├── deploy.yml    # Publishes to GitHub Pages on merge to main
│       └── test.yml      # Runs tests on every pull request
│
├── docs/                 # Website output (served by GitHub Pages)
│   ├── index.html
│   ├── data/             # Cached JSON files from the FPL API
│   └── assets/           # CSS, JavaScript, images
│
├── tests/
│   ├── test_fetch.py
│   └── test_build.py
│
├── config/
│   ├── settings.json     # Non-sensitive project settings
│   └── .env.example      # Template showing required environment variables
│
└── README.md             # This file — executive summary and living documentation
```

---

## Environments and deployment pipeline

| Environment | Branch | Purpose | URL |
|---|---|---|---|
| Local dev | any feature branch | Write and test code on your machine | `localhost:8000` |
| Staging | `staging` | Preview changes before they go live | GitHub Actions preview |
| Production | `main` | Live public site | GitHub Pages URL |

**Rule:** Nothing reaches production without passing the automated test suite. If `pytest` or the linter fails, the pipeline stops and the live site is not touched.

---

## How to run locally

**Requirements:** Python 3.11+, pip

```bash
# 1. Clone the repository
git clone https://github.com/<your-username>/fpl-report.git
cd fpl-report

# 2. Install dependencies
pip install -r requirements.txt

# 3. Fetch fresh data from the FPL API
python src/fetch.py

# 4. Build the site
python src/build.py

# 5. Preview in your browser
python -m http.server 8000 --directory docs
# Then open http://localhost:8000
```

---

## How to run tests

```bash
pytest tests/
```

All tests must pass before a pull request can be merged to `main`.

---

## Scheduled refresh

The data pipeline runs automatically. The schedule is defined in `.github/workflows/refresh.yml`:

```yaml
on:
  schedule:
    - cron: '0 7 * * *'   # Every day at 07:00 UTC
```

To trigger a manual refresh, go to the Actions tab in GitHub and run the `refresh` workflow manually.

---

## Security and privacy

- **No personal data is stored.** The site uses only public FPL API data (player names, scores, fixtures). No user accounts, no cookies, no analytics.
- **Secrets are never in code.** Any sensitive values (e.g. a personal FPL team ID used for testing) are stored in GitHub Secrets and injected at runtime — never committed to the repository.
- **Personal team features are client-side only.** If a visitor enters their FPL team ID to view personal stats, that ID stays in their browser and is never sent to a server we own.
- **API usage is respectful.** We fetch data once per day and cache it. The live site serves the cached files — it never hits the FPL API in real time on page load.

---

## Tech stack

| Layer | Tool | Why |
|---|---|---|
| Language | Python 3.11 | Data processing, page generation |
| Automation | GitHub Actions | Free scheduled runs, CI/CD |
| Hosting | GitHub Pages | Free static site hosting |
| Testing | pytest | Automated quality gate |
| Local dev | VS Code + Claude Code | Development environment |
| Data source | FPL API | `fantasy.premierleague.com/api/` |

---

## Contributing

1. Create a feature branch from `main`
2. Make your changes
3. Run `pytest tests/` locally and confirm all tests pass
4. Open a pull request to `staging` for review
5. After approval, merge to `main` — deployment is automatic

---

## Changelog

| Version | Date | Summary |
|---|---|---|
| 0.1.0 | TBD | Initial infrastructure setup — repo, CI/CD, GitHub Pages |
| 0.2.0 | TBD | Data pipeline — fetch, process, cache FPL API data |
| 0.3.0 | TBD | Core pages — Overview, Players, Teams, Fixtures |
| 0.4.0 | TBD | Advanced pages — Gameweek, Wildcard, League & my team |
| 1.0.0 | TBD | Public launch |

---

*This README is the executive summary of the project. It should be updated whenever the architecture, scope, or key decisions change. Last updated: June 2026.*
