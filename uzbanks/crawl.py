"""Playwright bilan bank saytini aylanib chiqib, kredit va omonat sahifalarini yig'ish."""
import asyncio
import re
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse, urlunparse

from .parse import classify_link, summarize

LANGS = {"uz", "ru", "en", "oz", "uzc", "uz-cyrl", "uz-latn", "kr", "cy"}

# Sahifadagi barcha havolalar, ular joylashgan "kartochka" matni bilan birga
JS_LINKS = r"""
() => Array.from(document.querySelectorAll('a[href]')).map(a => {
  let card = a, best = (a.innerText || '').trim();
  for (let i = 0, el = a.parentElement; i < 6 && el && el !== document.body; i++, el = el.parentElement) {
    const t = (el.innerText || '').trim();
    if (t.length > 900) break;
    // boshqa sahifaga havola ham bor konteyner — bu kartochka emas, ro'yxat
    const other = Array.from(el.querySelectorAll('a[href]')).some(x => x.href.split('#')[0] !== a.href.split('#')[0]);
    if (other) break;
    card = el; best = t;
  }
  return {href: a.href, text: (a.innerText || a.title || a.getAttribute('aria-label') || '').trim(), card: best};
})
"""

# Ko'rinadigan matn + yashirin tab/akkordeon panellari matni
JS_TEXT = r"""
() => {
  const root = document.querySelector('main') || document.body;
  let text = root.innerText || '';
  const hidden = document.querySelectorAll('[role=tabpanel], .tab-pane, details, [class*=accordion], [class*=collapse], [class*=tab-content]');
  for (const el of hidden) {
    if (!el.offsetParent) text += '\n' + (el.textContent || '').replace(/\s+/g, ' ');
  }
  return text;
}
"""

JS_TABLES = r"""
() => Array.from(document.querySelectorAll('table')).map(t =>
  Array.from(t.rows).map(r => Array.from(r.cells).map(c => (c.innerText || c.textContent || '').trim().replace(/\s+/g, ' ')))
).filter(t => t.length > 1)
"""

JS_TITLE = r"""
() => ((document.querySelector('h1') || {}).innerText || document.title || '').trim()
"""


def _host(url):
    h = urlparse(url).hostname or ""
    return h[4:] if h.startswith("www.") else h


def normalize(url):
    p = urlparse(url)
    path = re.sub(r"/+$", "", p.path) or "/"
    return urlunparse((p.scheme, (p.hostname or "").removeprefix("www."), path, "", p.query, ""))


def lang_of(url):
    seg = urlparse(url).path.strip("/").split("/")[0].lower()
    return seg if seg in LANGS else None


def same_site(url, site):
    a, b = _host(url), _host(site)
    return a == b or a.endswith("." + b)


async def _goto(page, url, timeout):
    await page.goto(url, wait_until="domcontentloaded", timeout=timeout)
    try:
        await page.wait_for_load_state("networkidle", timeout=min(timeout, 15000))
    except Exception:
        pass
    # lazy-load qilinadigan kartochkalar uchun pastgacha aylantirish
    for _ in range(4):
        await page.mouse.wheel(0, 4000)
        await page.wait_for_timeout(400)


def _wanted(url, site, lang):
    if not same_site(url, site) or not url.startswith("http"):
        return False
    lg = lang_of(url)
    return lg is None or lang is None or lg == lang or (lang == "uz" and lg in {"uz-latn", "oz"})


async def scrape_bank(browser, bank, sections, max_pages=40, lang="uz", timeout=45000, log=print):
    """Bitta bank: {'bank':..., 'credits': [...], 'deposits': [...], 'errors': [...]}"""
    site = bank["site"]
    result = {"bank_id": bank["id"], "bank": bank["name"], "site": site,
              "scraped_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
              "errors": []}
    for s in sections:
        result[s] = []

    ctx = await browser.new_context(
        locale="uz-UZ" if lang == "uz" else "ru-RU",
        user_agent=("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/129.0 Safari/537.36"),
        viewport={"width": 1366, "height": 900},
        ignore_https_errors=True,
    )
    page = await ctx.new_page()
    try:
        queues = {s: [] for s in sections}
        for s in sections:  # banks.json da qo'lda berilgan URL lar
            queues[s] += [urljoin(site + "/", u) for u in bank.get(s, [])]

        # Bosh sahifa (va til prefiksli varianti) dan bo'lim havolalarini topish
        links, ok = [], False
        starts = [site] + ([site.rstrip("/") + f"/{lang}"] if lang else [])
        for url in starts:
            try:
                await _goto(page, url, timeout)
                links += await page.evaluate(JS_LINKS)
                ok = True
            except Exception as e:
                result["errors"].append(f"{url}: {e.__class__.__name__}: {str(e).splitlines()[0]}")
        if not ok:
            return result

        found = {s: [] for s in sections}
        for ln in links:
            sec = classify_link(ln["href"], ln["text"])
            if sec in found and _wanted(ln["href"], site, None):
                found[sec].append(ln["href"])
        # Tanlangan tilda havola bo'lmasa, sayt qaysi tilda bo'lsa o'shani olamiz
        if lang and not any(_wanted(u, site, lang) for v in found.values() for u in v):
            lang = None
        for s in sections:
            queues[s] += [u for u in found[s] if _wanted(u, site, lang)]

        for sec in sections:
            seen, todo, n = set(), list(queues[sec]), 0
            while todo and n < max_pages:
                url = todo.pop(0)
                key = normalize(url)
                if key in seen:
                    continue
                seen.add(key)
                n += 1
                try:
                    await _goto(page, url, timeout)
                    title = await page.evaluate(JS_TITLE)
                    text = await page.evaluate(JS_TEXT)
                    tables = await page.evaluate(JS_TABLES)
                    links = await page.evaluate(JS_LINKS)
                except Exception as e:
                    result["errors"].append(f"{url}: {e.__class__.__name__}: {str(e).splitlines()[0]}")
                    continue

                base_path = urlparse(page.url).path.rstrip("/")
                cards, children = [], []
                for ln in links:
                    href = ln["href"].split("#")[0]
                    if not _wanted(href, site, lang) or normalize(href) == normalize(page.url):
                        continue
                    child_path = urlparse(href).path.rstrip("/")
                    is_child = base_path and child_path.startswith(base_path + "/")
                    if is_child or classify_link(href, ln["text"]) == sec:
                        children.append(href)
                        if is_child and ln["card"]:
                            cards.append({"url": href, "text": ln["card"], **_short(summarize(ln["card"]))})
                todo += children

                full = summarize(text + "\n" + "\n".join(" | ".join(r) for t in tables for r in t))
                result[sec].append({
                    "url": page.url, "title": title,
                    "kind": "listing" if len(cards) >= 2 else "product",
                    **full,
                    "cards": _dedupe_cards(cards),
                    "tables": tables,
                    "text": text[:20000],
                })
                log(f"  [{bank['id']}] {sec}: {title[:60]!r} {page.url}")
    except Exception as e:
        result["errors"].append(f"{e.__class__.__name__}: {e}")
    finally:
        await ctx.close()
    return result


def _short(s):
    return {k: s[k] for k in ("rate_min", "rate_max", "term_min_months", "term_max_months",
                              "amount_min", "amount_max", "currencies")}


def _dedupe_cards(cards):
    out = {}
    for c in cards:
        key = normalize(c["url"])
        if key not in out or len(c["text"]) > len(out[key]["text"]):
            out[key] = c
    return list(out.values())


async def scrape_all(banks, sections, concurrency=4, headless=True, executable_path=None, **kw):
    from playwright.async_api import async_playwright

    sem = asyncio.Semaphore(concurrency)
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=headless, executable_path=executable_path)

        async def one(bank):
            async with sem:
                print(f"→ {bank['name']} ({bank['site']})")
                r = await scrape_bank(browser, bank, sections, **kw)
                counts = ", ".join(f"{s}: {len(r[s])}" for s in sections)
                print(f"✓ {bank['name']}: {counts}" + (f", xatolar: {len(r['errors'])}" if r["errors"] else ""))
                return r

        results = await asyncio.gather(*(one(b) for b in banks))
        await browser.close()
    return results
