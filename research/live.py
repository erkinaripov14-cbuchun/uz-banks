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
NOT_PRODUCT = re.compile(r"yacheyka|ячейк|seyf|сейф|ijara qutisi|arxiv|архив|archive", re.I)


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
    if hi - lo > 10:   # oralig'i juda keng — sahifada turli narsalar aralashgan, ishonchsiz
        return None
    return lo, hi


# Mahsulot nomi emas: ro'yxat, xizmat va xato sahifalari
GENERIC_TITLES = re.compile(
    r"^(kredit(lar)?|kreditlash|kredit mahsulotlari|omonat(lar)?|depozit(lar)?|amanatlar|jismoniy shaxslar\w*|"
    r"kalkulyator\w*|savol[- ]javob\w*|talabnoma\w*|ariza\w*|saytdan qidirish|qidiruv|404|"
    r"xizmat sifatini baholang|доступ запрещён|bosh sahifa|asosiy|varaqasi\*?|.{0,3}|"
    r"avtokreditlar|ipoteka kreditlari|mikroqarzlar|mikrokreditlar|iste.mol kreditlari|"
    r"omonatlar va depozitlar|barchasi omonatlar haqida|xorijiy valyutada|milliy valyutada|вклады|кредиты)$", re.I)


# Kartochkadagi birinchi qator mahsulot nomi bo'lmasligi mumkin: summa, stavka, reklama jumlasi
BAD_TITLE = re.compile(r"^(сумма|summa|общая|umumiy|stavka|ставка|foiz|bazaviy|базов|muddat|срок|bizda|biz |"
                       r"har bir|ariza|подробнее|batafsil|ko.proq|[\d\s.,+%–-]+$)", re.I)


def clean_title(t):
    t = re.sub(r"\s+", " ", t or "").strip()
    return "" if not t or BAD_TITLE.search(t) or len(t) > 70 else t


BUSINESS_URL = re.compile(r"/(corporate|corporate-customers|small-business|legal|juristic|yuridik[-_]shaxslar\w*|business|biznes-uchun)(/|$)", re.I)


def _segment(p):
    return p.get("segment") or ("yuridik" if BUSINESS_URL.search(re.sub(r"^https?://[^/]+", "", p["url"]) + "/") else "jismoniy")


def _plausible(kind, lo, hi, cur="UZS", cat=""):
    """Matndan olingan foiz real bo'lishi kerak; aks holda qator saytga chiqmaydi."""
    if hi - lo > 10:
        return False
    if kind == "O":
        return (3 <= lo <= hi <= 30) if cur == "UZS" else (0.5 <= lo <= hi <= 12)
    if lo == hi == 0:          # 0% aksiya (masalan, avtokredit)
        return True
    cap = {"Ipoteka": 35, "Avtokredit": 40, "Ta'lim": 30}.get(cat, 50)   # yuqorisi — odatda boshlang'ich badal
    return 10 <= lo <= hi <= cap


def _items(bank, section):
    """Mahsulot sahifalari + ro'yxat sahifalaridagi kartochkalar (alohida sahifasi o'qilmagan bo'lsa)."""
    pages = bank.get(section, [])
    product_urls = {p["url"].rstrip("/") for p in pages if p.get("kind") == "product"}
    for p in pages:
        if p.get("kind") == "product":
            yield p
            continue
        for c in p.get("cards") or []:
            if c["url"].rstrip("/") in product_urls or c.get("rate_min") is None:
                continue
            lines = [l.strip() for l in c["text"].splitlines() if l.strip()]
            title = next((clean_title(l) for l in lines if clean_title(l) and len(l) > 3), "")
            yield {**c, "title": title[:120], "kind": "card"}


def convert(results):
    rows, seen = [], set()
    for bank in results:
        date = (bank.get("scraped_at") or "")[:10]
        for section, kind in (("credits", "K"), ("deposits", "O")):
            for p in _items(bank, section):
                if p.get("rate_min") is None:
                    continue
                title = clean_title(p.get("title"))
                if not title or GENERIC_TITLES.match(title) or NOT_PRODUCT.search(title):
                    continue
                rng = _rates(p, kind) if p.get("rates") is not None else (p["rate_min"], p["rate_max"])
                if not rng:
                    continue
                lo, hi = rng
                cur = p.get("currencies") or []
                if kind == "O" and FX_TITLE.search(f"{title} {p['url']}"):
                    cur = [c for c in cur if c != "UZS"] or ["USD"]
                cur1 = "UZS" if not cur or "UZS" in cur else cur[0]
                cat = _category(section, f"{title} {p['url']}", cur)
                if kind == "K" and _segment(p) == "yuridik" and cat in ("Iste'mol", "Mikroqarz"):
                    cat = "Biznes"
                if not _plausible(kind, lo, hi, cur1, cat):
                    continue
                key = (bank["bank"], title.lower(), lo, hi)
                if key in seen:
                    continue
                seen.add(key)
                tmax = p.get("term_max_months")
                long_ok = cat in ("Ipoteka", "Ta'lim") or kind == "O"
                term = _months(p.get("term_min_months"), tmax) if tmax is None or tmax <= 120 or long_ok else ""
                rows.append({
                    "bank": bank["bank"], "type": kind, "cat": cat, "segment": _segment(p),
                    "name": title[:120], "lo": lo, "hi": hi, "term": term,
                    "amount": _amount(p.get("amount_min"), p.get("amount_max")),
                    "cur": cur1, "url": p["url"], "date": date, "note": "", "stale": False,
                })
    return rows


def combine(previous, results, rows, now):
    """Yangi natijani avvalgisi bilan birlashtirish: faqat shu safar muvaffaqiyatli o'qilgan banklarning
    qatorlari almashadi. Ayrim banklar uchun yangilash (--only) yoki o'qilmay qolgan bank boshqa banklarning
    ma'lumotini o'chirmaydi."""
    ok = {r["bank"] for r in results if any(r.get(s) for s in ("credits", "deposits"))}
    kept = [r for r in (previous or {}).get("rows", []) if r["bank"] not in ok]
    all_rows = rows + kept
    banks_with_data = {r["bank"] for r in all_rows}
    attempted = {r["bank"] for r in results}
    prev_failed = set((previous or {}).get("failed", []))
    failed = sorted((attempted - ok - banks_with_data) | (prev_failed - ok - banks_with_data - attempted))
    return {
        "updated": now,
        "banks_ok": len(banks_with_data), "banks_total": max(len(attempted | banks_with_data | prev_failed),
                                                             (previous or {}).get("banks_total", 0)),
        "failed": failed,
        "last_run": {"banks": sorted(attempted), "ok": len(ok)},
        "rows": all_rows,
    }


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
    previous = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else None
    data = combine(previous, results, rows, datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"))
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Yozildi: {OUT} — jami {len(data['rows'])} ta mahsulot, {data['banks_ok']} bank")


if __name__ == "__main__":
    main()
