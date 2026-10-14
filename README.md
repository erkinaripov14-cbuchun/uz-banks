# uz-banks — O'zbekiston banklarining kredit va omonatlari

32 ta O'zbekiston bankining kredit va omonat mahsulotlari: foiz, muddat, summa va valyuta —
faqat bankning o'z saytidan.

**Sayt: https://erkinaripov14-cbuchun.github.io/uz-banks/**

## Natijalar

| Fayl | Nima bor |
|---|---|
| [**docs/index.html**](docs/index.html) | Sayt: xulosalar, reytinglar, qidiruv va filtrli jadvallar, banklar kartochkalari |
| [**XULOSALAR.md**](research/rasmiy-2026-10-14/XULOSALAR.md) | Asosiy xulosalar va reytinglar: eng yuqori omonatlar, eng arzon kreditlar |
| [banklar_kredit_omonat_rasmiy.xlsx](research/rasmiy-2026-10-14/banklar_kredit_omonat_rasmiy.xlsx) | To'liq jadval: Xulosalar, Kreditlar (113), Omonatlar (103), Banklar xulosasi |
| [kreditlar.csv](research/rasmiy-2026-10-14/kreditlar.csv), [omonatlar.csv](research/rasmiy-2026-10-14/omonatlar.csv) | Shu ma'lumot CSV da |

Qisqacha (2026-10-14 holatiga):

- **So'm omonatlar** — asosan 16–22%; eng yuqorisi Garant bank «Red Line» 25% (13 oy), Anorbank «SMART 3.0» va Asia Alliance «Strategiya online» 23% (24 oy).
- **Dollar omonatlar** — 5–7.5%; eng yuqorisi Universal bank «Invest 7.5» 7.5%.
- **Ipoteka** — 17% dan (Hamkorbank, Agrobank, Ipoteka-bank); odatda 20–24%.
- **Avtokredit** — odatda 21–27%; ayrim modellarga 0% aksiyalar.
- **Mikroqarz** — 20–49%; garovli va ish haqi loyihasidagilar arzonroq, garovsiz onlayn eng qimmat.

Ma'lumot qidiruv tizimi orqali bank saytlaridan olingan, ko'p sahifalar sanasiz — muhim qarordan
oldin bankning o'zidan tekshiring.

## Skraper

Skript `banks.json` dagi har bir bankning **o'z rasmiy saytiga** kirib, kredit va omonat
bo'limlarini topadi, har bir mahsulot sahifasini ochadi va quyidagilarni yig'adi:

- mahsulot nomi va sahifa havolasi;
- foiz stavkalari (diapazon + saytdagi asl matn parchasi);
- muddatlar (oyga o'girilgan);
- summalar (so'mda) va valyutalar (UZS / USD / EUR / RUB);
- sahifadagi barcha jadvallar (tariflar jadvali odatda shu yerda bo'ladi);
- sahifaning to'liq matni (yashirin tab/akkordeonlar ham) — hech narsa yo'qolmasligi uchun.

### O'rnatish

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
```

### Ishga tushirish

```bash
python scrape.py                            # hamma banklar, kreditlar + omonatlar
python scrape.py --only hamkorbank,nbu      # faqat tanlangan banklar
python scrape.py --sections deposits        # faqat omonatlar
python scrape.py --lang ru                  # saytning rus tilidagi versiyasi
python scrape.py --headful --concurrency 1  # brauzer oynasini ko'rib turish
```

Natija `output/<sana>/` papkasiga yoziladi:

| Fayl | Nima bor |
|---|---|
| `report.xlsx` | **Kreditlar**, **Omonatlar** — har bir sahifa: foiz, muddat, summa, valyuta, havola. **… (kartochkalar)** — ro'yxat sahifasidagi har bir mahsulot kartochkasi. **Banklar** — bank bo'yicha soni va xatolar. |
| `credits.json`, `deposits.json` | Barcha topilgan sahifalar, jadvallar va foiz/muddat/summa tafsilotlari |
| `all.json` | Hammasi + sahifalarning to'liq matni |

### `banks.json`

```json
{"id": "hamkorbank", "name": "Hamkorbank", "site": "https://hamkorbank.uz"}
```

Skript bo'limlarni bosh sahifadagi havolalardan o'zi topadi (kredit, ipoteka, avtokredit, mikroqarz,
omonat, depozit, кредит, вклад …). Agar biror bankda topa olmasa, URL ni qo'lda bering:

```json
{"id": "xalqbank", "name": "Xalq banki", "site": "https://xb.uz",
 "credits": ["/uz/individuals/credits"], "deposits": ["/uz/individuals/deposits"]}
```

### Bilish kerak

- Har bir bank sayti har xil tuzilgan, shuning uchun foiz/muddat/summa matndan **avtomatik**
  ajratiladi. Har bir qatorda saytdagi asl matn parchasi va havola bor — muhim qarordan oldin
  saytning o'zidan tekshiring.
- Saytdagi "Ro'yxat" sahifasida bir nechta mahsulotning foizi aralash ko'rinadi; aniq qiymatlar
  "Mahsulot" qatorlarida va "kartochkalar" varag'ida.
- `banks.json` dagi domenlar ochiq manbalardan olingan; bank nomi yoki sayti o'zgargan bo'lsa,
  "Banklar" varag'ida xato chiqadi — faylni tuzating.

### Testlar

```bash
pip install pytest
pytest -q        # lokal test-sayt ustida, internet kerak emas
```

## Sayt

`docs/index.html` — bitta mustaqil HTML fayl (barcha ma'lumot ichida). Brauzerda to'g'ridan-to'g'ri
ochish mumkin. GitHub Pages'da `main` branch'ining `/docs` papkasidan joylangan:
https://erkinaripov14-cbuchun.github.io/uz-banks/ — `main` ga push qilingandan keyin avtomatik yangilanadi.
`site/index.html` — shu sahifaning Claude Artifact uchun versiyasi.

## Avtomatik yangilash

Saytdagi **"Yangilash"** tugmasi sahifani eng so'nggi ma'lumot bilan qayta yuklaydi (tashrif buyuruvchilar uchun).
Ma'lumotni bank saytlaridan qayta yig'ish uchun sayt pastidagi **"Ma'lumotni qayta yig'ish (administrator uchun)"**
havolasi GitHub Actions'dagi [Ma'lumotni yangilash](.github/workflows/update.yml) jarayonini ochadi. U yerda **Run workflow** ni bosing
(repoga yozish huquqi kerak; ixtiyoriy ravishda faqat ayrim banklarni yozish mumkin, masalan `hamkorbank,nbu`).
Jarayon har dushanba 08:17 (Toshkent) da o'zi ham ishlaydi.

Jarayon nima qiladi:
1. `scrape.py` bilan bank saytlarini o'qiydi;
2. `research/live.py` natijani `research/live/latest.json` ga yozadi;
3. `research/build.py` saytni qayta yasaydi, o'zgarishni `main` ga commit qiladi va Pages'ni qayta joylaydi.

Skraper topgan mahsulotlar saytning **Yangi topilganlar** bo'limida chiqadi (ma'lumot bo'lmasa, bo'lim ko'rinmaydi). Ular sahifa matnidan avtomatik
ajratilgani uchun qo'lda tekshirilgan jadvaldan aniqligi pastroq. Skraperning to'liq natijasi (Excel, JSON)
jarayon sahifasida `scraper-output` artifakti sifatida yuklab olinadi.

## Natijalarni qayta yasash

Ma'lumot `research/data_rasmiy.py` da, xulosalar matni `research/xulosalar.py` da.
Excel, CSV, XULOSALAR.md va saytni (`docs/`, `site/`) qayta yasash; sayt shabloni `research/site_template.html`:

```bash
python research/build.py
```

