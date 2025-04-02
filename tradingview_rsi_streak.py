import os
import time
import requests
import numpy as np
from tradingview_ta import TA_Handler, Interval
from datetime import datetime

# === Konfiguration ===
CMC_API_KEY = os.getenv("CMC_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
RSI_PERIOD = 14
RSI_STREAK_THRESHOLD = 4  # Anzahl nacheinander über/unter Schwelle
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30
MAX_SYMBOLS = 30

# === Helper: Telegram ===
def send_telegram_message(text):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Telegram-Konfiguration fehlt.")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": text})
    except Exception as e:
        print(f"❌ Telegram-Fehler: {e}")

# === Helper: CoinMarketCap Top-30 ===
def get_top_volume_symbols():
    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"
    params = {"sort": "volume_24h", "limit": MAX_SYMBOLS}
    headers = {"X-CMC_PRO_API_KEY": CMC_API_KEY}
    try:
        response = requests.get(url, headers=headers, params=params)
        data = response.json()
        symbols = []
        for item in data.get("data", []):
            symbol = item["symbol"]
            if symbol.endswith("USD") or symbol in ["USDT", "USDC", "FDUSD", "DAI"]:  # Stablecoins filtern
                continue
            symbols.append(f"{symbol}USDT")
        return symbols
    except Exception as e:
        print(f"❌ Fehler bei CMC: {e}")
        return []

# === Helper: Phemex Perp Filter ===
def get_phemex_symbols():
    url = "https://api.phemex.com/exchange/public/products"
    try:
        response = requests.get(url)
        data = response.json()
        return [p["symbol"] for p in data["data"] if p["type"] == "Perpetual"]
    except Exception as e:
        print(f"❌ Fehler bei Phemex-Symbolen: {e}")
        return []

# === RSI aus TradingView abrufen ===
def get_rsi(symbol):
    try:
        handler = TA_Handler(
            symbol=symbol,
            screener="crypto",
            exchange="BINANCE",
            interval=Interval.INTERVAL_4_HOURS,
        )
        analysis = handler.get_analysis()
        return analysis.indicators["RSI"]
    except Exception as e:
        print(f"❌ Fehler bei {symbol}: {e}")
        return None

# === Hauptfunktion ===
def main():
    print("🔍 RSI-Streak-Check via TradingView...")

    cmc_symbols = get_top_volume_symbols()
    phemex_symbols = get_phemex_symbols()

    filtered = [s for s in cmc_symbols if s.replace("USDT", "USD") in phemex_symbols]
    print(f"📈 Analysiere {len(filtered)} Symbole: {filtered}...")

    streak_summary = []
    for symbol in filtered:
        print(f"📊 {symbol}...")
        rsi_values = []

        # Aktueller RSI + 3 vorherige RSI-Werte abfragen
        for i in range(RSI_STREAK_THRESHOLD):
            rsi = get_rsi(symbol)
            if rsi is not None:
                rsi_values.append(rsi)
            time.sleep(1.5)  # leicht verzögern wegen Rate Limit

        if len(rsi_values) < RSI_STREAK_THRESHOLD:
            print("⏳ Nicht genug RSI-Werte.")
            continue

        current = rsi_values[0]
        streak = 0
        trend = None

        for r in rsi_values:
            if r < RSI_OVERSOLD:
                if trend in [None, "down"]:
                    streak += 1
                    trend = "down"
                else:
                    break
            elif r > RSI_OVERBOUGHT:
                if trend in [None, "up"]:
                    streak += 1
                    trend = "up"
                else:
                    break
            else:
                break

        print(f"Aktueller RSI: {current:.2f}")
        if streak >= RSI_STREAK_THRESHOLD:
            msg = f"✅ {symbol}: {streak}x RSI {'<' if trend=='down' else '>'} {RSI_OVERSOLD if trend=='down' else RSI_OVERBOUGHT}\n📈 RSI: {current:.2f}"
            streak_summary.append(msg)
        else:
            print("ℹ️ Kein RSI-Streak.")

    # Telegram-Report
    now = datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')
    if streak_summary:
        final_report = f"📊 RSI-Streak-Report ({now})\n\n" + "\n".join(streak_summary)
    else:
        final_report = f"📊 RSI-Streak-Report ({now})\n\n❌ Kein Coin mit aktuellem RSI-Streak."

    print(final_report)
    send_telegram_message(final_report)


if __name__ == "__main__":
    main()
