"""Bank sahifasi matnidan foiz, muddat va summalarni ajratib olish (internetsiz, sof funksiyalar)."""
import re

# Bo'lim kalit so'zlari (uz lotin / uz kirill / rus / ingliz)
SECTION_KEYWORDS = {
    "credits": [
        "kredit", "credit", "кредит", "qarz", "қарз", "заем", "займ", "ipoteka", "ипотек",
        "mortgage", "avtokredit", "автокредит", "mikroqarz", "микрозайм", "loan",
    ],
    "deposits": [
        "omonat", "омонат", "depozit", "deposit", "депозит", "вклад", "jamg'arma",
        "savings", "накопит",
    ],
}

# Mahsulot bo'lmagan sahifalar (kalkulyator, yangiliklar, kartalar va h.k.)
EXCLUDE_KEYWORDS = [
    "news", "yangilik", "новост", "press", "vacanc", "vakans", "вакан", "career",
    "login", "auth", "contact", "aloqa-markaz", "filial", "branch", "atm", "bankomat",
    ".pdf", ".doc", ".xls", "mailto:", "tel:", "javascript:", "#",
]

_NUM = r"\d{1,3}(?:[   ]?\d{3})*(?:[.,]\d+)?"

RATE_RE = re.compile(
    r"(?P<a>\d{1,2}(?:[.,]\d{1,2})?)\s*%?\s*(?:[-–—]|dan|до|to)\s*(?P<b>\d{1,2}(?:[.,]\d{1,2})?)\s*%"
    r"|(?P<c>\d{1,2}(?:[.,]\d{1,2})?)\s*%",
)

TERM_UNITS = {
    "kun": 1 / 30, "кун": 1 / 30, "день": 1 / 30, "дня": 1 / 30, "дней": 1 / 30, "day": 1 / 30, "days": 1 / 30,
    "oy": 1, "ой": 1, "мес": 1, "месяц": 1, "месяца": 1, "месяцев": 1, "month": 1, "months": 1,
    "yil": 12, "йил": 12, "год": 12, "года": 12, "лет": 12, "year": 12, "years": 12,
}
TERM_RE = re.compile(
    r"(?:(?P<a>\d{1,4})\s*(?:[-–—]|dan|до|to)\s*)?(?P<b>\d{1,4})\s*"
    r"(?P<u>kun|кун|дней|дня|день|days?|oy|ой|месяцев|месяца|месяц|мес|months?|yil|йил|года|год|лет|years?)"
    r"(?:gacha|dan|lik|гача|дан|лик)?(?![a-zа-яёўқғҳ])",
    re.IGNORECASE,
)

CURRENCY_MAP = {
    "so'm": "UZS", "so‘m": "UZS", "soʻm": "UZS", "сўм": "UZS", "сум": "UZS", "uzs": "UZS", "sum": "UZS",
    "usd": "USD", "$": "USD", "доллар": "USD", "dollar": "USD",
    "eur": "EUR", "€": "EUR", "евро": "EUR", "yevro": "EUR",
    "rub": "RUB", "рубл": "RUB", "rubl": "RUB",
}
MULTIPLIERS = {
    "ming": 1e3, "минг": 1e3, "тыс": 1e3,
    "mln": 1e6, "million": 1e6, "млн": 1e6, "миллион": 1e6,
    "mlrd": 1e9, "milliard": 1e9, "млрд": 1e9, "миллиард": 1e9,
}
AMOUNT_RE = re.compile(
    rf"(?P<n>{_NUM})\s*(?P<m>ming|минг|тыс\.?|mln\.?|million|млн\.?|миллион\w*|mlrd\.?|milliard|млрд\.?|миллиард\w*)?\s*"
    r"(?P<c>so['‘ʻ`]?m|сўм|сум|uzs|usd|\$|eur|€|rub\w*|рубл\w*|доллар\w*|dollar|евро|yevro)",
    re.IGNORECASE,
)


def _f(s):
    return float(s.replace(",", ".").replace(" ", "").replace(" ", "").replace(" ", ""))


def classify_link(href, text):
    """Havola qaysi bo'limga tegishli: 'credits', 'deposits' yoki None."""
    hay = f"{href} {text}".lower()
    if any(k in hay for k in EXCLUDE_KEYWORDS if k != "#") or href.strip().startswith("#"):
        return None
    for section, words in SECTION_KEYWORDS.items():
        if any(w in hay for w in words):
            return section
    return None


def _context(text, start, end, width=60):
    a, b = max(0, start - width), min(len(text), end + width)
    return re.sub(r"\s+", " ", text[a:b]).strip()


def extract_rates(text):
    out = []
    for m in RATE_RE.finditer(text):
        if m.group("c"):
            lo = hi = _f(m.group("c"))
        else:
            lo, hi = sorted((_f(m.group("a")), _f(m.group("b"))))
        if 0 < lo <= 80 and 0 < hi <= 80:
            out.append({"min": lo, "max": hi, "context": _context(text, m.start(), m.end())})
    return out


def extract_terms(text):
    out = []
    for m in TERM_RE.finditer(text):
        k = TERM_UNITS[m.group("u").lower()]
        b = int(m.group("b"))
        a = int(m.group("a")) if m.group("a") else b
        lo, hi = sorted((a * k, b * k))
        if 0 < hi <= 360:  # 30 yildan oshmaydi
            out.append({"min_months": round(lo, 2), "max_months": round(hi, 2),
                        "raw": m.group(0).strip(), "context": _context(text, m.start(), m.end())})
    return out


def _currency(token):
    t = token.lower()
    for k, v in CURRENCY_MAP.items():
        if t.startswith(k):
            return v
    return None


def extract_amounts(text):
    out = []
    for m in AMOUNT_RE.finditer(text):
        try:
            n = _f(m.group("n"))
        except ValueError:
            continue
        mult = m.group("m")
        if mult:
            key = mult.lower().rstrip(".")
            n *= next((v for k, v in MULTIPLIERS.items() if key.startswith(k)), 1)
        cur = _currency(m.group("c"))
        if cur and n > 0:
            out.append({"value": n, "currency": cur, "raw": m.group(0).strip(),
                        "context": _context(text, m.start(), m.end())})
    return out


def summarize(text):
    """Sahifa matnidan qisqa xulosa: foiz/muddat/summa diapazonlari va valyutalar."""
    rates, terms, amounts = extract_rates(text), extract_terms(text), extract_amounts(text)
    s = {
        "rate_min": min((r["min"] for r in rates), default=None),
        "rate_max": max((r["max"] for r in rates), default=None),
        "term_min_months": min((t["min_months"] for t in terms), default=None),
        "term_max_months": max((t["max_months"] for t in terms), default=None),
        "currencies": sorted({a["currency"] for a in amounts}),
        "amount_min": None, "amount_max": None,
        "rates": rates, "terms": terms, "amounts": amounts,
    }
    uzs = [a["value"] for a in amounts if a["currency"] == "UZS"]
    if uzs:
        s["amount_min"], s["amount_max"] = min(uzs), max(uzs)
    return s
