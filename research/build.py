"""research/data_*.py dagi qo'lda yig'ilgan ma'lumotdan Excel va CSV yasash.

    python research/build.py
"""
import csv
import sys
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

sys.path.insert(0, str(Path(__file__).parent))
from data_2026_10_14 import GAPS, MARKET, ROWS  # noqa: E402

OUT = Path(__file__).parent / "2026-10-14"
HEAD = ["Bank", "Toifa", "Mahsulot", "Foiz min, %", "Foiz max, %", "Muddat", "Summa", "Valyuta",
        "Manba turi", "Manba sanasi", "Izoh", "Manba havolasi"]
WIDTHS = [26, 14, 38, 11, 11, 18, 16, 9, 11, 13, 55, 50]
FILL = {"Rasmiy": "E2EFDA", "MB": "DDEBF7", "OAV": "FFF2CC", "Agregator": "FCE4D6"}


def rows(kind):
    out = [r for r in ROWS if r[1] == kind]
    return sorted(out, key=lambda r: (r[0], r[2], -(r[5] or r[4] or 0)))


def as_list(r):
    bank, _, cat, name, lo, hi, term, amount, cur, src, url, date, note = r
    return [bank, cat, name, lo, hi, term, amount, cur, src, date, note, url]


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


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    wb = Workbook()
    wb.remove(wb.active)
    for kind, title in (("K", "Kreditlar"), ("O", "Omonatlar")):
        data = [as_list(r) for r in rows(kind)]
        ws = sheet(wb, title, HEAD, data, WIDTHS)
        for row in ws.iter_rows(min_row=2):
            color = FILL.get(row[8].value)
            if color:
                row[8].fill = PatternFill("solid", fgColor=color)
        with open(OUT / f"{title.lower()}.csv", "w", newline="", encoding="utf-8-sig") as f:
            csv.writer(f).writerows([HEAD, *data])

    banks = sorted({r[0] for r in ROWS} | set(GAPS))
    summary = []
    for b in banks:
        k = [r for r in ROWS if r[0] == b and r[1] == "K" and (r[4] or r[5])]
        o = [r for r in ROWS if r[0] == b and r[1] == "O" and r[8] == "UZS" and (r[4] or r[5])]
        rng = lambda xs: (f"{min(x[4] if x[4] is not None else x[5] for x in xs):g} – "
                          f"{max(x[5] if x[5] is not None else x[4] for x in xs):g}") if xs else ""
        summary.append([b, len([r for r in ROWS if r[0] == b and r[1] == "K"]), rng(k),
                        len([r for r in ROWS if r[0] == b and r[1] == "O"]), rng(o), GAPS.get(b, "")])
    sheet(wb, "Banklar xulosasi", ["Bank", "Kredit mahsulotlari", "Kredit foizi, %", "Omonat mahsulotlari",
                                   "So'm omonat foizi, %", "Kamchilik"], summary, [28, 12, 16, 12, 16, 60])
    sheet(wb, "Bozor", ["Ko'rsatkich", "Qiymat", "Manba sanasi", "Manba havolasi"],
          [[a, b, d, c] for a, b, c, d in MARKET], [36, 50, 13, 60])
    sheet(wb, "Izoh", ["Muhim"], [[t] for t in [
        "Ma'lumot 2026-10-14 da internet qidiruvi orqali yig'ildi; bank saytlari skraper bilan to'g'ridan-to'g'ri o'qilmagan.",
        "Manba turi: Rasmiy — bank sayti; MB — Markaziy bank ma'lumoti; OAV — spot.uz, pravilno.uz, gazeta.uz kabi nashrlar; Agregator — bank.uz, depozit.uz, bankxizmatlari.uz.",
        "Ko'p sahifalarda sana ko'rsatilmagan — bunday qatorlarda 'Manba sanasi' bo'sh. Ular eskirgan bo'lishi mumkin.",
        "Bir mahsulot uchun manbalar ziddiyatli bo'lsa, 'Izoh' ustunida yozilgan.",
        "Kredit stavkalari ko'pincha qarz oluvchiga qarab individual belgilanadi.",
        "Omonat stavkasi ochish kanaliga (ilova / filial) va foiz to'lash tartibiga qarab farq qiladi.",
        "Qaror qabul qilishdan oldin bank saytidan yoki call-markazidan tekshiring.",
        "To'liq va yangi ma'lumot uchun: python scrape.py (bank saytlariga kirish mumkin bo'lgan kompyuterda).",
    ]], [140])
    wb.save(OUT / "banklar_kredit_omonat.xlsx")
    k, o = len(rows("K")), len(rows("O"))
    print(f"{OUT}/banklar_kredit_omonat.xlsx: {len(banks)} bank, {k} kredit, {o} omonat")


if __name__ == "__main__":
    main()
