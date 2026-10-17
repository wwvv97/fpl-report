
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

// ── Team view ─────────────────────────────────────────────────────────────────
const teamSelect = document.getElementById('team-select');

function renderTeam(teamId) {
  if (typeof TEAMS === 'undefined') return;
  const t = TEAMS[teamId];
  if (!t) return;

  const statsEl = document.getElementById('team-stats');
  statsEl.innerHTML = `
    <div class="stat-card"><div class="stat-label">${t.name}</div><div class="stat-value">${t.played} played</div></div>
    <div class="stat-card"><div class="stat-label">Wins</div><div class="stat-value">${t.win}</div></div>
    <div class="stat-card"><div class="stat-label">Draws</div><div class="stat-value">${t.draw}</div></div>
    <div class="stat-card"><div class="stat-label">Losses</div><div class="stat-value">${t.loss}</div></div>
    <div class="stat-card">
      <div class="stat-label">Goals scored</div>
      <div class="stat-value">${t.gf}</div>
      <div class="stat-sub">${t.gf_rank} of ${t.team_count}</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">Goals conceded</div>
      <div class="stat-value">${t.ga}</div>
      <div class="stat-sub">${t.ga_rank} of ${t.team_count}</div>
    </div>`;

  const heading = document.getElementById('team-roster-heading');
  if (heading) heading.textContent = `${t.name} squad (sorted by minutes played)`;

  const body = document.getElementById('team-roster-body');
  body.innerHTML = t.roster.map(p => `
    <tr>
      <td class="player-name">
        <span class="name">${p.name}</span>
        <span class="pos-badge pos-${p.pos_num}">${p.position}</span>
      </td>
      <td>${p.age ?? '—'}</td>
      <td>${p.minutes}</td>
      <td>${p.starts}</td>
      <td>${p.goals}</td>
      <td>${p.assists}</td>
      <td>${p.clean_sheets}</td>
      <td>${p.yellow_cards}</td>
      <td>${p.red_cards}</td>
      <td>${p.xg}</td>
      <td>${p.xa}</td>
      <td>${p.ict_index}</td>
      <td>${p.bonus}</td>
    </tr>`).join('');
}

if (teamSelect) {
  teamSelect.addEventListener('change', () => renderTeam(teamSelect.value));
  renderTeam(typeof DEFAULT_TEAM !== 'undefined' ? DEFAULT_TEAM : teamSelect.value);
}
