// docs/script.js
const DATA_BASE = './data/';

async function loadIndex() {
  const res = await fetch(`${DATA_BASE}index.json`, { cache: 'no-store' });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

function renderList(items) {
  const list = document.getElementById('days');
  list.innerHTML = '';
  if (!items || !items.length) {
    list.innerHTML = '<li>Brak danych</li>';
    return;
  }
  items
    .sort((a,b) => (a.date < b.date ? 1 : -1))
    .forEach(({ date, count, file }) => {
      const li = document.createElement('li');
      li.innerHTML = `
        <a href="data/${file}" target="_blank" rel="noopener">
          <strong>${date}</strong> — wpisów: ${count}
        </a>`;
      list.appendChild(li);
    });
}

(async () => {
  try {
    const data = await loadIndex();
    renderList(data);
  } catch (e) {
    console.error('Błąd ładowania index.json:', e);
    const list = document.getElementById('days');
    list.innerHTML = `<li>Błąd ładowania danych (sprawdź Console/Network).</li>`;
  }
})();
