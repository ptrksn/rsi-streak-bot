import os
import time
import hmac
import hashlib
import requests

API_KEY = os.getenv("PHEMEX_API_KEY")
API_SECRET = os.getenv("PHEMEX_API_SECRET")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
BASE_URL = "https://vapi.phemex.com"


def send_telegram_message(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": msg}
    try:
        requests.post(url, data=data)
    except Exception as e:
        print("❌ Fehler beim Senden der Telegram-Nachricht:", e)


def test_api():
    endpoint = "/accounts/account"
    timestamp = str(int(time.time() * 1000))
    message = endpoint + timestamp
    signature = hmac.new(
        bytes(API_SECRET, "utf-8"),
        bytes(message, "utf-8"),
        digestmod=hashlib.sha256
    ).hexdigest()

    headers = {
        "x-phemex-access-token": API_KEY,
        "x-phemex-request-expiry": timestamp,
        "x-phemex-request-signature": signature
    }

    url = BASE_URL + endpoint
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 403:
            print("⏳ API noch nicht freigeschaltet. Warte weiter...")
            return False
        else:
            print("✅ API funktioniert:", response.status_code)
            send_telegram_message("✅ Phemex API jetzt aktiv! Zugriff auf vapi.phemex.com funktioniert.")
            return True
    except Exception as e:
        print("❌ Fehler bei API-Test:", e)
        return False


if __name__ == "__main__":
    print("🔁 Starte Phemex-API-Watchdog...")
    while True:
        success = test_api()
        if success:
            break
        time.sleep(600)  # 10 Minuten warten
