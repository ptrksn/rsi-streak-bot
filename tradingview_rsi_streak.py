import os
import time
import requests
from tradingview_ta import TA_Handler, Interval

# === Telegram-Konfiguration ===
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# === Konfiguration ===
INTERVAL = Interval.INTERVAL_4_HOURS
RSI_STREAK_LENGTH = 4
RSI_THRESHOLD_LOW = 30
RSI_THRESHOLD_HIGH = 70
CMC_API_KEY = os.getenv("CMC_API_KEY")

# === Nur "echte" Coins analysieren ===
STABLECOIN_KEYWORDS = ["USDT", "USDC", "FDUSD", "DAI"]
EXCLUDED_SYMBOLS = ["vBNB", "WETH", "USDT.z", "ETH.z", "XUSDT"]

# === Telegram senden ===
def send_telegram(msg):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Telegram nicht konfiguriert.")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": msg})
    except Exception as e:
        print(f"❌ Telegram-Fehler: {e}")

# === Hole Top-CMC-Symbole ===
def get_top_symbols(limit=30):
    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"
    headers = {"X-CMC_PRO_API_KEY": CMC_API_KEY}
    params = {"sort": "volume_24h", "limit": limit, "convert": "USD"}
    try:
        response = requests.get(url, headers=headers, params=params)
        data = response.json()
        symbols = []
        for entry in data["data"]:
            symbol = entry["symbol"]
            if any(stable in symbol for stable in STABLECOIN_KEYWORDS):
                continue
            if symbol in EXCLUDED_SYMBOLS:
                continue
            symbols.append(f"{symbol}USDT")
        return symbols
    except Exception as e:
        print(f"❌ Fehler beim Abrufen der CMC-Symbole: {e}")
        return []

# === RSI berechnen ===
def get_rsi(symbol):
    try:
        handler = TA_Handler(
            symbol=symbol,
            screener="crypto",
            exchange="BINANCE",
            interval=INTERVAL
        )
        analysis = handler.get_analysis()
        return analysis.indicators.get("RSI")
    except Exception as e:
        print(f"❌ Fehler bei {symbol}: {e}")
        return None

# === Hauptlogik ===
def main():
    print("🔍 RSI-Streak-Check via TradingView...")
    symbols = get_top_symbols()
    print(f"📈 Analysiere {len(symbols)} Symbole: {symbols[:5]}...")

    long_setups = []
    short_setups = []

    for symbol in symbols:
        print(f"📊 {symbol}...")
        rsi = get_rsi(symbol)
        if rsi is None:
            continue

        print(f"Aktueller RSI: {rsi:.2f}")

        if rsi < RSI_THRESHOLD_LOW:
            long_setups.append(symbol)
            print("⚠️ RSI < 30 → Long-Setup möglich")
            send_telegram(f"📉 {symbol}: RSI < 30 – Long Setup denkbar!")
        elif rsi > RSI_THRESHOLD_HIGH:
            short_setups.append(symbol)
            print("⚠️ RSI > 70 → Short-Setup möglich")
            send_telegram(f"📈 {symbol}: RSI > 70 – Short Setup denkbar!")
        else:
            print("ℹ️ Kein RSI-Streak.")

    # === Telegram-Statusreport ===
    summary = f"✅ RSI-Analyse abgeschlossen.\n"
    summary += f"Long-Setups: {len(long_setups)}\n"
    summary += f"Short-Setups: {len(short_setups)}\n"
    send_telegram(summary)

# === Start ===
if __name__ == "__main__":
    main()
