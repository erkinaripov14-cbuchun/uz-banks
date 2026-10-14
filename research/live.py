"""Skraper natijasini (output/<sana>/all.json) saytdagi "Avtomatik" bo'lim uchun qatorlarga aylantirish.

    python research/live.py output/2026-10-14/all.json

Natija research/live/latest.json ga yoziladi. Ma'lumot yetarli bo'lmasa (masalan, bank saytlari
ochilmagan bo'lsa), eski latest.json o'zgarmaydi.
"""
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

OUT = Path(__file__).parent / "live" / "latest.json"

CREDIT_CATS = [
    ("Ipoteka", ("ipoteka", "ипотек", "mortgage", "uy-joy", "uy joy")),
    ("Avtokredit", ("avto", "авто", "auto", "car")),
    ("Mikroqarz", ("mikro", "микро", "micro", "onlayn kredit", "online")),
    ("Ta'lim", ("ta'lim", "talim", "таълим", "образоват", "education")),
    ("Kredit karta", ("karta", "карт", "card", "overdraft", "овердрафт")),
    ("Biznes", ("biznes", "бизнес", "business", "tadbirkor", "kichik")),
]


def _category(section, text, currencies):
    t = text.lower()
    if section == "deposits":
        return "So'm omonat" if not currencies or "UZS" in currencies else "Valyuta omonat"
    return next((name for name, words in CREDIT_CATS if any(w in t for w in words)), "Iste'mol")


def _months(lo, hi):
    if lo is None and hi is None:
        return ""
    fmt = lambda m: f"{m / 12:g} yil" if m >= 12 and m % 12 == 0 else f"{m:g} oy"
    return fmt(hi) + "gacha" if lo == hi or lo is None else f"{fmt(lo)} – {fmt(hi)}"


def _money(v):
    for d, s in ((1e9, " mlrd"), (1e6, " mln"), (1e3, " ming")):
        if v >= d:
            return f"{v / d:g}{s}"
    return f"{v:g}"


def _amount(lo, hi):
    if lo is None:
        return ""
    return f"{_money(hi)} gacha" if lo == hi else f"{_money(lo)} – {_money(hi)}"


# Mahsulot nomi emas: ro'yxat, xizmat va xato sahifalari
GENERIC_TITLES = re.compile(
    r"^(kredit(lar)?|kreditlash|kredit mahsulotlari|omonat(lar)?|depozit(lar)?|amanatlar|jismoniy shaxslar\w*|"
    r"kalkulyator\w*|savol[- ]javob\w*|talabnoma\w*|ariza\w*|saytdan qidirish|qidiruv|404|"
    r"xizmat sifatini baholang|доступ запрещён|bosh sahifa|asosiy|varaqasi\*?|.{0,3})$", re.I)


def _plausible(kind, lo, hi):
    """Matndan olingan foiz real bo'lishi kerak: omonat 0.5–35%, kredit 5–60% (0% aksiya — alohida)."""
    if kind == "O":
        return 0.5 <= lo <= hi <= 35
    return (lo == hi == 0) or (5 <= lo <= hi <= 60)


def convert(results):
    rows, seen = [], set()
    for bank in results:
        date = (bank.get("scraped_at") or "")[:10]
        for section, kind in (("credits", "K"), ("deposits", "O")):
            for p in bank.get(section, []):
                # Ro'yxat sahifalarida bir nechta mahsulot foizi aralash — faqat mahsulot sahifalari
                if p.get("kind") != "product" or p.get("rate_min") is None:
                    continue
                title = (p.get("title") or "").strip()
                if not title or GENERIC_TITLES.match(title):
                    continue
                if not _plausible(kind, p["rate_min"], p["rate_max"]):
                    continue
                key = (bank["bank"], title.lower(), p["rate_min"], p["rate_max"])
                if key in seen:
                    continue
                seen.add(key)
                cur = p.get("currencies") or []
                rows.append({
                    "bank": bank["bank"], "type": kind,
                    "cat": _category(section, f"{p.get('title', '')} {p['url']}", cur),
                    "name": title[:120],
                    "lo": p["rate_min"], "hi": p["rate_max"],
                    "term": _months(p.get("term_min_months"), p.get("term_max_months")),
                    "amount": _amount(p.get("amount_min"), p.get("amount_max")),
                    "cur": "UZS" if not cur or "UZS" in cur else cur[0],
                    "url": p["url"], "date": date, "note": "", "stale": False,
                })
    return rows


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    results = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    rows = convert(results)
    ok = [r["bank"] for r in results if any(r.get(s) for s in ("credits", "deposits"))]
    print(f"{len(rows)} ta mahsulot, {len(ok)}/{len(results)} bankdan")
    if not rows:
        print("Hech narsa topilmadi — research/live/latest.json o'zgartirilmadi.")
        return
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps({
        "updated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "banks_ok": len(ok), "banks_total": len(results),
        "failed": sorted(r["bank"] for r in results if r["bank"] not in ok),
        "rows": rows,
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Yozildi: {OUT}")


if __name__ == "__main__":
    main()
