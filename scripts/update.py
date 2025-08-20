#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Update daily snapshot of Google Trends (PL) and maintain index.json.

Outputs:
  - data/YYYY-MM-DD.md         -> markdown snapshot for the day
  - data/index.json            -> [{date, source, count, file}, ...] (latest first)

Notes:
  - Requires: pytrends, requests (installed via requirements.txt in CI)
  - Safe fallbacks: if no trends fetched, writes "brak danych"
"""

import json
import os
import sys
import time
from datetime import datetime
from typing import List, Tuple

try:
    # Python 3.9+ stdlib timezone
    from zoneinfo import ZoneInfo  # type: ignore
except Exception:  # pragma: no cover
    ZoneInfo = None  # fallback: use UTC

# ---------- Config ----------
SOURCE_NAME = "google-trends-pl"
DATA_DIR = "data"
INDEX_FILE = os.path.join(DATA_DIR, "index.json")
MAX_ITEMS = int(os.environ.get("MAX_ITEMS", "20"))
SLEEP_BETWEEN_ATTEMPTS = 2  # seconds
MAX_ATTEMPTS = 3            # retries for fetch

# ---------- Utils ----------

def now_dates() -> Tuple[str, str]:
    """Return tuple (date_slug, human_ts) in Europe/Warsaw if available, else UTC."""
    tz = ZoneInfo("Europe/Warsaw") if ZoneInfo else None
    now = datetime.now(tz=tz)
    date_slug = now.strftime("%Y-%m-%d")
    human_ts = now.strftime("%Y-%m-%d %H:%M:%S %Z")
    return date_slug, human_ts


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def read_index(path: str) -> List[dict]:
    if not os.path.isfile(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def write_json(path: str, obj) -> None:
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


# ---------- Fetchers ----------

def fetch_trends_pl(limit: int = MAX_ITEMS) -> List[str]:
    """
    Fetch Google 'Trending searches' for Poland using pytrends.
    Returns a list of strings (top queries), length ≤ limit.
    """
    from pytrends.request import TrendReq  # lazy import so script starts even if missing until CI installs

    pytrends = TrendReq(hl="pl-PL", tz=120)  # tz in minutes (UTC+2 in summer)
    # Use retries — Google can rate-limit occasionally on GH runners
    last_err = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            df = pytrends.trending_searches(pn="poland")
            # df has one column (0) with trending queries
            items = df[0].dropna().astype(str).tolist()
            if items:
                return items[:limit]
            # empty -> try again after short sleep
        except Exception as e:  # network/HTTP/parse errors
            last_err = e
        time.sleep(SLEEP_BETWEEN_ATTEMPTS)

    # If we got here: failed to fetch
    if last_err:
        print(f"[warn] fetch_trends_pl failed after {MAX_ATTEMPTS} attempts: {last_err}", file=sys.stderr)
    return []


# ---------- Writers ----------

def write_markdown(date_slug: str, human_ts: str, items: List[str]) -> str:
    """
    Write data/YYYY-MM-DD.md with H1 title and bullet list.
    Returns the relative file path written.
    """
    ensure_dir(DATA_DIR)
    md_path = os.path.join(DATA_DIR, f"{date_slug}.md")

    lines: List[str] = []
    lines.append(f"# {date_slug} — snapshot trendów Google (PL)")
    lines.append("")  # blank

    if items:
        for it in items:
            lines.append(f"- {it}")
    else:
        lines.append("brak danych")

    content = "\n".join(lines) + "\n"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(content)

    print("=== PODGLĄD PIERWSZYCH LINII ===")
    for i, ln in enumerate(lines[:12], 1):
        print(f"{i:02d}: {ln}")
    print("=== KONIEC PODGLĄDU ===")
    return os.path.relpath(md_path, ".")


def update_index(index_path: str, date_slug: str, count: int) -> List[dict]:
    """
    Prepend/replace entry for the date in index.json.
    Keeps newest first, unique by date.
    """
    index = read_index(index_path)
    entry = {"date": date_slug, "source": SOURCE_NAME, "count": count, "file": f"{date_slug}.md"}

    # remove existing entry for that date
    filtered = [e for e in index if e.get("date") != date_slug]
    # newest first
    new_index = [entry] + filtered
    write_json(index_path, new_index)
    return new_index


# ---------- Main ----------

def main() -> int:
    date_slug, human_ts = now_dates()

    print(f"Timestamp: {human_ts}")
    print("Pobieram trendy Google (PL)...")
    items = fetch_trends_pl(MAX_ITEMS)
    count = len(items)
    print(f"Pobrano {count} pozycji.")

    md_rel = write_markdown(date_slug, human_ts, items)
    idx = update_index(INDEX_FILE, date_slug, count)

    print(f"Zapisano: {md_rel}")
    print(f"Zaktualizowano indeks: {INDEX_FILE} (n={len(idx)})")
    # exit 0 even if empty — front się wyświetli, a CI przejdzie
    return 0


if __name__ == "__main__":
    sys.exit(main())
