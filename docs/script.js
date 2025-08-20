(async () => {
  const listEl = document.getElementById('trends-list');
  const detailsEl = document.getElementById('details');
  const metaEl = document.getElementById('meta');

  function setEmpty(msg) {
    listEl.innerHTML = `<li class="empty">${msg}</li>`;
    detailsEl.textContent = 'Wybierz snapshot z listy.';
    metaEl.textContent = '';
  }

  async function fetchJson(url) {
    const res = await fetch(url, { cache: 'no-store' });
    if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
    return res.json();
  }

  async function fetchText(url) {
    const res = await fetch(url, { cache: 'no-store' });
    if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
    return res.text();
  }

  let index;
  try {
    // Działa zarówno lokalnie jak i na Pages (docs/ jest rootem strony)
    index = await fetchJson('./data/index.json');
  } catch (e) {
    console.error('Nie udało się pobrać index.json:', e);
    setEmpty('Brak danych (index.json niedostępny).');
    return;
  }

  if (!Array.isArray(index) || index.length === 0) {
    setEmpty('Brak snapshotów.');
    return;
  }

  // posortuj malejąco po dacie (gdyby backend nie posortował)
  index.sort((a, b) => String(b.date).localeCompare(String(a.date)));

  listEl.innerHTML = '';
  index.forEach((item, i) => {
    const li = document.createElement('li');
    li.innerHTML = `<strong>${item.date}</strong> &mdash; ${item.count ?? '?'} pozycji`;
    li.addEventListener('click', async () => {
      [...listEl.children].forEach(c => c.classList.remove('active'));
      li.classList.add('active');

      metaEl.textContent = `Źródło: ${item.source || '—'} • Plik: ${item.file || '—'}`;

      const mdPath = `./data/${item.file}`;
      try {
        const text = await fetchText(mdPath);
        detailsEl.textContent = text;
        detailsEl.classList.remove('empty');
      } catch (e) {
        console.error('Błąd pobrania pliku MD:', mdPath, e);
        detailsEl.textContent = 'Nie udało się wczytać treści snapshotu.';
        detailsEl.classList.add('empty');
      }
    });
    if (i === 0) li.classList.add('active'); // preselect first
    listEl.appendChild(li);
  });

  // auto-otwórz pierwszy
  listEl.firstElementChild?.click();
})();
