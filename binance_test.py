import requests
import os
import hmac
import hashlib
import time
from urllib.parse import urlencode

API_KEY = os.environ.get("BINANCE_API_KEY")
API_SECRET = os.environ.get("BINANCE_API_SECRET")

def check_api_access():
    base_url = "https://api.binance.com"
    endpoint = "/api/v3/account"
    timestamp = int(time.time() * 1000)
    query_string = urlencode({'timestamp': timestamp})
    signature = hmac.new(API_SECRET.encode(), query_string.encode(), hashlib.sha256).hexdigest()

    url = f"{base_url}{endpoint}?{query_string}&signature={signature}"
    headers = {"X-MBX-APIKEY": API_KEY}

    try:
        response = requests.get(url, headers=headers)
        print("📡 Anfrage gesendet...")
        if response.status_code == 200:
            print("✅ Binance API Key funktioniert!")
            print(response.json())
        else:
            print(f"❌ Fehler: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"❌ Ausnahmefehler: {e}")

check_api_access()
