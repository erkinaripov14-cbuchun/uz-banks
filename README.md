# uz-banks — O'zbekiston banklarining kredit va omonatlari

30 ta O'zbekiston bankining kredit va omonat mahsulotlari: foiz, muddat, summa va valyuta —
faqat bankning o'z saytidan.

**Sayt: https://erkinaripov14-cbuchun.github.io/uz-banks/**

> **Hozir sayt va Excel faqat kreditlarni ko'rsatadi.** Omonat ma'lumoti `research/data_rasmiy.py` da saqlanadi;
> qaytarish uchun `research/xulosalar.py` da `SHOW_DEPOSITS = True` qiling va `--sections credits` ni
> `.github/workflows/update.yml` hamda `uz_yangilash.py` dan olib tashlang.

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

**Tillar:** sahifa tepasida til tanlanadi: O'zbek (lotin), Ўзбек (kirill), Русский, English. Havola orqali ham ochish mumkin:
`?lang=uz`, `?lang=cy`, `?lang=ru`, `?lang=en`. Kirill matn lotindan avtomatik o'giriladi; rus va ingliz tarjimalari —
interfeys uchun `research/site_template.html` ichida, ma'lumot matnlari (izohlar, xulosalar) uchun `research/i18n_texts.json` da.
Yangi izoh yoki xulosa qo'shilsa, uning tarjimasini shu faylga qo'shing (bo'lmasa o'zbekcha ko'rinadi).

## Avtomatik yangilash

Tashrif buyuruvchilar ma'lumotni yangilay olmaydi: saytda ular uchun faqat ko'rish, grafiklar va **Excel yuklab olish** bor.

Administrator sayt pastidagi **"Administrator"** havolasini bosib, parol bilan kiradi va **"Ma'lumotni yangilash"**
tugmasini bosadi — sayt GitHub API orqali [Ma'lumotni yangilash](.github/workflows/update.yml) jarayonini o'zi ishga tushiradi
va holatini ko'rsatib turadi. Buning uchun har bir qurilmada bir marta GitHub tokeni kiritiladi:

- [Fine-grained token](https://github.com/settings/personal-access-tokens/new) yarating: Repository access → faqat `uz-banks`,
  Permissions → **Actions: Read and write** (boshqa ruxsat kerak emas).
- Token admin paroli bilan shifrlanadi (PBKDF2 + AES-GCM) va shu brauzerda saqlanadi.
- **Bitta tugma, har qanday qurilmada:** admin bo'limida "Barcha qurilmalarda ishlashi uchun kod olish" bilan shifrlangan
  kodni olib, `research/admin_token.json` ga yozing va saytni qayta yasang (`python research/build.py`). Shundan keyin
  istalgan qurilmada parol → "Ma'lumotni yangilash". Kod parolsiz ochilmaydi; tokenning o'zi repoda saqlanmaydi.
- Bu faqat asosiy saytda (github.io) ishlaydi.

Jarayonni GitHub'ning o'zidan ham ishga tushirish mumkin: Actions → **Run workflow** (ixtiyoriy ravishda faqat ayrim banklar, masalan `hamkorbank,nbu`).
Ayrim banklar uchun yangilaganda faqat o'sha banklarning ma'lumoti almashadi, qolganlari saqlanib qoladi.
Jarayon har dushanba 08:17 (Toshkent) da o'zi ham ishlaydi.

Jarayon nima qiladi:
1. `scrape.py` bilan bank saytlarini o'qiydi;
2. `research/live.py` natijani `research/live/latest.json` ga yozadi;
3. `research/build.py` saytni qayta yasaydi, o'zgarishni `main` ga commit qiladi va Pages'ni qayta joylaydi.

Skraper bank saytidagi "Kreditlar" va "Omonatlar" bo'limlariga kirib, ichidagi har bir mahsulot sahifasini va kartochkasini
o'qiydi — jismoniy va yuridik shaxslar bo'limlarini ham (yuridiklar alohida belgilanadi). Natija (`research/merge.py`)
qo'lda tekshirilgan jadval bilan solishtiriladi: bir xil mahsulot bitta qator bo'ladi va "saytda hozir" foizi yonida
ko'rsatiladi, yangi mahsulot "saytdan avtomatik" belgisi bilan qo'shiladi. Saytdagi Kreditlar va Omonatlar jadvallarida
"Jismoniy shaxslar / Yuridik shaxslar va tadbirkorlar" tanlovi bor; banklar bo'yicha sonlar shu umumiy ro'yxatdan hisoblanadi. Skraperning to'liq natijasi (Excel, JSON)
jarayon sahifasida `scraper-output` artifakti sifatida yuklab olinadi.

## Natijalarni qayta yasash

Ma'lumot `research/data_rasmiy.py` da, xulosalar matni `research/xulosalar.py` da.
Excel, CSV, XULOSALAR.md va saytni (`docs/`, `site/`) qayta yasash; sayt shabloni `research/site_template.html`:

```bash
python research/build.py
```


## O'zbekistondan yangilash (server yoki Windows kompyuter)

Asakabank va Anorbank saytlari GitHub serveridan (AQSh) ochilmaydi: sahifa bo'sh keladi, ulanish uziladi
yoki "403". Ular O'zbekistondagi server yoki kompyuterda o'qiladi. Buning uchun unga bir marta GitHub runner dasturi
`uz` belgisi bilan o'rnatiladi (Linux server yoki Windows kompyuter — ikkalasi ham ishlaydi). Keyin `.github/workflows/update-uz.yml` asosiy yangilashdan so'ng o'zi ishga tushadi va shu kompyuterda
`uz_yangilash.py` ni bajaradi. Kompyuter o'chiq bo'lsa, navbatda kutadi; asosiy yangilashga xalaqit bermaydi.

### A. O'zbekistondagi Linux server (VPS) — doim yoqiq, tavsiya etiladi

**Server talablari:** Ubuntu 24.04 (yoki 22.04), 2 CPU, 2 GB RAM, 20 GB disk, **IP manzili O'zbekistonniki**.
Hosting sizga server IP manzili va `root` paroli beradi.

1. Serverga ulaning: kompyuterda `ssh root@SERVER_IP`, iPhone'da **Termius** ilovasi (host — IP, user — `root`, parol).
2. Quyidagilarni bajaring (bir marta, nusxalab qo'ying):
   ```bash
   curl -s ipinfo.io/country        # UZ chiqishi kerak — aks holda server O'zbekistonda emas
   apt-get update && apt-get install -y git curl python3-venv
   python3 -m venv /opt/pw && /opt/pw/bin/pip install playwright && /opt/pw/bin/playwright install-deps chromium
   useradd -m -s /bin/bash runner
   su - runner
   ```
3. Brauzerda oching: https://github.com/erkinaripov14-cbuchun/uz-banks/settings/actions/runners/new?arch=x64&os=linux
4. **Download** bo'limidagi buyruqlarni birma-bir serverda bajaring.
5. **Configure** bo'limidagi `./config.sh --url ... --token ...` buyrug'ining **oxiriga** ` --labels uz --unattended`
   qo'shib bajaring.
6. Servis qilib o'rnating (server qayta yoqilganda ham o'zi ishga tushadi):
   ```bash
   exit
   cd /home/runner/actions-runner && ./svc.sh install runner && ./svc.sh start
   ```
7. Runners sahifasida server **Idle** (yashil) ko'rinadi. Quyidagi 7–8-bandlarni (xavfsizlik va sinov) bajaring.

### B. Windows kompyuter (bepul, yangilash paytida yoqiq turishi kerak)

1. **Git** o'rnating: https://git-scm.com/download/win (hamma sozlamalar standart).
2. Brauzerda oching: https://github.com/erkinaripov14-cbuchun/uz-banks/settings/actions/runners/new?arch=x64&os=win
3. **PowerShell** ni administrator sifatida oching (Pusk → PowerShell → o'ng tugma → "Run as administrator").
4. Sahifadagi **Download** bo'limidagi buyruqlarni birma-bir nusxalab, PowerShell'ga qo'yib bajaring.
5. **Configure** bo'limidagi `./config.cmd --url ... --token ...` buyrug'ini bajaring va savollarga javob bering:
   - runner group, name, work folder — **Enter**;
   - *additional labels* — **`uz`** deb yozing (muhim);
   - *run as service?* — **Y**;
   - *user account for the service* — **`NT AUTHORITY\SYSTEM`** deb yozing.
6. Runners sahifasida kompyuter **Idle** (yashil) bo'lib ko'rinadi — tayyor.
7. Xavfsizlik (repo ochiq): Settings → Actions → General → *Fork pull request workflows from outside collaborators* →
   **Require approval for all outside collaborators**.
8. Sinov: Actions → **O'zbekistondan yangilash** → **Run workflow**. Birinchi safar Python va brauzer yuklanadi (~5 daqiqa).
