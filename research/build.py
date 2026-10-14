"""research/data_rasmiy.py dagi ma'lumotdan Excel va CSV yasash.

    python research/build.py
"""
import csv
import json
from collections import Counter
import sys
from pathlib import Path
from urllib.parse import urlparse

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

sys.path.insert(0, str(Path(__file__).parent))
from data_rasmiy import GAPS, ROWS  # noqa: E402
import xulosalar  # noqa: E402

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


def summary_sheet(wb):
    ws = wb.create_sheet("Xulosalar", 0)
    bold, title = Font(bold=True), Font(bold=True, size=14)
    head_font, head_fill = Font(bold=True, color="FFFFFF"), PatternFill("solid", fgColor="1F4E78")
    wrap = Alignment(wrap_text=True, vertical="top")
    ws.append(["O'zbekiston banklari: kreditlar va omonatlar — asosiy xulosalar"])
    ws["A1"].font = title
    ws.append([f"Manba: faqat bank saytlari, 2026-10-14. {len(ROWS)} ta mahsulot, {len({r[0] for r in ROWS})} ta bank."])
    ws.append([])
    for topic, text in xulosalar.KEY_POINTS:
        ws.append([topic, text])
        r = ws.max_row
        ws.cell(r, 1).font = bold
        ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=6)
        ws.cell(r, 2).alignment = wrap
        ws.row_dimensions[r].height = 15 * (len(text) // 95 + 1)
    for name, header, data in xulosalar.tables():
        ws.append([])
        ws.append([name])
        ws.cell(ws.max_row, 1).font = Font(bold=True, size=12)
        ws.append(header)
        for c in ws[ws.max_row]:
            c.font, c.fill = head_font, head_fill
        for row in data:
            ws.append(row)
            link = ws.cell(ws.max_row, len(row))
            link.hyperlink, link.style = link.value, "Hyperlink"
            for c in ws[ws.max_row][:-1]:
                c.alignment = wrap
    ws.append([])
    ws.append(["Eslatmalar"])
    ws.cell(ws.max_row, 1).font = bold
    for t in xulosalar.NOTES:
        ws.append(["", t])
    for i, w in enumerate([28, 40, 12, 18, 20, 55], 1):
        ws.column_dimensions[get_column_letter(i)].width = w


def write_markdown(path):
    lines = ["# O'zbekiston banklari: kreditlar va omonatlar — asosiy xulosalar", "",
             f"Manba: faqat bank saytlari, 2026-10-14. {len(ROWS)} ta mahsulot, "
             f"{len({r[0] for r in ROWS})} ta bank. To'liq jadval: "
             "[banklar_kredit_omonat_rasmiy.xlsx](banklar_kredit_omonat_rasmiy.xlsx).", "",
             "## Asosiy xulosalar", ""]
    lines += [f"- **{t}.** {x}" for t, x in xulosalar.KEY_POINTS]
    for name, header, data in xulosalar.tables():
        lines += ["", f"## {name}", "", "| " + " | ".join(header[:-1]) + " |",
                  "|" + "---|" * (len(header) - 1)]
        for r in data:
            cells = [str(c) for c in r[:-1]]
            cells[1] = f"[{cells[1]}]({r[-1]})"
            lines.append("| " + " | ".join(cells) + " |")
    lines += ["", "## Eslatmalar", ""] + [f"- {t}" for t in xulosalar.NOTES]
    lines += ["", "## Ma'lumot topilmagan joylar", ""] + [f"- **{b}:** {t}" for b, t in sorted(GAPS.items())]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


LIVE = Path(__file__).parent / "live" / "latest.json"
PAGES_URL = "https://erkinaripov14-cbuchun.github.io/uz-banks/"
EXCEL_NAME = "banklar_kredit_omonat.xlsx"
SITE_DIRS = [Path(__file__).parent.parent / "site", Path(__file__).parent.parent / "docs"]


def write_site():
    """site/index.html — Artifact uchun (skeletsiz); docs/index.html — GitHub Pages uchun to'liq hujjat."""
    sites = {}
    for b in {r[0] for r in ROWS}:
        hosts = Counter(".".join((urlparse(r[9]).hostname or "").split(".")[-2:]) for r in ROWS if r[0] == b)
        sites[b] = hosts.most_common(1)[0][0]
    data = {
        "generated": "2026-10-14",
        "rows": [{"bank": r[0], "type": r[1], "cat": r[2], "name": r[3], "lo": r[4], "hi": r[5], "term": r[6],
                  "amount": r[7], "cur": r[8], "url": r[9], "date": r[10], "note": r[11],
                  "stale": xulosalar.is_stale(r)} for r in ROWS],
        "points": xulosalar.KEY_POINTS,
        "rankings": xulosalar.rankings(),
        "notes": xulosalar.NOTES,
        "gaps": GAPS,
        "sites": sites,
        "repo": "erkinaripov14-cbuchun/uz-banks",
        "excel": PAGES_URL + EXCEL_NAME,
        # Administrator paroli SHA-256 xeshi (parolning o'zi repoda saqlanmaydi)
        "adminHash": "6ec2f9f12dba6ee672f9e6c5d15daf4fdd036b59949138e61bcc521065cc2da1",
        "live": json.loads(LIVE.read_text(encoding="utf-8")) if LIVE.exists() else None,
    }
    blob = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    page = (Path(__file__).parent / "site_template.html").read_text(encoding="utf-8").replace("/*DATA*/null", blob)
    SITE_DIRS[0].mkdir(exist_ok=True)
    (SITE_DIRS[0] / "index.html").write_text(page, encoding="utf-8")
    SITE_DIRS[1].mkdir(exist_ok=True)
    full = ('<!doctype html>\n<html lang="uz">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
            '<style>[hidden]{display:none!important} body{margin:0} img{max-width:100%}</style>\n'
            + page.replace("<header class=\"top\">", "</head>\n<body>\n<header class=\"top\">", 1)
            + "\n</body>\n</html>\n")
    (SITE_DIRS[1] / "index.html").write_text(full, encoding="utf-8")
    # Saytdagi "Excel yuklab olish" tugmasi uchun nusxa (GitHub Pages docs/ dan beradi)
    (SITE_DIRS[1] / EXCEL_NAME).write_bytes((OUT / "banklar_kredit_omonat_rasmiy.xlsx").read_bytes())


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    wb = Workbook()
    wb.remove(wb.active)
    summary_sheet(wb)
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
    write_markdown(OUT / "XULOSALAR.md")
    write_site()
    print(f"{OUT}/banklar_kredit_omonat_rasmiy.xlsx: {len(summary)} bank, "
          f"{len(rows('K'))} kredit, {len(rows('O'))} omonat")


if __name__ == "__main__":
    main()
