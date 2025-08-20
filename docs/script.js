// docs/script.js

// Ustal bazową ścieżkę repo dla GitHub Pages: "/trend-archive"
const parts = window.location.pathname.split('/').filter(Boolean);
// dla adresów w stylu "/trend-archive/" parts[0] === "trend-archive"
const base = parts.length ? `/${parts[0]}` : '';

// Ładuj indeks z repo (działa lokalnie i na Pages)
fetch(`${base}/data/index.json`)
  .then(r => r.json())
  .then(index => {
    const list = document.getElementById('days');
    list.innerHTML = '';
    index.days.forEach(d => {
      const li = document.createElement('li');
      li.innerHTML = `<a href="${base}/data/${d.date}.md">${d.date}</a> — ${d.count} trendów`;
      list.appendChild(li);
    });
  })
  .catch(err => {
    console.error('Nie udało się wczytać index.json:', err);
    document.getElementById('days').innerHTML =
      '<li>Nie udało się wczytać danych. Spróbuj odświeżyć za minutę.</li>';
  });
