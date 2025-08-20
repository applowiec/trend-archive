#!/usr/bin/env python3
import os
import sys
import json
import time
import datetime as dt
from typing import List, Tuple

import requests
from pytrends.request import TrendReq

# ------- konfiguracja -------
DATA_DIR = "data"
INDEX_FILE = os.path.join(DATA_DIR, "index.json")
SOURCE_NAME = "google-trends(PL)"
MAX_ITEMS = 20  # utnijmy listy żeby były krótkie i stabilne

# ------- utilsy -------
def now_dates() -> Tuple[str, str]:
    """Zwraca (date_slug, human_ts) w strefie Europy/Środkowej."""
    # użyjemy czasu UTC + info o strefie dla przejrzystości
    ts = dt.datetime.utcnow()
    date_slug = ts.strftime("%Y-%m-%d")
    human = ts.strftime("%Y-%m-%d %H:%M:%S UTC")
    return date_slug, human

def ensure_dirs():
    os.makedirs(DATA_DIR, exist_ok=True)

def load_index(path: str) -> List[dict]:
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def save_index(path: str, data: List[dict]) -> None:
    # sort malejąco po dacie (string YYYY-MM-DD sortuje się leksykograficznie)
    data_sorted = sorted(data, key=lambda x: x.get("date", ""), reverse=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data_sorted, f, ensure_ascii=False, indent=2)

def write_markdown(date_slug: str, human_ts: str, items: List[str]) -> str:
    """Zapisuje markdown dnia i zwraca relatywną ścieżkę pliku .md."""
    md_path = os.path.join(DATA_DIR, f"{date_slug}.md")
    title = f"# {date_slug} — snapshot trendów Google (PL)\n"
    if items:
        body = "\n".join(f"- {s}" for s in items)
    else:
        body = "_brak danych_"
    content = f"{title}\n{body}\n"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(content)
    return md_path

def update_index(index_path: str, date_slug: str, count: int) -> List[dict]:
    idx = load_index(index_path)
    entry = {
        "date": date_slug,
        "source": SOURCE_NAME,
        "count": count,
        "file": f"{date_slug}.md",
    }
    # podmień jeśli już istnieje wpis dla danej daty
    found = False
    for i, e in enumerate(idx):
        if e.get("date") == date_slug:
            idx[i] = entry
            found = True
            break
    if not found:
        idx.append(entry)
    save_index(index_path, idx)
    return idx

# ------- zbiory danych (3 podejścia) -------
def fetch_trending_searches_pytrends(max_items: int) -> List[str]:
    """pytrends.trending_searches(pn='poland')"""
    try:
        pt = TrendReq(hl="pl-PL", tz=120)  # tz=120 ≈ CET/CEST w minutach
        df = pt.trending_searches(pn="poland")
        items = [str(x).strip() for x in list(df[0]) if str(x).strip()]
        return items[:max_items]
    except Exception as e:
        print(f"[warn] trending_searches failed: {e}")
        return []

def fetch_today_searches_pytrends(max_items: int) -> List[str]:
    """pytrends.today_searches — często działa, gdy trending_searches zwraca pustkę."""
    try:
        pt = TrendReq(hl="pl-PL", tz=120)
        arr = pt.today_searches(pn="PL")  # w niektórych wersjach parametr pn ignorowany
        items = [str(x).strip() for x in arr if str(x).strip()]
        return items[:max_items]
    except Exception as e:
        print(f"[warn] today_searches failed: {e}")
        return []

def fetch_dailytrends_api(max_items: int) -> List[str]:
    """
    Publiczne endpointy Trends: dailytrends (na wczoraj/dziś). Nie wymaga auth.
    Trzeba zrzucić 5 znaków prefixu )]}', i sparsować JSON.
    """
    url = "https://trends.google.com/trends/api/dailytrends"
    params = {
        "hl": "pl-PL",
        "tz": "120",
        "geo": "PL"
    }
    try:
        r = requests.get(url, params=params, timeout=20)
        r.raise_for_status()
        text = r.text
        # strip prefix
        if text.startswith(")]}',"):
            text = text[5:]
        data = json.loads(text)
        days = data.get("default", {}).get("trendingSearchesDays", [])
        items: List[str] = []
        for day in days:
            for tr in day.get("trendingSearches", []):
                title = tr.get("title", {}).get("query")
                if title:
                    items.append(title.strip())
        # dedupe zachowując kolejność
        seen = set()
        deduped = []
        for t in items:
            if t not in seen:
                seen.add(t)
                deduped.append(t)
        return deduped[:max_items]
    except Exception as e:
        print(f"[warn] dailytrends API failed: {e}")
        return []

def fetch_trends_pl(max_items: int) -> Tuple[List[str], str]:
    """
    Spróbuj kolejno 3 źródeł. Zwraca (lista, nazwa_źródła_użytego).
    """
    items = fetch_trending_searches_pytrends(max_items)
    if items:
        return items, "pytrends.trending_searches"

    items = fetch_today_searches_pytrends(max_items)
    if items:
        return items, "pytrends.today_searches"

    items = fetch_dailytrends_api(max_items)
    if items:
        return items, "dailytrends.api"

    return [], "none"

# ------- główny flow -------
def main() -> int:
    ensure_dirs()
    date_slug, human_ts = now_dates()

    print(f"== {human_ts} ==")
    items, source_used = fetch_trends_pl(MAX_ITEMS)
    print(f"Źródło: {source_used}  |  liczba pozycji: {len(items)}")

    md_rel = write_markdown(date_slug, human_ts, items)
    idx = update_index(INDEX_FILE, date_slug, len(items))
    print(f"Zapisano: {md_rel}")
    print(f"Zaktualizowano {INDEX_FILE} (n={len(idx)})")

    # krótkie podsumowanie (pojawia się w Actions logach)
    print(f"[ok] {date_slug}: {len(items)} pozycji | plik: {md_rel} | index: {INDEX_FILE}")
    # jeżeli pusto – zwróć 0 (strona frontowa i tak pokaże „brak danych”)
    return 0

if __name__ == "__main__":
    sys.exit(main())
