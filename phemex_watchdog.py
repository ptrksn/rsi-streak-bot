import os
import requests
import time

# === Debug-Ausgabe zur Laufzeit ===
print("✅ Watchdog-Skript gestartet...")

# === Einstellungen ===
PHEMEX_BASE_URL = "https://api.phemex.com"
TOP_SYMBOLS = ["BTCUSD", "ETHUSD", "XRPUSD", "LINKUSD", "LTCUSD"]  # Nur Beispiele
VOLUME_SPIKE_THRESHOLD = 2.0  # Faktor (z. B. 2.0 = doppelt so viel Volumen wie Schnitt)

# === Funktion: Volumen holen ===
def get_24h_volume(symbol):
    try:
        url = f"{PHEMEX_BASE_URL}/md/ticker/24hr?symbol={symbol}"
        response = requests.get(url)
        data = response.json()
        vol = float(data["result"]["turnoverEv"]) / 1e8
        return vol
    except Exception as e:
        print(f"⚠️ Fehler beim Abruf von Volumen für {symbol}: {e}")
        return None

# === Funktion: Telegram senden ===
def send_telegram_alert(symbol, vol):
    message = f"📈 Volumen-Anstieg bei {symbol}! Aktuelles Volumen: {vol:.2f}"
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not bot_token or not chat_id:
        print("⚠️ Telegram-Konfiguration fehlt.")
        return
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    requests.post(url, data={"chat_id": chat_id, "text": message})

# === Hauptlogik: Vergleiche Volumen mit früherem Durchschnitt ===
def main():
    print("🔍 Starte Volumen-Überwachung für Top-Symbole...")
    volumes = {}

    # Initiales Volumen speichern
    for symbol in TOP_SYMBOLS:
        vol = get_24h_volume(symbol)
        if vol:
            volumes[symbol] = vol
            print(f"💾 {symbol} - Initialvolumen: {vol:.2f}")
        time.sleep(1)

    # Kurze Wartezeit zur Simulation von Intervall
    print("⏳ Warte 60 Sekunden, um erneutes Volumen zu messen...")
    time.sleep(60)

    # Neues Volumen vergleichen
    for symbol in TOP_SYMBOLS:
        new_vol = get_24h_volume(symbol)
        if new_vol and symbol in volumes:
            factor = new_vol / volumes[symbol] if volumes[symbol] > 0 else 0
            print(f"📊 {symbol}: Vorher: {volumes[symbol]:.2f}, Jetzt: {new_vol:.2f}, Faktor: {factor:.2f}")
            if factor >= VOLUME_SPIKE_THRESHOLD:
                print(f"🚨 Volumen-Spike erkannt bei {symbol}!")
                # send_telegram_alert(symbol, new_vol)
        time.sleep(1)

    print("✅ Watchdog abgeschlossen.")

# === Starten ===
if __name__ == "__main__":
    main()
