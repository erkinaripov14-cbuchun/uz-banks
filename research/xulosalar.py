"""Asosiy xulosalar: matn (qo'lda yozilgan) va reyting jadvallari (data_rasmiy.py dan hisoblanadi)."""
import re

from data_rasmiy import ROWS

KEY_POINTS = [
    ("So'm omonatlar",
     "Ko'pchilik banklarda yillik 16–22%. Eng yuqorisi: Garant bank «Red Line» — 25% (13 oy), "
     "Anorbank «SMART 3.0» va Asia Alliance Bank «Strategiya online» — 23% (24 oy), "
     "Trastbank «Onlayn-Trast Imkon» (24 oy) va Tenge Bank «Qulay onlayn» (13 oy) — 22%."),
    ("Qanday ochish foydaliroq",
     "Ilova orqali ochilgan omonat odatda filialdagidan 0.5–1% yuqori (NBU, Ipoteka-bank, Mikrokreditbank, "
     "Asakabank). Foiz muddat oxirida to'lansa, oyma-oy to'lovdan yuqori bo'ladi "
     "(Ipoteka-bank DaroMax: 21% va 18.5%)."),
    ("Muddatidan oldin yechish",
     "Deyarli hamma bankda foiz keskin tushadi yoki umuman to'lanmaydi "
     "(masalan, Mikrokreditbank «Omonat karta»: 3 oygacha 0%). TBC Bank muddatli omonatini muddatidan oldin yechib bo'lmaydi."),
    ("Dollar omonatlar",
     "Asosan 5–7.5%. Eng yuqorisi Universal bank «Invest 7.5» — 7.5% (18 oy, 200 $ dan). 7% — Davr bank «Optimal» "
     "va Turonbank «Turon Oltin» (100 $ dan), Trastbank, Ipak Yo'li, Asia Alliance (onlayn), Anorbank «ELITE» (10 000 $ dan). "
     "Eng pasti: Ziraat 1–2%, SQB 3%."),
    ("Ipoteka",
     "17% dan boshlanadi: Hamkorbank, Agrobank «Xonadon plyus», Ipoteka-bank; subsidiyali «Oson» — 17.5% (badal 15%). "
     "Odatda 20–24%, muddat 10–20 yil, boshlang'ich badal 15–26%. Eng qimmati Poytaxt bank «Maskan» — 28–32%."),
    ("Avtokredit",
     "Oddiy stavka 21–27%. Ayrim modellar uchun 0% aksiyalar bor (Hamkorbank, SQB «Uzavto-Imkon», "
     "Asia Alliance «Onix va Tracker», Garant bank) — odatda faqat hamkor dilerlar va aniq modellar uchun. "
     "OFB «BYD Special Plus» — 12.5% dan."),
    ("Mikroqarz",
     "Stavkalar eng keng oraliqda: 20–49%. Arzonlari: OFB «Green» — 20%, Ipak Yo'li garovli — 21.9% dan, "
     "SQB ish haqi loyihasi — 22% dan, Hamkorbank onlayn — 23% dan. Qimmatlari: TBC va Tenge — 49% gacha, "
     "Anorbank — 44%, Davr bank — 33–38%, Octobank — 37.9%. Uzum Bank: 30 kunga 0%, keyin to'lovlarga bo'linadi."),
    ("Iste'mol va ta'lim krediti",
     "Iste'mol krediti asosan 22–32% (SQB «Yangicha» — 21.99% dan, ish haqi loyihasi mijozlariga). "
     "Ta'lim krediti eng arzon: Hamkorbank va BRB — 14%, 7 yilgacha."),
    ("Biznes krediti",
     "Imtiyozli dasturlar 10–19%: BRB «Invest» — 10% dan, NBU yoshlar uchun — 14%, SQB «Yosh tadbirkor» — 18%, "
     "InfinBank — 18.99%. Oddiy biznes kreditlari 21–30%."),
    ("Umumiy qoida",
     "Garov, rasmiy daromad yoki bankda ish haqi loyihasi bo'lsa, kredit stavkasi sezilarli past. "
     "Garovsiz onlayn mikroqarz eng qimmat kredit turi."),
]


def _hi(r):
    return r[5] if r[5] is not None else r[4]


def _lo(r):
    return r[4] if r[4] is not None else r[5]


def _stale(r):
    """2025 yildan oldingi yoki arxivdagi sahifalar reytingga kiritilmaydi."""
    m = re.match(r"(\d{4})", r[10] or "")
    return (m and int(m.group(1)) < 2025) or "arxiv" in r[11].lower()


def _fmt(lo, hi):
    return f"{lo:g}" if lo == hi or hi is None else f"{lo:g} – {hi:g}"


def top_deposits(currency_uzs, n):
    xs = [r for r in ROWS if r[1] == "O" and _hi(r) and not _stale(r) and (r[8] == "UZS") == currency_uzs]
    xs.sort(key=lambda r: (-_hi(r), r[0]))
    return [[r[0], r[3], _fmt(_lo(r), _hi(r)), r[6], r[7], r[9]] for r in xs[:n]]


def cheapest(category, n, reverse=False):
    xs = [r for r in ROWS if r[1] == "K" and r[2] == category and _lo(r) and not _stale(r)]
    xs.sort(key=(lambda r: (-_hi(r), r[0])) if reverse else (lambda r: (_lo(r), r[0])))
    return [[r[0], r[3], _fmt(_lo(r), _hi(r)), r[6], r[7], r[9]] for r in xs[:n]]


def tables():
    head = ["Bank", "Mahsulot", "Foiz, %", "Muddat", "Summa", "Havola"]
    return [
        ("Eng yuqori so'm omonatlar", head, top_deposits(True, 10)),
        ("Eng yuqori valyuta omonatlar", head, top_deposits(False, 8)),
        ("Eng arzon ipoteka", head, cheapest("Ipoteka", 6)),
        ("Eng arzon avtokredit (0% aksiyalarsiz)", head, cheapest("Avtokredit", 6)),
        ("Eng arzon mikroqarz (0% aksiyalarsiz)", head, cheapest("Mikroqarz", 8)),
        ("Eng qimmat mikroqarz", head, cheapest("Mikroqarz", 6, reverse=True)),
        ("Eng arzon iste'mol krediti", head, cheapest("Iste'mol", 5)),
        ("Eng arzon biznes krediti", head, cheapest("Biznes", 6)),
    ]


NOTES = [
    "Reytinglarga 2025 yildan oldingi va arxivdagi sahifalar kiritilmagan (masalan, Kapitalbank «Maksimal kapital» 25% — 2023).",
    "Ma'lumot faqat bank saytlaridan, qidiruv tizimi orqali olingan; ko'p sahifalarda sana yo'q.",
    "Istisno: Asakabank sayti mahsulotlarni faqat O'zbekistondan ko'rsatadi, shuning uchun uning foizlari bank.uz agregatoridan olingan (har bir qatorda belgilangan).",
    "Kredit stavkasi mijozga qarab individual belgilanadi — jadvaldagi raqam boshlang'ich stavka.",
    "Muhim qarordan oldin stavkani bankning o'zidan tekshiring.",
]


def _as_dict(r):
    return {"bank": r[0], "name": r[3], "lo": r[4], "hi": r[5], "term": r[6], "amount": r[7], "url": r[9]}


def rankings():
    """Saytdagi reyting kartochkalari uchun: tables() bilan bir xil tartib, lekin xom qiymatlar bilan."""
    dep = lambda uzs: sorted([r for r in ROWS if r[1] == "O" and _hi(r) and not _stale(r) and (r[8] == "UZS") == uzs],
                             key=lambda r: (-_hi(r), r[0]))
    cre = lambda cat, rev=False: sorted([r for r in ROWS if r[1] == "K" and r[2] == cat and _lo(r) and not _stale(r)],
                                        key=(lambda r: (-_hi(r), r[0])) if rev else (lambda r: (_lo(r), r[0])))
    spec = [("Eng yuqori so'm omonatlar", "O", dep(True)[:10]),
            ("Eng yuqori valyuta omonatlar", "O", dep(False)[:8]),
            ("Eng arzon ipoteka", "K", cre("Ipoteka")[:6]),
            ("Eng arzon avtokredit (0% aksiyalarsiz)", "K", cre("Avtokredit")[:6]),
            ("Eng arzon mikroqarz (0% aksiyalarsiz)", "K", cre("Mikroqarz")[:8]),
            ("Eng qimmat mikroqarz", "K", cre("Mikroqarz", True)[:6]),
            ("Eng arzon iste'mol krediti", "K", cre("Iste'mol")[:5]),
            ("Eng arzon biznes krediti", "K", cre("Biznes")[:6])]
    return [{"title": t, "kind": k, "rows": [_as_dict(r) for r in rs]} for t, k, rs in spec]


def is_stale(r):
    return bool(_stale(r))
