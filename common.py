"""Telegram bildirimleri ve JSON tabanlı durum dosyaları için ortak yardımcılar."""
import json
import os

import requests

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")


def load_json_set(path):
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return set(json.load(f))
        except Exception:
            return set()
    return set()


def save_json_set(path, values):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(sorted(values), f, ensure_ascii=False, indent=2)


def send_telegram_message(text):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram bilgileri yok, bildirim atlanıyor.")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    try:
        res = requests.post(url, json=payload, timeout=10)
        if res.status_code != 200:
            print(f"Telegram mesaj hatası ({res.status_code}): {res.text}")
    except Exception as e:
        print(f"Telegram mesaj hatası: {e}")


def send_telegram_document(path):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram bilgileri yok, dosya gönderimi atlanıyor.")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument"
    try:
        with open(path, "rb") as f:
            res = requests.post(
                url,
                data={"chat_id": TELEGRAM_CHAT_ID},
                files={"document": f},
                timeout=60,
            )
        if res.status_code != 200:
            print(f"Telegram dosya gönderme hatası ({res.status_code}): {res.text}")
    except Exception as e:
        print(f"Telegram dosya gönderme hatası: {e}")
