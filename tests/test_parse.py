from uzbanks.parse import classify_link, extract_amounts, extract_rates, extract_terms, summarize


def test_rates():
    r = extract_rates("yillik 24% dan 26% gacha")
    assert (r[0]["min"], r[0]["max"]) == (24, 26)
    r = extract_rates("от 18,5 до 22 % годовых")
    assert (r[0]["min"], r[0]["max"]) == (18.5, 22)
    assert [x["min"] for x in extract_rates("17–19 %")] == [17]


def test_terms():
    t = extract_terms("12 dan 60 oygacha")[0]
    assert (t["min_months"], t["max_months"]) == (12, 60)
    assert extract_terms("20 yilgacha")[0]["max_months"] == 240
    assert extract_terms("до 36 месяцев")[0]["max_months"] == 36
    assert extract_terms("2026 yil") == []


def test_amounts():
    a = extract_amounts("50 mln so'mdan 800 mln so'mgacha")
    assert [x["value"] for x in a] == [50e6, 800e6]
    assert extract_amounts("1 000 000 сум")[0]["value"] == 1e6
    assert extract_amounts("100 USD")[0]["currency"] == "USD"


def test_classify():
    assert classify_link("https://b.uz/uz/kreditlar", "Kreditlar") == "credits"
    assert classify_link("https://b.uz/ru/vklady", "Вклады") == "deposits"
    assert classify_link("https://b.uz/uz/news/kredit", "Yangilik") is None


def test_summary():
    s = summarize("Avtokredit: 24% dan 26% gacha, 60 oygacha, 800 mln so'm")
    assert (s["rate_min"], s["rate_max"], s["term_max_months"], s["amount_max"]) == (24, 26, 60, 800e6)


def test_skip_and_business_urls():
    from uzbanks.crawl import _wanted
    site = "https://bank.uz"
    assert _wanted("https://bank.uz/uz/private/crediting/avto/", site, "uz")
    assert _wanted("https://www.bank.uz/uz/private/deposit/x", site, "uz")
    assert not _wanted("https://bank.uz/uz/search/?q=Kredit", site, "uz")
    assert not _wanted("https://bank.uz/uz/private/crediting/request/?credit=X", site, "uz")
    assert not _wanted("https://bank.uz/uz/services/calculators/", site, "uz")
    assert not _wanted("https://bank.uz/uz/private/deposit/?currency=USD&filter=yes", site, "uz")
    assert not _wanted("https://bank.uz/uz/corporate/crediting/", site, "uz")
    assert not _wanted("https://bank.uz/uz/small-business/deposits/", site, "uz")
    assert not _wanted("https://cabinet.bank.uz/", site, "uz")
    assert not _wanted("https://bank.uz/oz/private/deposit/", site, "uz")
    assert not _wanted("https://bank.uz/qr/private/crediting/", site, "uz")


def test_repeated_titles_fall_back_to_document_title():
    from uzbanks.crawl import _fix_repeated_titles
    r = {"credits": [{"title": "Xizmat sifatini baholang", "doc_title": f"Kredit {i}"} for i in range(3)]
                    + [{"title": "Avtokredit", "doc_title": "Avtokredit"}]}
    _fix_repeated_titles(r, ["credits"])
    assert [p["title"] for p in r["credits"]] == ["Kredit 0", "Kredit 1", "Kredit 2", "Avtokredit"]
