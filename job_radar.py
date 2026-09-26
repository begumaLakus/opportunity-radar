import os
import time

import requests
from bs4 import BeautifulSoup

from common import load_json_set, save_json_set, send_telegram_message

SEEN_JOBS_FILE = "gorulen_ilanlar.json"

# Yalnızca hedeflediğin şehirler (Kastamonu vb. gelmemesi için Turkey kaldırıldı)
LOCATIONS = ["Istanbul", "Ankara", "Mersin", "Kocaeli", "Samsun", "Antalya"]
KEYWORDS = ["React Native", "Node.js", "Backend Developer", "Mobile Developer"]

# Pozitif Filtre: İlan başlığında bunlardan en az BİRİ mutlaka geçmeli
TARGET_KEYWORDS = [
    "react", "native", "node", "backend", "back-end",
    "mobile", "mobil", "frontend", "front-end",
    "full stack", "fullstack", "software engineer", "yazılım mühendis"
]

# Elenecek kıdem ve alakasız roller
EXCLUDED_KEYWORDS = [
    "senior", "sr.", "sr ", "lead", "principal", "director",
    "head of", "architect", "account manager", "solution designer",
    "sales", "satış", "engelli"
]


def notify_new_job(title, company, location, link):
    message = (
        f"🎯 <b>Yeni Uygun İlan Bulundu!</b>\n\n"
        f"📌 <b>Pozisyon:</b> {title}\n"
        f"🏢 <b>Şirket:</b> {company}\n"
        f"📍 <b>Konum:</b> {location}\n\n"
        f"🔗 <a href='{link}'>İlana Git ve Başvur</a>"
    )
    send_telegram_message(message)


def fetch_jobs_for_query(keyword, location):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    url = (
        f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?"
        f"keywords={requests.utils.quote(keyword)}&"
        f"location={requests.utils.quote(location)}&"
        f"f_TPR=r86400&sortBy=DD"
    )
    try:
        res = requests.get(url, headers=headers, timeout=15)
        if res.status_code == 200:
            return res.text
    except Exception as e:
        print(f"Arama Hatası ({keyword} - {location}): {e}")
    return ""


def scan_jobs():
    seen_jobs = load_json_set(SEEN_JOBS_FILE)
    total_new = 0

    print(f"[{time.strftime('%H:%M:%S')}] Hedef şehirler taranıyor...")

    for location in LOCATIONS:
        for keyword in KEYWORDS:
            html = fetch_jobs_for_query(keyword, location)
            if not html:
                continue

            soup = BeautifulSoup(html, "html.parser")
            cards = soup.find_all("li")

            for card in cards:
                link_tag = card.find("a", class_="base-card__full-link")
                title_tag = card.find("h3", class_="base-search-card__title")
                company_tag = card.find("h4", class_="base-search-card__subtitle")
                loc_tag = card.find("span", class_="job-search-card__location")

                if not link_tag or not title_tag:
                    continue

                job_link = link_tag.get("href", "").split("?")[0]
                job_id = card.find("div", class_="base-card").get("data-entity-urn", job_link)

                if job_id in seen_jobs:
                    continue

                title = title_tag.text.strip()
                company = company_tag.text.strip() if company_tag else "Bilinmiyor"
                job_loc = loc_tag.text.strip() if loc_tag else location
                title_lower = title.lower()

                if any(ex in title_lower for ex in EXCLUDED_KEYWORDS):
                    seen_jobs.add(job_id)
                    continue

                if not any(target in title_lower for target in TARGET_KEYWORDS):
                    seen_jobs.add(job_id)
                    continue

                print(f"-> Uygun İlan Bulundu: {title} | {company} ({job_loc})")
                notify_new_job(title, company, job_loc, job_link)

                seen_jobs.add(job_id)
                total_new += 1

            time.sleep(1.2)

    save_json_set(SEEN_JOBS_FILE, seen_jobs)
    print(f"Tarama bitti. Toplam {total_new} yeni uygun ilan bildirildi.\n")


if __name__ == "__main__":
    scan_jobs()
