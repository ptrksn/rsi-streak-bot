import os
import time
import numpy as np
from datetime import datetime
from tradingview_ta import TA_Handler, Interval
import requests

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
CMC_API_KEY = os.getenv("CMC_API_KEY")

HEADERS = {
    "X-CMC_PRO_API_KEY": CMC_API_KEY
}

TRADINGVIEW_INTERVAL = Interval.INTERVAL_4_HOURS
MIN_REQUIRED_VALUES = 4


def send_telegram(msg):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Telegram-Konfiguration fehlt.")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": msg})


def get_cmc_top_symbols(limit=50):
    url = f"https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest?limit={limit}&convert=USDT"
    try:
        response = requests.get(url, headers=HEADERS)
        data = response.json()
        symbols = [entry['symbol'] + 'USDT' for entry in data['data']]
        return symbols
    except Exception as e:
        print(f"❌ Fehler beim Abruf der CMC-Symbole: {e}")
        return []


def get_rsi_values(symbol):
    handler = TA_Handler(
        symbol=symbol,
        screener="crypto",
        exchange="BINANCE",
        interval=Interval.INTERVAL_4_HOURS,
    )

    try:
        analysis = handler.get_analysis()
        rsi_series = analysis.indicators.get("RSI", None)

        # Sicherstellen, dass rsi_series eine Liste ist
        if isinstance(rsi_series, list):
            return rsi_series
        elif isinstance(rsi_series, (int, float)):
            return [rsi_series]  # ein einzelner Wert → in Liste packen
        else:
            return []
    except Exception as e:
        print(f"❌ Fehler bei {symbol}: {e}")
        return []


def check_rsi_streak(rsi_values):
    streak = 0
    last_4 = rsi_values[-4:] if len(rsi_values) >= 4 else []
    for rsi in reversed(last_4):
        if rsi < 30:
            streak += 1
        else:
            break
    if streak >= 4:
        return "LONG"
    elif sum(1 for rsi in last_4 if rsi < 30) >= 3:
        return "LONG_SETUP"

    streak = 0
    for rsi in reversed(last_4):
        if rsi > 70:
            streak += 1
        else:
            break
    if streak >= 4:
        return "SHORT"
    elif sum(1 for rsi in last_4 if rsi > 70) >= 3:
        return "SHORT_SETUP"

    return None


def main():
    print("🔍 RSI-Streak-Check via TradingView...")
    all_symbols = get_cmc_top_symbols(limit=50)

    valid_symbols = [s for s in all_symbols if s.endswith("USDT") and not any(
        x in s for x in [".z", "v", "USDC", "TUSD", "FDUSD", "USDTUSDT"])]
    print(f"📈 Analysiere {len(valid_symbols)} Symbole: {valid_symbols[:5]}...")

    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    long_streaks = []
    short_streaks = []
    long_setups = []
    short_setups = []
    errors = []

    for symbol in valid_symbols:
        print(f"📊 {symbol}...")
        rsi, rsi_values = get_rsi_values(symbol)
        if rsi is None or not rsi_values:
            errors.append(symbol)
            continue

        status = check_rsi_streak(rsi_values)
        if status == "LONG":
            long_streaks.append(symbol)
        elif status == "SHORT":
            short_streaks.append(symbol)
        elif status == "LONG_SETUP":
            long_setups.append(symbol)
        elif status == "SHORT_SETUP":
            short_setups.append(symbol)

    # Report generieren
    report = f"📊 RSI-Streak-Report ({timestamp})\n\n"

    if long_streaks or short_streaks or long_setups or short_setups:
        if long_streaks:
            report += "🚀 RSI-Streak (LONG):\n" + "\n".join([f"✅ {s}" for s in long_streaks]) + "\n\n"
        if short_streaks:
            report += "🔻 RSI-Streak (SHORT):\n" + "\n".join([f"✅ {s}" for s in short_streaks]) + "\n\n"
        if long_setups:
            report += "⚠️ Long Setup denkbar:\n" + "\n".join([f"⚠️ {s}" for s in long_setups]) + "\n\n"
        if short_setups:
            report += "⚠️ Short Setup denkbar:\n" + "\n".join([f"⚠️ {s}" for s in short_setups]) + "\n\n"
    else:
        report += "❌ Kein Coin mit aktuellem RSI-Streak oder Setup."

    if errors:
        report += "\n\n❌ Fehlerhafte Symbole:\n" + "\n".join(errors)

    send_telegram(report)
    print("✅ RSI-Analyse abgeschlossen.")


if __name__ == "__main__":
    main()
