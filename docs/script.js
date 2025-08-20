(async () => {
  // Wyznacz bezpieczną bazę dla Projekt Pages: /<user>.github.io/<repo>/
  // Działa lokalnie i na Pages.
  const basePath = (function () {
    const p = location.pathname;
    // upewnij się, że kończy się na '/'
    const dir = p.endsWith('/') ? p : p.replace(/[^/]+$/, '');
    return dir;
  })();

  // Zawsze celujemy w docs/data/index.json względem bieżącego katalogu
  const dataUrl = new URL('./data/index.json', location.origin + basePath).toString();

  const $tbody = document.getElementById('tbody');
  const $last = document.getElementById('lastUpdated');

  function renderEmpty(msg) {
    $tbody.innerHTML = `<tr><td colspan="4" class="empty">${msg}</td></tr>`;
  }

  try {
    const res = await fetch(dataUrl, { cache: 'no-store' });
    if (!res.ok) {
      renderEmpty(`Nie udało się pobrać danych (${res.status}).`);
      return;
    }
    // index.json ma być tablicą obiektów: { date, source, count, file }
    const items = await res.json();
    if (!Array.isArray(items) || items.length === 0) {
      renderEmpty('Brak wpisów w indeksie.');
      return;
    }

    // sortuj malejąco po dacie (YYYY-MM-DD)
    items.sort((a, b) => (a.date < b.date ? 1 : a.date > b.date ? -1 : 0));

    const rows = items.map((it) => {
      const fileHref = new URL(`./data/${it.file}`, location.origin + basePath).toString();
      return `
        <tr>
          <td>${it.date}</td>
          <td>${it.source ?? '-'}</td>
          <td>${it.count ?? '-'}</td>
          <td><a href="${fileHref}" target="_blank" rel="noopener">podgląd</a></td>
        </tr>
      `;
    });

    $tbody.innerHTML = rows.join('');

    // ostatnia data do pigułki
    $last.textContent = items[0]?.date ?? '—';
  } catch (err) {
    console.error(err);
    renderEmpty('Błąd podczas przetwarzania danych.');
  }
})();
