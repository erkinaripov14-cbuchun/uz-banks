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


def test_rates_ignore_down_payment_penalty_and_early_withdrawal():
    def r(lo, hi, ctx):
        return {"min": lo, "max": hi, "context": ctx}
    credit = {"url": "https://t.uz/ipoteka", "title": "Ipoteka krediti", "kind": "product", "rate_min": 10, "rate_max": 50,
              "currencies": ["UZS"], "term_min_months": 12, "term_max_months": 240, "rates": [
                  r(17, 19, "Foiz stavkasi: yillik 17–19%"), r(25, 25, "Boshlang'ich badal 25%"),
                  r(50, 50, "jarima 50%"), r(10, 10, "qarz yuki 10%")]}
    deposit = {"url": "https://t.uz/omonat/eur", "title": "Yevro Onlayn", "kind": "product", "rate_min": 1, "rate_max": 10,
               "currencies": ["UZS", "EUR"], "rates": [r(2, 2, "yillik 2%"), r(1, 1, "muddatidan oldin yechilsa 1%")]}
    box = {"url": "https://t.uz/x", "title": "Depozit yacheykalari", "kind": "product", "rate_min": 20, "rate_max": 20, "rates": []}
    rows = convert([{"bank": "B", "scraped_at": "2026-10-14", "credits": [credit], "deposits": [deposit, box]}])
    assert [(x["name"], x["lo"], x["hi"], x["cat"], x["cur"]) for x in rows] == [
        ("Ipoteka krediti", 17, 19, "Ipoteka", "UZS"), ("Yevro Onlayn", 2, 2, "Valyuta omonat", "EUR")]


def test_listing_cards_become_products_with_segment():
    results = [{"bank": "B", "scraped_at": "2026-10-14", "credits": [
        {"url": "https://t.uz/uz/corporate/crediting/", "title": "Kreditlar", "kind": "listing", "rate_min": 18, "rate_max": 30,
         "cards": [
             {"url": "https://t.uz/uz/corporate/crediting/aylanma/", "text": "Aylanma kredit\n22% dan\n36 oygacha",
              "rate_min": 22, "rate_max": 22, "currencies": ["UZS"], "term_min_months": 36, "term_max_months": 36,
              "amount_min": None, "amount_max": None},
             {"url": "https://t.uz/uz/corporate/crediting/invest/", "text": "Invest\n18%", "rate_min": 18, "rate_max": 18,
              "currencies": ["UZS"]},
         ]},
        # bu kartochkaning o'z sahifasi o'qilgan — kartochka emas, sahifa olinadi
        {"url": "https://t.uz/uz/corporate/crediting/invest", "title": "Invest krediti", "kind": "product",
         "rate_min": 19, "rate_max": 19, "currencies": ["UZS"], "rates": [{"min": 19, "max": 19, "context": "yillik 19%"}]},
    ]}]
    rows = convert(results)
    assert sorted((r["name"], r["lo"], r["segment"]) for r in rows) == [
        ("Aylanma kredit", 22, "yuridik"), ("Invest krediti", 19, "yuridik")]


def test_stricter_plausibility():
    from live import _plausible
    assert not _plausible("O", 6, 18, "USD")        # dollar omonat 18% — so'mdagi stavka aralashgan
    assert not _plausible("K", 6, 19, "UZS", "Iste'mol")
    assert not _plausible("K", 50, 50, "UZS", "Ipoteka")
    assert _plausible("K", 0, 0, "UZS", "Avtokredit")
    assert _plausible("O", 7, 7, "USD") and _plausible("O", 20, 22)
