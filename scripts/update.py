#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Trend Archive — dzienny snapshot trendów Google (PL)

- Pobiera dzienne "Trending Searches" dla Polski (pytrends.trending_searches pn='poland').
- Zapisuje:
    * data/YYYY-MM-DD.md         — lista trendów (Markdown)
    * data/index.json            — indeks dla frontu (docs/)
- Projekt zakłada, że workflow skopiuje data/* do docs/data/ (patrz .github/workflows/update.yml).

Autor: applowiec + GPT
"""

from __future__ import annotations
import os
import json
import sys
import time
import traceback
from typing import List, Tuple, Dict
from datetime import datetime, timezone

# === KONFIG ===
DATA_DIR: str = "data"
INDEX_FILE: str = os.path.join(DATA_DIR, "index.json")
SOURCE_NAME: str = "google-trends(PL)"
MAX_ITEMS: int = 20  # ile pozycji maksymalnie w Markdownie

# === UTYLITKI ===
def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)

def now_dates() -> Tuple[str, str]:
    """
    Zwraca:
      - date_slug: YYYY-MM-DD (w UTC)
      - human_ts:  2025-08-20 HH:MM:SS UTC
    """
    now_utc = datetime.now(timezone.utc)
    return now_utc.strftime("%Y-%m-%d"), now_utc.strftime("%Y-%m-%d %H:%M:%S UTC")

def load_index(path: str) -> List[Dict]:
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        print(f"[WARN] Nie udało się wczytać {path}, zaczynam od pustej listy.", file=sys.stderr)
        return []

def save_index(path: str, data: List[Dict]) -> None:
    ensure_dir(os.path.dirname(path))
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def write_markdown(date_slug: str, human_ts: str, items: List[str]) -> str:
    """
    Tworzy plik data/YYYY-MM-DD.md i zwraca jego ścieżkę względną.
    """
    ensure_dir(DATA_DIR)
    md_path = os.path.join(DATA_DIR, f"{date_slug}.md")
    lines: List[str] = []
    lines.append(f"# {date_slug} — snapshot trendów Google (PL)")
    lines.append("")  # pusty wiersz

    if items:
        for t in items:
            lines.append(f"- {t}")
    else:
        lines.append("_brak danych_")

    lines.append("")  # newline na końcu
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return os.path.relpath(md_path).replace("\\", "/")

# === POBIERANIE TRENDÓW ===
def fetch_trends_pl(limit: int = MAX_ITEMS) -> Tuple[List[str], str]:
    """
    Zwraca (lista_trendów, pn_used). Wymusza dzienne „Trending Searches” dla Polski.
    """
    try:
        from pytrends.request import TrendReq
    except Exception:
        print("[ERROR] Brak modułu 'pytrends' — dodaj go do requirements.txt i zainstaluj w CI.", file=sys.stderr)
        return [], "error"

    # hl = pl-PL, tz = offset (minuty) — 120 = CEST zimą 60; damy 120 aby nie przeszkadzało
    pytrends = TrendReq(hl="pl-PL", tz=120)

    # Najstabilniejsze: trending_searches(pn='poland')
    tries = 3
    for attempt in range(1, tries + 1):
        try:
            df = pytrends.trending_searches(pn="poland")
            # DataFrame z kolumną 0
            items = [str(x).strip() for x in df[0].tolist() if str(x).strip()]
            return items[:limit], "poland"
        except Exception as e:
            print(f"[WARN] Próba {attempt}/{tries} — błąd Trends: {e}", file=sys.stderr)
            time.sleep(2 * attempt)

    # Ostateczny fallback — pusto
    return [], "error"

# === GŁÓWNY PRZEPŁYW ===
def main() -> int:
    date_slug, human_ts = now_dates()
    print(f"== {human_ts} ==")

    # 1) Pobierz trendy
    items, pn_used = fetch_trends_pl(MAX_ITEMS)
    count = len(items)
    print(f"Pobrano {count} pozycji z {SOURCE_NAME}, pn='{pn_used}'.")

    # 2) Zapisz Markdown
    md_rel = write_markdown(date_slug, human_ts, items)
    print(f"Zapisano Markdown: {md_rel}")

    # 3) Zaktualizuj index.json
    index = load_index(INDEX_FILE)

    entry = {
        "date": date_slug,
        "source": SOURCE_NAME,
        "count": count,
        "file": f"{date_slug}.md",
    }

    # zaktualizuj istniejący dzień (jeśli był), inaczej dodaj
    found = False
    for i, e in enumerate(index):
        if e.get("date") == date_slug:
            index[i] = entry
            found = True
            break
    if not found:
        index.append(entry)

    # posortuj malejąco po dacie (string YYYY-MM-DD sortuje się poprawnie)
    index.sort(key=lambda e: e.get("date", ""), reverse=True)
    save_index(INDEX_FILE, index)
    print(f"Zaktualizowano indeks: {INDEX_FILE} (n={len(index)})")

    # 4) Podsumowanie (pojawia się w logach Actions)
    print(f"[OK] {date_slug}: zapisano {count} trendów → {md_rel} + {INDEX_FILE}")
    # status 0 zawsze — front pokaże „0” jeśli brak danych
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit as e:
        raise
    except Exception:
        traceback.print_exc()
        sys.exit(1)
