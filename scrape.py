"""O'zbekiston banklari saytlaridan kredit va omonat mahsulotlarini yig'ish.

Misollar:
    python scrape.py                          # hamma banklar, kredit + omonat
    python scrape.py --only hamkorbank,nbu    # faqat tanlangan banklar
    python scrape.py --sections deposits      # faqat omonatlar
    python scrape.py --headful --concurrency 1   # brauzerni ko'rib turish
"""
import argparse
import asyncio
import json
import os
from datetime import date
from pathlib import Path

from uzbanks.crawl import scrape_all
from uzbanks.report import write_excel, write_json


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--banks", default="banks.json", help="banklar ro'yxati (JSON)")
    ap.add_argument("--only", help="vergul bilan bank id lari, masalan: hamkorbank,nbu")
    ap.add_argument("--sections", default="credits,deposits", help="credits, deposits yoki ikkalasi")
    ap.add_argument("--lang", default="uz", help="sayt tili: uz, ru, en (bo'sh qoldirilsa hammasi)")
    ap.add_argument("--max-pages", type=int, default=40, help="har bir bo'lim uchun maksimal sahifalar")
    ap.add_argument("--concurrency", type=int, default=4, help="bir vaqtda nechta bank")
    ap.add_argument("--timeout", type=int, default=45, help="sahifa yuklanish vaqti, soniya")
    ap.add_argument("--headful", action="store_true", help="brauzer oynasini ko'rsatish")
    ap.add_argument("--out", default=f"output/{date.today().isoformat()}", help="natijalar papkasi")
    a = ap.parse_args()

    banks = json.loads(Path(a.banks).read_text(encoding="utf-8"))
    if a.only:
        ids = {x.strip() for x in a.only.split(",")}
        unknown = ids - {b["id"] for b in banks}
        if unknown:
            ap.error(f"noma'lum bank id: {', '.join(sorted(unknown))}")
        banks = [b for b in banks if b["id"] in ids]
    sections = [s.strip() for s in a.sections.split(",") if s.strip()]
    for s in sections:
        if s not in ("credits", "deposits"):
            ap.error(f"noto'g'ri bo'lim: {s}")

    results = asyncio.run(scrape_all(
        banks, sections, concurrency=a.concurrency, headless=not a.headful,
        executable_path=os.environ.get("CHROMIUM_PATH"),
        max_pages=a.max_pages, lang=a.lang or None, timeout=a.timeout * 1000,
    ))

    out = Path(a.out)
    write_json(results, out, sections)
    write_excel(results, out / "report.xlsx", sections)
    print(f"\nTayyor: {out / 'report.xlsx'}")
    for s in sections:
        print(f"  {s}: {sum(len(r[s]) for r in results)} sahifa")
    failed = [r["bank"] for r in results if not any(r[s] for s in sections)]
    if failed:
        print(f"  Ma'lumot topilmadi: {', '.join(failed)} (Excel'dagi 'Banklar' varag'ida xatolar)")


if __name__ == "__main__":
    main()
