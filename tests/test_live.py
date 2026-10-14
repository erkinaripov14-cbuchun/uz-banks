import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "research"))
from live import convert  # noqa: E402


def test_convert_keeps_product_pages_only():
    results = [{"bank": "Test bank", "scraped_at": "2026-10-14T10:00:00+00:00", "credits": [
        {"url": "https://t.uz/uz/kreditlar", "title": "Kreditlar", "kind": "listing", "rate_min": 17, "rate_max": 28},
        {"url": "https://t.uz/uz/kreditlar/avto", "title": "Avtokredit", "kind": "product", "rate_min": 24, "rate_max": 26,
         "term_min_months": 12, "term_max_months": 60, "amount_min": 5e7, "amount_max": 8e8, "currencies": ["UZS"]},
        {"url": "https://t.uz/uz/kreditlar/x", "title": "Matnsiz", "kind": "product", "rate_min": None, "rate_max": None},
    ], "deposits": [
        {"url": "https://t.uz/uz/omonat/usd", "title": "Dollar omonati", "kind": "product", "rate_min": 6, "rate_max": 6,
         "term_min_months": 13, "term_max_months": 13, "amount_min": None, "amount_max": None, "currencies": ["USD"]},
    ]}]
    rows = convert(results)
    assert [(r["type"], r["cat"], r["name"]) for r in rows] == [
        ("K", "Avtokredit", "Avtokredit"), ("O", "Valyuta omonat", "Dollar omonati")]
    avto, usd = rows
    assert (avto["lo"], avto["hi"], avto["term"], avto["amount"], avto["date"]) == (24, 26, "1 yil – 5 yil", "50 mln – 800 mln", "2026-10-14")
    assert (usd["cur"], usd["term"]) == ("USD", "13 oygacha")


def test_convert_drops_generic_pages_noise_and_duplicates():
    page = lambda title, lo, hi, url="https://t.uz/a": {"url": url, "title": title, "kind": "product",
                                                        "rate_min": lo, "rate_max": hi, "currencies": ["UZS"]}
    results = [{"bank": "B", "scraped_at": "2026-10-14", "credits": [
        page("Kalkulyator", 20, 30), page("Kreditlar", 20, 30), page("404", 20, 30),
        page("Avtokredit", 1, 2),            # matndagi shovqin, kredit foizi emas
        page("Avtokredit", 24, 26), page("Avtokredit", 24, 26, "https://t.uz/b"),  # takror
        page("Uzavto 0%", 0, 0),
    ], "deposits": [page("Omonat", 22, 22), page("Yillik omonat", 22, 80)]}]
    rows = convert(results)
    assert [(r["name"], r["lo"], r["hi"]) for r in rows] == [("Avtokredit", 24, 26), ("Uzavto 0%", 0, 0)]
