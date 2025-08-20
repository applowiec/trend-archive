(async () => {
  const app = document.getElementById('app');

  async function fetchIndex() {
    const tries = [
      'data/index.json',
      'docs/data/index.json',
      'https://raw.githubusercontent.com/applowiec/trend-archive/main/data/index.json'
    ];
    let lastErr;
    for (const url of tries) {
      try {
        const res = await fetch(url, { cache: 'no-store' });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const json = await res.json();
        return { json, from: url };
      } catch (e) { lastErr = e; }
    }
    throw lastErr || new Error('Nieznany błąd pobierania');
  }

  function row(item, baseHref) {
    const file = item.file || (item.date + '.md');
    const href = baseHref + encodeURIComponent(file);
    return `
      <div class="card row">
        <div class="date">📆 ${item.date}</div>
        <div class="pill">źródło: ${item.source || 'n/a'}</div>
        <div class="pill">liczba pozycji: ${item.count ?? '—'}</div>
        <div class="actions">
          <a class="btn" href="${href}">Podgląd</a>
          <a class="btn" href="https://github.com/applowiec/trend-archive/blob/main/data/${encodeURIComponent(file)}">GitHub</a>
        </div>
      </div>`;
  }

  try {
    const { json, from } = await fetchIndex();
    const baseHref = from.includes('raw.githubusercontent.com')
      ? 'https://raw.githubusercontent.com/applowiec/trend-archive/main/data/'
      : 'data/';

    if (!Array.isArray(json) || json.length === 0) {
      app.innerHTML = '<div class="card empty">Brak danych do wyświetlenia.</div>';
      return;
    }

    const list = [...json].sort((a,b) => (b.date || '').localeCompare(a.date || ''));
    app.innerHTML = list.map(x => row(x, baseHref)).join('');

  } catch (err) {
    app.innerHTML = `<div class="err"><b>Błąd ładowania danych</b><br>${String(err)}</div>`;
    console.error(err);
  }
})();
