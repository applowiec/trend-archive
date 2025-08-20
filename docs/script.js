async function loadTrends() {
  const statusEl = document.getElementById("status");
  const listEl = document.getElementById("days");

  try {
    // Spróbuj wczytać index.json z /docs/data/
    const res = await fetch("data/index.json");
    if (!res.ok) throw new Error(`HTTP ${res.status}`);

    const snapshots = await res.json();

    if (snapshots.length === 0) {
      statusEl.textContent = "Brak dostępnych trendów.";
      return;
    }

    statusEl.textContent = `Znaleziono ${snapshots.length} snapshotów:`;

    snapshots.forEach(snap => {
      const li = document.createElement("li");

      const a = document.createElement("a");
      a.href = `data/${snap.file}`;
      a.textContent = `${snap.date} — ${snap.count} trendów (${snap.source})`;

      li.appendChild(a);
      listEl.appendChild(li);
    });
  } catch (err) {
    console.error(err);
    statusEl.textContent = "Błąd ładowania danych trendów.";
  }
}

// uruchom po załadowaniu strony
document.addEventListener("DOMContentLoaded", loadTrends);
