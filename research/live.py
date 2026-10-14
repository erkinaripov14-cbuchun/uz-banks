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


# Foiz qaysi ma'noda yozilgani — matndagi atrofiga qarab
RATE_WORDS = re.compile(r"foiz|stavka|yillik|годов|ставк|процент|interest|rate", re.I)
NOT_RATE_WORDS = re.compile(
    r"badal|взнос|boshlang|первоначал|jarima|penya|пеня|неусто|штраф|muddatidan oldin|досрочн|oldin yech|"
    r"keshbek|cashback|кешбэк|komissiya|комисси|chegirma|скидк|soliq|налог|qarz yuki|долговой нагруз|"
    r"ulush|доля|qoplash|покрыти|garov|залог|sug.urta|страхов|inflyatsiya|инфляц", re.I)
FX_TITLE = re.compile(r"dollar|usd|\$|yevro|evro|euro|eur|€|valyuta|валют|доллар|евро", re.I)
NOT_PRODUCT = re.compile(r"yacheyka|ячейк|seyf|сейф|ijara qutisi", re.I)


def _rates(p, kind):
    """Sahifadagi foizlardan faqat stavkaga tegishlilarini olish: (min, max) yoki None."""
    good, plain = [], []
    for r in p.get("rates") or []:
        ctx = r.get("context", "")
        if NOT_RATE_WORDS.search(ctx):
            continue
        (good if RATE_WORDS.search(ctx) else plain).append(r)
    use = good or plain
    if kind == "O" and any(r["min"] >= 3 for r in use):
        use = [r for r in use if r["min"] >= 3]  # 1–2% yonida yuqori stavka bo'lsa — bu muddatidan oldin yechish
    if not use:
        return None
    lo, hi = min(r["min"] for r in use), max(r["max"] for r in use)
    if hi - lo > 15:   # oralig'i juda keng — sahifada turli narsalar aralashgan, ishonchsiz
        return None
    return lo, hi


# Mahsulot nomi emas: ro'yxat, xizmat va xato sahifalari
GENERIC_TITLES = re.compile(
    r"^(kredit(lar)?|kreditlash|kredit mahsulotlari|omonat(lar)?|depozit(lar)?|amanatlar|jismoniy shaxslar\w*|"
    r"kalkulyator\w*|savol[- ]javob\w*|talabnoma\w*|ariza\w*|saytdan qidirish|qidiruv|404|"
    r"xizmat sifatini baholang|доступ запрещён|bosh sahifa|asosiy|varaqasi\*?|.{0,3}|"
    r"avtokreditlar|ipoteka kreditlari|mikroqarzlar|mikrokreditlar|iste.mol kreditlari|"
    r"omonatlar va depozitlar|xorijiy valyutada|milliy valyutada|вклады|кредиты)$", re.I)


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
                if not title or GENERIC_TITLES.match(title) or NOT_PRODUCT.search(title):
                    continue
                rng = _rates(p, kind) if p.get("rates") is not None else (p["rate_min"], p["rate_max"])
                if not rng or not _plausible(kind, *rng):
                    continue
                lo, hi = rng
                key = (bank["bank"], title.lower(), lo, hi)
                if key in seen:
                    continue
                seen.add(key)
                cur = p.get("currencies") or []
                if kind == "O" and FX_TITLE.search(f"{title} {p['url']}"):
                    cur = [c for c in cur if c != "UZS"] or ["USD"]
                cat = _category(section, f"{title} {p['url']}", cur)
                tmax = p.get("term_max_months")
                long_ok = cat in ("Ipoteka", "Ta'lim") or kind == "O"
                term = _months(p.get("term_min_months"), tmax) if tmax is None or tmax <= 120 or long_ok else ""
                rows.append({
                    "bank": bank["bank"], "type": kind,
                    "cat": cat,
                    "name": title[:120],
                    "lo": lo, "hi": hi,
                    "term": term,
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
