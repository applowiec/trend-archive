#!/usr/bin/env python3
import os
import sys
import json
import datetime as dt
from typing import List, Tuple

import requests
from pytrends.request import TrendReq

DATA_DIR = "data"
INDEX_FILE = os.path.join(DATA_DIR, "index.json")
SOURCE_NAME = "google-trends(PL)"
MAX_ITEMS = 20

def now_dates() -> Tuple[str, str]:
    ts = dt.datetime.utcnow()
    return ts.strftime("%Y-%m-%d"), ts.strftime("%Y-%m-%d %H:%M:%S UTC")

def ensure_dirs():
    os.makedirs(DATA_DIR, exist_ok=True)

def load_index(path: str):
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def save_index(path: str, data):
    data = sorted(data, key=lambda x: x.get("date",""), reverse=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def write_markdown(date_slug: str, human_ts: str, items: List[str]) -> str:
    md_path = os.path.join(DATA_DIR, f"{date_slug}.md")
    title = f"# {date_slug} — snapshot trendów Google (PL)\n"
    body = "\n".join(f"- {s}" for s in items) if items else "_brak danych_"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(f"{title}\n{body}\n")
    return md_path

def update_index(index_path: str, date_slug: str, count: int):
    idx = load_index(index_path)
    entry = {"date": date_slug, "source": SOURCE_NAME, "count": count, "file": f"{date_slug}.md"}
    for i, e in enumerate(idx):
        if e.get("date") == date_slug:
            idx[i] = entry
            break
    else:
        idx.append(entry)
    save_index(index_path, idx)
    return idx

def fetch_trending_searches_pytrends(max_items: int) -> List[str]:
    try:
        pt = TrendReq(hl="pl-PL", tz=120)
        df = pt.trending_searches(pn="poland")
        items = [str(x).strip() for x in list(df[0]) if str(x).strip()]
        return items[:max_items]
    except Exception as e:
        print(f"[warn] trending_searches failed: {e}")
        return []

def fetch_today_searches_pytrends(max_items: int) -> List[str]:
    try:
        pt = TrendReq(hl="pl-PL", tz=120)
        arr = pt.today_searches(pn="PL")
        items = [str(x).strip() for x in arr if str(x).strip()]
        return items[:max_items]
    except Exception as e:
        print(f"[warn] today_searches failed: {e}")
        return []

def fetch_dailytrends_api(max_items: int) -> List[str]:
    url = "https://trends.google.com/trends/api/dailytrends"
    params = {"hl": "pl-PL", "tz": "120", "geo": "PL"}
    try:
        r = requests.get(url, params=params, timeout=20)
        r.raise_for_status()
        text = r.text[5:] if r.text.startswith(")]}',") else r.text
        data = json.loads(text)
        days = data.get("default", {}).get("trendingSearchesDays", [])
        items = []
        for day in days:
            for tr in day.get("trendingSearches", []):
                q = tr.get("title", {}).get("query")
                if q:
                    items.append(q.strip())
        # deduplikacja z zachowaniem kolejności
        seen, out = set(), []
        for t in items:
            if t not in seen:
                seen.add(t)
                out.append(t)
        return out[:max_items]
    except Exception as e:
        print(f"[warn] dailytrends API failed: {e}")
        return []

def fetch_trends_pl(max_items: int):
    items = fetch_trending_searches_pytrends(max_items)
    if items: return items, "pytrends.trending_searches"
    items = fetch_today_searches_pytrends(max_items)
    if items: return items, "pytrends.today_searches"
    items = fetch_dailytrends_api(max_items)
    if items: return items, "dailytrends.api"
    return [], "none"

def main() -> int:
    ensure_dirs()
    date_slug, human_ts = now_dates()
    print(f"== {human_ts} ==")
    items, used = fetch_trends_pl(MAX_ITEMS)
    print(f"Źródło: {used} | n={len(items)}")
    md_rel = write_markdown(date_slug, human_ts, items)
    idx = update_index(INDEX_FILE, date_slug, len(items))
    print(f"[ok] {date_slug}: {len(items)} pozycji | plik: {md_rel} | index: {INDEX_FILE}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
