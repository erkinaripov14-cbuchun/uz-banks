"""Qo'lda tekshirilgan ma'lumot (data_rasmiy.py) va saytlardan avtomatik o'qilgan ma'lumotni (live/latest.json) birlashtirish.

- Bir xil mahsulot (bank, turi va nomi mos) — bitta qator: asosiy foiz qo'lda tekshirilgandan,
  "saytda hozir" — avtomatik o'qilgandan.
- Faqat avtomatik topilgan mahsulot — yangi qator, manbasi "avtomatik".
- Har bir qator jismoniy yoki yuridik shaxslar uchun ekani belgilanadi.
"""
import json
import re
from pathlib import Path

from data_rasmiy import ROWS
import live as live_rules
import xulosalar

LIVE = Path(__file__).parent / "live" / "latest.json"
NOISE_WORDS = re.compile(r"\b(omonati?|krediti?|avtokrediti?|mikroqarzi?|mikrokrediti?|depoziti?|ipotekasi|"
                         r"вклад|кредит|online|onlayn|yangi)\b", re.I)


def _norm(name):
    s = re.sub(r"[«»“”\"'‘’`ʻʼ]", "", name.lower())
    s = NOISE_WORDS.sub(" ", s)
    return re.sub(r"[^\w]+", " ", s).strip()


def _same(a, b):
    a, b = _norm(a), _norm(b)
    if len(a) < 3 or len(b) < 3:
        return False
    return a == b or (len(a) >= 4 and a in b) or (len(b) >= 4 and b in a)


def live_meta():
    if not LIVE.exists():
        return None
    d = json.loads(LIVE.read_text(encoding="utf-8"))
    return {k: v for k, v in d.items() if k != "rows"}


def _live_rows():
    if not LIVE.exists():
        return []
    out = []
    for r in json.loads(LIVE.read_text(encoding="utf-8"))["rows"]:
        # Eski yozilgan fayllar uchun ham bugungi qoidalar qo'llanadi
        name = live_rules.clean_title(r["name"])
        if not name or live_rules.GENERIC_TITLES.match(name) or live_rules.NOT_PRODUCT.search(name):
            continue
        r = {**r, "name": name}
        seg = r.get("segment") or live_rules._segment(r)
        if r["type"] == "K" and seg == "yuridik" and r["cat"] in ("Iste'mol", "Mikroqarz"):
            r["cat"] = "Biznes"
        if not live_rules._plausible(r["type"], r["lo"], r["hi"], r["cur"], r["cat"]):
            continue
        out.append({**r, "segment": seg})
    return out


def merged_rows():
    rows = []
    for r in ROWS:
        bank, typ, cat, name, lo, hi, term, amount, cur, url, date, note = r
        rows.append({"bank": bank, "type": typ, "cat": cat, "name": name, "lo": lo, "hi": hi, "term": term,
                     "amount": amount, "cur": cur, "url": url, "date": date, "note": note,
                     "stale": xulosalar.is_stale(r), "segment": "yuridik" if cat == "Biznes" else "jismoniy",
                     "source": "tekshirilgan", "live": None})
    for lr in _live_rows():
        match = next((r for r in rows if r["source"] == "tekshirilgan" and r["bank"] == lr["bank"]
                      and r["type"] == lr["type"] and _same(r["name"], lr["name"])), None)
        if match:
            # "Saytda hozir" faqat aniq (tor oraliqli) qiymat bo'lsa ko'rsatiladi
            if match["live"] is None and lr["hi"] - lr["lo"] <= 3:
                match["live"] = {"lo": lr["lo"], "hi": lr["hi"], "date": lr["date"], "url": lr["url"]}
            continue
        rows.append({**lr, "source": "avtomatik", "live": None})
    return rows
