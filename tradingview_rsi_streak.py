import os
import time
import numpy as np
from datetime import datetime
from tradingview_ta import TA_Handler, Interval, Exchange
import requests

CMC_API_KEY = os.getenv("CMC_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


def send_telegram_message(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Telegram-Konfiguration fehlt.")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        response = requests.post(url, data=data)
        if response.status_code != 200:
            print("⚠️ Fehler beim Senden der Telegram-Nachricht:", response.text)
    except Exception as e:
        print("❌ Telegram-Fehler:", e)


def get_top_30_symbols():
    try:
        url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"
        headers = {"X-CMC_PRO_API_KEY": CMC_API_KEY}
        params = {"start": "1", "limit": "50", "sort": "volume_24h", "convert": "USDT"}
        response = requests.get(url, headers=headers, params=params)
        data = response.json()
        symbols = [entry["symbol"] + "USDT" for entry in data["data"]]

        # Filtere Stablecoins und ungültige Symbole
        blacklist = ["USDTUSDT", "USDCUSDT", "FDUSDUSDT", "TUSDUSDT", "DAIUSDT", "EURUSDT", "vBNBUSDT", "ETH.zUSDT", "USDT.zUSDT"]
        filtered = [s for s in symbols if s not in blacklist and "." not in s and len(s) <= 12]
        return filtered[:30]  # Top 30
    except Exception as e:
        print("❌ Fehler beim Abrufen der CMC-Daten:", e)
        return []


def get_rsi_values(symbol):
    try:
        handler = TA_Handler(
            symbol=symbol.replace("USDT", ""),
            screener="crypto",
            exchange="BINANCE",
            interval=Interval.INTERVAL_4_HOURS
        )
        analysis = handler.get_analysis()
        rsi_list = analysis.indicators.get("RSI")
        if isinstance(rsi_list, (int, float)):
            return float(rsi_list), [float(rsi_list)]
        return None, []
    except Exception as e:
        print(f"❌ {symbol}: Fehler bei RSI", e)
        return None, []


def check_rsi_streak(rsi_values):
    last_4 = rsi_values[-4:] if len(rsi_values) >= 4 else []
    if len(last_4) < 4:
        return "none"

    below_30 = sum(1 for r in last_4 if r < 30)
    above_70 = sum(1 for r in last_4 if r > 70)

    if below_30 == 4:
        return "streak_long"
    elif above_70 == 4:
        return "streak_short"
    elif below_30 >= 3:
        return "potential_long"
    elif above_70 >= 3:
        return "potential_short"
    else:
        return "none"


def main():
    print("🔍 RSI-Streak-Check via TradingView...")
    symbols = get_top_30_symbols()
    print(f"📈 Analysiere {len(symbols)} Symbole: {symbols[:5]}...")

    streaks = []
    potentials = []
    none = []

    for symbol in symbols:
        print(f"📊 {symbol}...")
        rsi, rsi_values = get_rsi_values(symbol)
        if rsi is None:
            none.append(f"❌ {symbol}: Fehler bei RSI")
            continue

        status = check_rsi_streak(rsi_values)

        if status == "streak_long":
            streaks.append(f"✅ {symbol}: RSI < 30 (4/4) – Long Streak")
        elif status == "streak_short":
            streaks.append(f"✅ {symbol}: RSI > 70 (4/4) – Short Streak")
        elif status == "potential_long":
            potentials.append(f"⚠️ {symbol}: RSI unter 30 – Long Setup denkbar")
        elif status == "potential_short":
            potentials.append(f"⚠️ {symbol}: RSI über 70 – Short Setup denkbar")
        else:
            none.append(f"❌ {symbol}: Kein RSI-Streak")

        time.sleep(1)

    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    report = f"📊 RSI-Streak-Report ({now})\n\n"

    if streaks:
        report += "✅ Aktuelle RSI-Streaks (4/4):\n" + "\n".join(streaks) + "\n\n"
    if potentials:
        report += "⚠️ Potenzielle Setups (3/4):\n" + "\n".join(potentials) + "\n\n"
    if none:
        report += "❌ Kein RSI-Streak oder Fehler:\n" + "\n".join(none)

    print(report)
    send_telegram_message(report)


if __name__ == "__main__":
    main()
