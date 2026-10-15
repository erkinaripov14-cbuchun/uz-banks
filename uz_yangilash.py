"""O'zbekistondagi kompyuterda (GitHub self-hosted runner) ishlaydi: chet eldan ochilmaydigan bank saytlarini o'qib,
natijani saytga qo'shadi va main ga push qiladi.

    python uz_yangilash.py                 # UZ_BANKS dagi banklar
    python uz_yangilash.py --only anorbank # faqat shu bank

Push paytida main o'zgargan bo'lsa (boshqa yangilash bilan bir vaqtda), eng so'nggi main dan qayta yasab, yana urinadi.
"""
import argparse
import subprocess
import sys
from datetime import date
from pathlib import Path

# GitHub serveridan (AQSh) o'qib bo'lmaydigan banklar: sahifa bo'sh keladi, ulanish uziladi yoki 403
UZ_BANKS = ["asakabank", "anorbank", "smartbank"]
OUT = Path("output/uz")
BOT = ["-c", "user.name=github-actions[bot]", "-c", "user.email=41898282+github-actions[bot]@users.noreply.github.com"]


def run(*args, check=True):
    print("$", " ".join(args), flush=True)
    return subprocess.run(args, check=check)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default=",".join(UZ_BANKS))
    ap.add_argument("--no-push", action="store_true", help="faqat o'qish va saytni yasash (sinov uchun)")
    a = ap.parse_args()

    py = sys.executable
    run(py, "scrape.py", "--only", a.only, "--out", str(OUT), "--max-pages", "40", "--concurrency", "3",
        "--timeout", "45", "--budget", "420")
    results = OUT / "all.json"

    for attempt in range(1, 4):
        if not a.no_push:
            run("git", "fetch", "origin", "main")
            run("git", "reset", "--hard", "origin/main")   # output/ papkasi git'da yo'q, o'chmaydi
        run(py, "research/live.py", str(results))
        if run("git", "diff", "--quiet", "--", "research/live", check=False).returncode == 0:
            print("Yangi mahsulot topilmadi — sayt o'zgartirilmadi.")
            return
        run(py, "research/build.py")
        if a.no_push:
            return
        run("git", "add", "research/live", "docs", "site")
        run("git", *BOT, "commit", "-m", f"Ma'lumot yangilandi: O'zbekistondan o'qiladigan banklar ({date.today()})")
        if run("git", "push", "origin", "HEAD:main", check=False).returncode == 0:
            print("Tayyor: natija saytga yuborildi.")
            return
        print(f"Push rad etildi ({attempt}-urinish) — main o'zgargan, qayta yasaladi.")
    sys.exit("Push 3 marta rad etildi.")


if __name__ == "__main__":
    main()
