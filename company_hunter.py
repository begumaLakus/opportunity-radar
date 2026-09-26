import json
import os
import time

import requests
import pandas as pd

from common import load_json_set, save_json_set, send_telegram_message, send_telegram_document

# Google Custom Search JSON API 1 Ocak 2027'de kapanıyor ve zaten yeni hesaplara
# kapatılmış durumda (https://developers.google.com/custom-search/v1/overview).
# Bu yüzden arama sağlayıcısı olarak Serper.dev kullanıyoruz: tek API key,
# GCP projesi/billing derdi yok, 2500 sorgu ücretsiz.
SERPER_API_KEY = os.environ.get("SERPER_API_KEY")

SEEN_COMPANIES_FILE = "gorulen_sirketler.json"
STATE_FILE = "arama_durumu.json"
OUTPUT_FILE = "hedef_sirketler.xlsx"
PAGES_PER_RUN = 4


def _require_search_env():
    if not SERPER_API_KEY:
        raise SystemExit(
            "Eksik ortam değişkeni: SERPER_API_KEY.\n"
            "https://serper.dev üzerinden ücretsiz kayıt olup (kredi kartı istemiyor) "
            "dashboard'daki key'i GitHub secrets'a ya da yerelde $env:SERPER_API_KEY "
            "olarak ayarlayın."
        )


def search_companies(query, page=1):
    url = "https://google.serper.dev/search"
    headers = {
        "X-API-KEY": SERPER_API_KEY,
        "Content-Type": "application/json",
    }
    payload = {"q": query, "gl": "tr", "hl": "tr", "num": 10, "page": page}
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=15)
        if res.status_code == 200:
            return res.json()
        print(f"API Hatası ({res.status_code}): {res.text}")
    except Exception as e:
        print(f"Bağlantı Hatası: {e}")
    return None


def load_start_page():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f).get("sonraki_sayfa", 1)
        except Exception:
            return 1
    return 1


def save_start_page(next_page):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump({"sonraki_sayfa": next_page}, f, ensure_ascii=False, indent=2)


def notify_telegram_summary(new_companies):
    lines = [f"🏢 <b>{len(new_companies)} yeni hedef şirket bulundu!</b>\n"]
    for c in new_companies[:15]:
        lines.append(f"• <a href='{c['LinkedIn Profili']}'>{c['Şirket Adı']}</a>")
    if len(new_companies) > 15:
        lines.append(f"\n...ve {len(new_companies) - 15} şirket daha (ekli Excel'de tam liste var).")
    send_telegram_message("\n".join(lines))


def build_company_list():
    _require_search_env()

    # Hedef şehirler ve ölçek (2-10, 11-50, 51-200 çalışan)
    query = (
        'site:linkedin.com/company ("Mersin" OR "Ankara" OR "Istanbul" OR "Kocaeli" OR "Samsun" OR "Antalya") '
        '("mobil" OR "react native" OR "yazılım" OR "software" OR "web") '
        '("11-50 employees" OR "2-10 employees" OR "51-200 employees")'
    )

    seen = load_json_set(SEEN_COMPANIES_FILE)
    start_page = load_start_page()
    scanned_total = 0
    new_companies = []
    last_page_scanned = start_page - 1
    reached_end = False

    print(f"🏢 Hedef şirketler taranıyor (Serper.dev), {start_page}. sayfadan devam ediliyor...")

    # Serper sayfa başına 10 sonuç döndürür. Her çalıştırmada kaldığımız sayfadan
    # devam ederek (start_page..start_page+PAGES_PER_RUN) her seferinde Google'ın
    # aynı ilk sonuçlarını değil, yeni bir dilimini tarıyoruz.
    for page in range(start_page, start_page + PAGES_PER_RUN):
        print(f"Sayfa taranıyor ({page})...")
        data = search_companies(query, page=page)
        if not data or "organic" not in data or not data["organic"]:
            reached_end = True
            break
        last_page_scanned = page

        for item in data["organic"]:
            link = item.get("link", "")
            if "linkedin.com/company/" not in link:
                continue

            scanned_total += 1
            if link in seen:
                continue

            title = item.get("title", "").split("|")[0].split("-")[0].strip()
            snippet = item.get("snippet", "")
            entry = {
                "Şirket Adı": title,
                "LinkedIn Profili": link,
                "Özet / Açıklama": snippet,
                "Durum": "İncelenmedi",
            }
            new_companies.append(entry)
            seen.add(link)

        time.sleep(1.0)

    # Bir sonraki çalıştırma nereden devam edecek? Sayfalar bittiyse (reached_end)
    # baştan (1) başlarız; bitmediyse kaldığımız yerden devam ederiz.
    next_start_page = 1 if reached_end else last_page_scanned + 1
    save_start_page(next_start_page)

    if scanned_total == 0:
        if reached_end and start_page == 1:
            print("Hiç sonuç dönmedi. SERPER_API_KEY'i ve internet bağlantısını kontrol edin.")
        else:
            print(f"{start_page}. sayfadan itibaren sonuç kalmamış, bir sonraki çalıştırma "
                  f"1. sayfadan tekrar başlayacak.")
        return

    if os.path.exists(OUTPUT_FILE):
        try:
            existing_df = pd.read_excel(OUTPUT_FILE)
        except Exception:
            existing_df = pd.DataFrame(columns=["Şirket Adı", "LinkedIn Profili", "Özet / Açıklama", "Durum"])
        df = pd.concat([existing_df, pd.DataFrame(new_companies)], ignore_index=True)
    else:
        df = pd.DataFrame(new_companies)

    if df.empty:
        print(f"{scanned_total} şirket tarandı ama hepsi daha önce görülmüştü, yeni ekleme yok.")
        return

    df.drop_duplicates(subset=["LinkedIn Profili"], inplace=True)
    df.to_excel(OUTPUT_FILE, index=False)
    save_json_set(SEEN_COMPANIES_FILE, seen)

    print(f"\nİşlem tamam! {scanned_total} şirket tarandı, {len(new_companies)} yenisi "
          f"'{OUTPUT_FILE}' dosyasına eklendi (toplam {len(df)} kayıt).")

    if new_companies:
        notify_telegram_summary(new_companies)
        send_telegram_document(OUTPUT_FILE)


if __name__ == "__main__":
    build_company_list()
