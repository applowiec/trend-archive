(async () => {
  // Baza dla GitHub Pages: /<user>.github.io/<repo>/
  const BASE = `${location.origin}${location.pathname.replace(/\/$/, '')}`;
  const dataURL = `${BASE}/data/index.json`;

  const ul = document.getElementById('days');
  const status = document.getElementById('status');

  try {
    const res = await fetch(dataURL, { cache: 'no-store' });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const days = await res.json();

    if (!Array.isArray(days) || days.length === 0) {
      status.textContent = 'Brak danych do wyświetlenia.';
      return;
    }

    // najnowsze na górze
    days.sort((a, b) => (a.date < b.date ? 1 : -1));

    for (const d of days) {
      const li = document.createElement('li');
      const a = document.createElement('a');
      a.href = `${BASE}/data/${encodeURIComponent(d.file)}`;
      a.textContent = `${d.date} — ${d.count} trendów`;
      li.appendChild(a);
      ul.appendChild(li);
    }

    status.textContent = '';
  } catch (e) {
    status.textContent = `Nie udało się wczytać danych: ${e.message}`;
    // podpowiedź debugowa
    console.error('Fetch failed', { tried: dataURL, error: e });
  }
})();
