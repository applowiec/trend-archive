#!/usr/bin/env python3
import json, os, time, datetime, pathlib, random

BASE = pathlib.Path(__file__).resolve().parent.parent
DATA = BASE / "data"
DATA.mkdir(exist_ok=True)

# Symulujemy dane (później podmienisz na realne pobieranie)
now = datetime.datetime.utcnow()
stamp = now.strftime("%Y-%m-%d")
items = [f"trend-{i}" for i in range(1, 1 + random.randint(5,15))]

# Zapis dziennego pliku
out_md = DATA / f"{stamp}.md"
with open(out_md, "w", encoding="utf-8") as f:
    f.write(f"# {stamp} — snapshot trendów\n\n")
    for it in items:
        f.write(f"- {it}\n")

# Aktualizacja index.json do frontendu
index_json = DATA / "index.json"
entry = {"date": stamp, "source": "demo", "count": len(items), "file": f"{stamp}.md"}

existing = []
if index_json.exists():
    with open(index_json, "r", encoding="utf-8") as f:
        existing = json.load(f)
# Usuń duplikat tego samego dnia
existing = [e for e in existing if e.get("date") != stamp]
existing.append(entry)
# Sort nowsze na górze
existing.sort(key=lambda e: e["date"], reverse=True)

with open(index_json, "w", encoding="utf-8") as f:
    json.dump(existing, f, ensure_ascii=False, indent=2)
