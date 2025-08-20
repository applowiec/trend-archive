(async () => {
  const LIST_ID = "list";
  const DATA_BASE = "data";              // na Pages katalog docs/ jest rootem, więc data/ jest pod /
  const INDEX_URL = `${DATA_BASE}/index.json?ts=${Date.now()}`; // bez cache

  const listEl = document.getElementById(LIST_ID);
  if (!listEl) return;

  try {
    const res = await fetch(INDEX_URL, { cache: "no-store" });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const index = await res.json();      // spodziewamy się { "days": ["YYYY-MM-DD", ...] }

    // Pusta lista? pokaż info
    if (!index?.days?.length) {
      listEl.innerHTML = "<li>Brak danych (index.json nie zawiera dni).</li>";
      return;
    }

    // Wyczyść i wyrenderuj
    listEl.innerHTML = "";
    [...index.days].sort().reverse().forEach((day) => {
      const li = document.createElement("li");
      const a = document.createElement("a");
      a.href = `${DATA_BASE}/${day}.md`; // link bezpośrednio do Markdownu
      a.textContent = day;
      li.appendChild(a);
      listEl.appendChild(li);
    });
  } catch (err) {
    console.error("Nie udało się wczytać index.json:", err);
    listEl.innerHTML = `<li>Błąd ładowania index.json — sprawdź w konsoli i czy URL istnieje.</li>`;
  }
})();
