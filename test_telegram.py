"""Telegram bot bağlantısını tek seferlik doğrulamak için kullanılır."""
from common import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, send_telegram_message

if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
    raise SystemExit(
        "TELEGRAM_BOT_TOKEN ve TELEGRAM_CHAT_ID ortam değişkenlerini ayarlamadan bu betiği çalıştıramazsınız.\n"
        "PowerShell örneği:\n"
        '  $env:TELEGRAM_BOT_TOKEN="senin_token"\n'
        '  $env:TELEGRAM_CHAT_ID="senin_chat_id"\n'
        "  python test_telegram.py"
    )

send_telegram_message("✅ Test bildirimi: Otomasyon sistemi başarıyla bağlandı!")
print("Mesaj gönderildi, Telegram'ı kontrol et.")
