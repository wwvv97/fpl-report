
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
