#!/usr/bin/env python3
from __future__ import annotations

import json
import time
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

# ──────────────────────────────────────────────────────────────────────────────
# Ustawienia
DATA_DIR = Path("data")
DATA_DIR.mkdir(parents=True, exist_ok=True)

MAX_ITEMS = 20  # ile trendów publikować dziennie
SOURCE_NAME = "google-trends(PL)"


def utc_now_pl() -> datetime:
    """Aktualny czas w strefie PL (dla podpisów)."""
    return datetime.now(ZoneInfo("Europe/Warsaw"))


def load_index(index_path: Path) -> list[dict]:
    if not index_path.exists():
        return []
    try:
        with index_path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        # jeśli cokolwiek nie gra – zaczynamy od pustego
        return []


def save_index(index_path: Path, items: list[dict]) -> None:
    # posortuj malejąco po dacie (nowsze na górze)
    items_sorted = sorted(items, key=lambda x: x.get("date", ""), reverse=True)
    with index_path.open("w", encoding="utf-8") as f:
        json.dump(items_sorted, f, ensure_ascii=False, indent=2)


def fetch_trends_pl(max_items: int = MAX_ITEMS) -> tuple[list[str], str]:
    """
    Pobiera dzisiejsze wyszukiwane hasła Google Trends dla Polski
    z użyciem biblioteki 'pytrends' (unofficial).
    Zwraca (lista_trendów, użyty_pn).
    """
    # import lokalny (żeby skrypt startował nawet jeśli modułu jeszcze nie ma)
    from pytrends.request import TrendReq

    # tz = offset w minutach (CET=60, CEST=120); damy 120 – nie ma to krytycznego znaczenia
    tr = TrendReq(hl="pl-PL", tz=120, retries=3, backoff_factor=0.3)

    # próbujemy kilka wariantów parametru 'pn'
    candidates = ("poland", "PL", "polska")
    for pn in candidates:
        try:
            df = tr.today_searches(pn=pn)
            if df is not None and not df.empty:
                items = [str(x).strip() for x in df[0].tolist()]
                items = [x for x in items if x]  # bez pustych
                return items[:max_items], pn
        except Exception:
            time.sleep(1.2)  # drobny backoff i kolejna próba
            continue

    return [], ""


def write_markdown(md_path: Path, date_str: str, trends: list[str]) -> None:
    header = f"# {date_str} — snapshot trendów Google (PL)\n\n"
    if trends:
        lines = "\n".join(f"- {t}" for t in trends)
    else:
        lines = "_brak danych_"
    md = header + lines + "\n"
    md_path.write_text(md, encoding="utf-8")


def main() -> None:
    now_pl = utc_now_pl()
    date_str = now_pl.strftime("%Y-%m-%d")

    # 1) pobierz trendy
    trends, pn_used = fetch_trends_pl(MAX_ITEMS)

    # 2) zapisz markdown
    md_path = DATA_DIR / f"{date_str}.md"
    write_markdown(md_path, date_str, trends)

    # 3) zaktualizuj index.json
    index_path = DATA_DIR / "index.json"
    index = load_index(index_path)

    entry = {
        "date": date_str,
        "source": SOURCE_NAME,
        "count": len(trends),
        "file": f"{date_str}.md",
    }

    # nadpisz wpis dla tej samej daty (albo dodaj jeśli go nie było)
    index = [e for e in index if e.get("date") != date_str]
    index.append(entry)
    save_index(index_path, index)

    # 4) krótki log do stdout (pojawia się w Actions)
    print(f"[OK] {date_str}: pobrano {len(trends)} trendów (pn='{pn_used}').")
    print(f"Pliki: {md_path} oraz {index_path}")


if __name__ == "__main__":
    main()
