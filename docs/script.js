async function load() {
  try {
    const res = await fetch('../data/index.json', { cache: 'no-store' });
    const items = await res.json();
    const ul = document.getElementById('list');
    ul.innerHTML = '';
    items.forEach(i => {
      const li = document.createElement('li');
      const a  = document.createElement('a');
      a.href = `../data/${i.file}`;
      a.textContent = `${i.date} — ${i.source} (${i.count} pozycji)`;
      li.appendChild(a);
      ul.appendChild(li);
    });
  } catch (e) {
    console.error(e);
  }
}
load();
