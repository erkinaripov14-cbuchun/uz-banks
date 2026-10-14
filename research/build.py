"""research/data_rasmiy.py dagi ma'lumotdan Excel va CSV yasash.

    python research/build.py
"""
import csv
import sys
from pathlib import Path
from urllib.parse import urlparse

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

sys.path.insert(0, str(Path(__file__).parent))
from data_rasmiy import GAPS, ROWS  # noqa: E402

OUT = Path(__file__).parent / "rasmiy-2026-10-14"
HEAD = ["Bank", "Toifa", "Mahsulot", "Foiz min, %", "Foiz max, %", "Muddat", "Summa", "Valyuta",
        "Sayt", "Sana", "Izoh", "Manba havolasi"]
WIDTHS = [26, 14, 38, 11, 11, 18, 18, 9, 20, 11, 60, 50]


def rows(kind):
    out = [r for r in ROWS if r[1] == kind]
    return sorted(out, key=lambda r: (r[0], r[2], -(r[5] if r[5] is not None else r[4] or 0)))


def as_list(r):
    bank, _, cat, name, lo, hi, term, amount, cur, url, date, note = r
    host = (urlparse(url).hostname or "").removeprefix("www.")
    return [bank, cat, name, lo, hi, term, amount, cur, host, date, note, url]


def sheet(wb, title, header, data, widths):
    ws = wb.create_sheet(title)
    ws.append(header)
    for c in ws[1]:
        c.font, c.fill = Font(bold=True, color="FFFFFF"), PatternFill("solid", fgColor="1F4E78")
        c.alignment = Alignment(wrap_text=True, vertical="center")
    for row in data:
        ws.append(row)
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    for row in ws.iter_rows(min_row=2):
        for c in row:
            c.alignment = Alignment(wrap_text=True, vertical="top")
        last = row[-1]
        if isinstance(last.value, str) and last.value.startswith("http"):
            last.hyperlink, last.style = last.value, "Hyperlink"
    ws.freeze_panes = "C2"
    ws.auto_filter.ref = ws.dimensions
    return ws


def _rng(xs):
    if not xs:
        return ""
    lo = min(x[4] if x[4] is not None else x[5] for x in xs)
    hi = max(x[5] if x[5] is not None else x[4] for x in xs)
    return f"{lo:g}" if lo == hi else f"{lo:g} – {hi:g}"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    wb = Workbook()
    wb.remove(wb.active)
    for kind, title in (("K", "Kreditlar"), ("O", "Omonatlar")):
        data = [as_list(r) for r in rows(kind)]
        sheet(wb, title, HEAD, data, WIDTHS)
        with open(OUT / f"{title.lower()}.csv", "w", newline="", encoding="utf-8-sig") as f:
            csv.writer(f).writerows([HEAD, *data])

    summary = []
    for b in sorted({r[0] for r in ROWS}):
        mine = [r for r in ROWS if r[0] == b]
        k = [r for r in mine if r[1] == "K"]
        o = [r for r in mine if r[1] == "O"]
        rated = lambda xs: [x for x in xs if x[4] is not None or x[5] is not None]
        uzs = [x for x in rated(o) if x[8] == "UZS"]
        fx = [x for x in rated(o) if x[8] != "UZS"]
        site = ".".join((urlparse(mine[0][9]).hostname or "").split(".")[-2:])
        summary.append([b, len(k), _rng(rated(k)), len(o), _rng(uzs), _rng(fx), GAPS.get(b, ""), site])
    sheet(wb, "Banklar xulosasi", ["Bank", "Kredit mahsulotlari", "Kredit foizi, %", "Omonat mahsulotlari",
                                   "So'm omonat, %", "Valyuta omonat, %", "Kamchilik", "Sayt"],
          summary, [28, 11, 15, 11, 14, 14, 60, 24])
    sheet(wb, "Izoh", ["Muhim"], [[t] for t in [
        "Ma'lumot 2026-10-14 da faqat banklarning o'z rasmiy saytlaridan olindi (qidiruv har bir bank domeni bilan cheklangan).",
        "Agregatorlar (bank.uz, depozit.uz, bankxizmatlari.uz) va yangilik saytlari ishlatilmagan.",
        "Istisno: InfinBank — rasmiy sayti infinbank.com.",
        "Bank saytlari bu muhitdan to'g'ridan-to'g'ri ochilmadi; ma'lumot qidiruv tizimi indekslagan sahifalardan olingan.",
        "Ko'p sahifalarda sana yo'q — 'Sana' bo'sh bo'lsa, sahifa eski bo'lishi mumkin. Bir bank sahifalari bir-biriga zid bo'lsa, 'Izoh'da yozilgan.",
        "Kredit stavkalari ko'pincha mijozga qarab individual; omonat stavkasi kanal (ilova / filial) va foiz to'lash tartibiga bog'liq.",
        "Qaror qabul qilishdan oldin bank sayti yoki call-markazi orqali tekshiring.",
        "Yangilash: python scrape.py (bank saytlariga kirish mumkin bo'lgan kompyuterda) yoki python research/build.py.",
    ]], [140])
    wb.save(OUT / "banklar_kredit_omonat_rasmiy.xlsx")
    print(f"{OUT}/banklar_kredit_omonat_rasmiy.xlsx: {len(summary)} bank, "
          f"{len(rows('K'))} kredit, {len(rows('O'))} omonat")


if __name__ == "__main__":
    main()
