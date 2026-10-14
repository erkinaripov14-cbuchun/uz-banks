"""Lokal test-sayt ustida skraperni to'liq ishlatish (internet kerak emas)."""
import asyncio
import functools
import http.server
import os
import threading
from pathlib import Path

import pytest

from uzbanks.crawl import scrape_all
from uzbanks.report import write_excel, write_json

SITE = Path(__file__).parent / "site"


@pytest.fixture(scope="module")
def server():
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(SITE))
    handler.log_message = lambda *a: None
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{srv.server_address[1]}"
    srv.shutdown()


def test_scrape_local_site(server, tmp_path):
    bank = {"id": "test", "name": "Test bank", "site": server}
    sections = ["credits", "deposits"]
    [r] = asyncio.run(scrape_all([bank], sections, executable_path=os.environ.get("CHROMIUM_PATH"), timeout=15000))

    credits = {p["title"]: p for p in r["credits"]}
    assert {"Jismoniy shaxslar uchun kreditlar", "Avtokredit", "Ipoteka krediti", "Mikroqarz"} <= set(credits)
    listing = credits["Jismoniy shaxslar uchun kreditlar"]
    assert listing["kind"] == "listing" and len(listing["cards"]) == 3
    assert [c["rate_min"] for c in listing["cards"]] == [24, 17, 28]
    assert (credits["Ipoteka krediti"]["rate_min"], credits["Ipoteka krediti"]["rate_max"]) == (17, 19)
    avto = credits["Avtokredit"]
    assert (avto["rate_min"], avto["rate_max"], avto["term_max_months"], avto["amount_max"]) == (24, 26, 60, 800e6)
    assert avto["tables"][0][0] == ["Muddat", "Stavka"]
    assert "Imtiyozli davr" in avto["text"]  # yashirin tab matni
    assert not any("news" in p["url"] or "/ru/" in p["url"] for p in r["credits"])

    yillik = next(p for p in r["deposits"] if p["title"] == "Yillik omonat")
    assert yillik["rate_max"] == 22 and yillik["currencies"] == ["USD", "UZS"]

    write_json([r], tmp_path, sections)
    write_excel([r], tmp_path / "report.xlsx", sections)
    assert (tmp_path / "report.xlsx").stat().st_size > 0
