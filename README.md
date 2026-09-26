# Opportunity Radar

LinkedIn ve Google araması üzerinden çalışan, kendi kriterlerime göre iş ilanlarını ve hedef şirketleri tarayıp Telegram üzerinden bana bildirim gönderen iki katmanlı bir otomasyon. GitHub Actions üzerinde zamanlanmış görevler olarak, sunucusuz şekilde çalışır.

## Nasıl çalışıyor

**1. Katman: İlan Radarı ([job_radar.py](job_radar.py))**
Belirlenen şehir ve pozisyon anahtar kelimelerine göre LinkedIn'in genel iş ilanı aramasını tarar, seviye/rol filtresinden geçen yeni ilanları Telegram botuna bildirir. Her 30 dakikada bir [GitHub Actions](.github/workflows/job_runner.yml) üzerinden otomatik çalışır.

**2. Katman: Şirket Avcısı ([company_hunter.py](company_hunter.py))**
[Serper.dev](https://serper.dev) arama API'si üzerinden hedef şehir/sektör/ölçek kriterlerine uyan LinkedIn şirket sayfalarını bulur, bir Excel dosyasına ekler ve özet bildirimi Telegram'a gönderir. Günde 2 kez [GitHub Actions](.github/workflows/company_hunter.yml) üzerinden çalışır; sayfalama durumunu (`arama_durumu.json`) kaydederek bir sonraki çalıştırmada kaldığı yerden devam eder.

Her iki script de aynı Telegram bildirim ve durum-dosyası mantığını [common.py](common.py) üzerinden paylaşır.

## Kurulum

Ortam değişkenleri (yerelde `.env` veya GitHub Actions secrets olarak):

| Değişken | Açıklama |
|---|---|
| `TELEGRAM_BOT_TOKEN` | [@BotFather](https://t.me/BotFather) üzerinden alınan bot token'ı |
| `TELEGRAM_CHAT_ID` | Bildirimin gideceği sohbetin chat ID'si |
| `SERPER_API_KEY` | [serper.dev](https://serper.dev) üzerinden alınan ücretsiz arama API anahtarı (yalnızca şirket avcısı için gerekli) |

```bash
pip install requests beautifulsoup4 pandas openpyxl

python job_radar.py       # ilan taraması
python company_hunter.py  # şirket taraması
python test_telegram.py   # bot bağlantısını doğrula
```

## Neden bu şekilde tasarladım

- **Durum dosyaları (`gorulen_ilanlar.json`, `gorulen_sirketler.json`, `arama_durumu.json`):** Her çalıştırmada aynı ilan/şirketin tekrar bildirilmemesi ve arama sayfalamasının kaldığı yerden devam etmesi için repoya commit'lenir (bkz. workflow dosyalarının son adımı).
- **Serper.dev'e geçiş:** Başlangıçta Google Custom Search API kullanıyordum; bu API'nin ücretsiz kullanımı kısıtlandığı ve 2027'de kapanacağı için tek anahtarlı, kurulumu daha basit bir alternatife geçtim.
- **Sırlar yalnızca ortam değişkeninden okunur, kodda hiçbir gerçek değer tutulmaz.**
