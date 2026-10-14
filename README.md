# uz-banks — O'zbekiston banklarining kredit va omonatlari

Skript `banks.json` dagi har bir bankning **o'z rasmiy saytiga** kirib, kredit va omonat
bo'limlarini topadi, har bir mahsulot sahifasini ochadi va quyidagilarni yig'adi:

- mahsulot nomi va sahifa havolasi;
- foiz stavkalari (diapazon + saytdagi asl matn parchasi);
- muddatlar (oyga o'girilgan);
- summalar (so'mda) va valyutalar (UZS / USD / EUR / RUB);
- sahifadagi barcha jadvallar (tariflar jadvali odatda shu yerda bo'ladi);
- sahifaning to'liq matni (yashirin tab/akkordeonlar ham) — hech narsa yo'qolmasligi uchun.

## O'rnatish

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
```

## Ishga tushirish

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

## `banks.json`

```json
{"id": "hamkorbank", "name": "Hamkorbank", "site": "https://hamkorbank.uz"}
```

Skript bo'limlarni bosh sahifadagi havolalardan o'zi topadi (kredit, ipoteka, avtokredit, mikroqarz,
omonat, depozit, кредит, вклад …). Agar biror bankda topa olmasa, URL ni qo'lda bering:

```json
{"id": "xalqbank", "name": "Xalq banki", "site": "https://xb.uz",
 "credits": ["/uz/individuals/credits"], "deposits": ["/uz/individuals/deposits"]}
```

## Bilish kerak

- Har bir bank sayti har xil tuzilgan, shuning uchun foiz/muddat/summa matndan **avtomatik**
  ajratiladi. Har bir qatorda saytdagi asl matn parchasi va havola bor — muhim qarordan oldin
  saytning o'zidan tekshiring.
- Saytdagi "Ro'yxat" sahifasida bir nechta mahsulotning foizi aralash ko'rinadi; aniq qiymatlar
  "Mahsulot" qatorlarida va "kartochkalar" varag'ida.
- `banks.json` dagi domenlar ochiq manbalardan olingan; bank nomi yoki sayti o'zgargan bo'lsa,
  "Banklar" varag'ida xato chiqadi — faylni tuzating.

## Testlar

```bash
pip install pytest
pytest -q        # lokal test-sayt ustida, internet kerak emas
```
