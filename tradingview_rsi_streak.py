import os
from datetime import datetime
from tradingview_ta import TA_Handler, Interval, Exchange
import time
import requests

# === Telegram-Konfiguration ===
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram(message):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Telegram-Konfiguration fehlt.")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print(f"❌ Fehler beim Senden der Telegram-Nachricht: {e}")

# === Coins (Top 30 stabil, Phemex-verfügbar) ===
SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "XRPUSDT", "BNBUSDT", "SOLUSDT", "DOGEUSDT", "ADAUSDT", "AVAXUSDT",
    "LINKUSDT", "UNIUSDT", "LTCUSDT", "TRXUSDT", "DOTUSDT", "SHIBUSDT", "BCHUSDT", "AAVEUSDT",
    "MATICUSDT", "EOSUSDT", "MASKUSDT", "COMPUSDT", "SANDUSDT", "GRTUSDT", "NEARUSDT",
    "APTUSDT", "RNDRUSDT", "INJUSDT", "ARBUSDT", "STXUSDT", "LDOUSDT", "CRVUSDT"
]

# === RSI-Analyse ===
def get_rsi_values(symbol):
    try:
        handler = TA_Handler(
            symbol=symbol,
            screener="crypto",
            exchange="binance",
            interval=Interval.INTERVAL_4_HOURS
        )
        analysis = handler.get_analysis()
        rsi_series = analysis.indicators.get("RSI")
        if isinstance(rsi_series, list):
            return rsi_series[-1], rsi_series[-4:]  # Aktuellster RSI, letzte 4
        elif isinstance(rsi_series, (int, float)):
            return rsi_series, [rsi_series] * 4
        else:
            raise ValueError("Ungueltiges RSI-Format")
    except Exception as e:
        return None, f"Fehler bei RSI: {e}"

def check_rsi_streak(rsi_values):
    if isinstance(rsi_values, str):
        return rsi_values
    below_30 = [r < 30 for r in rsi_values].count(True)
    above_70 = [r > 70 for r in rsi_values].count(True)
    if below_30 == 4:
        return "✅ RSI < 30 (4x) – Long Streak"
    elif above_70 == 4:
        return "✅ RSI > 70 (4x) – Short Streak"
    elif below_30 == 3:
        return "⚠️ RSI unter 30 – Long Setup denkbar"
    elif above_70 == 3:
        return "⚠️ RSI über 70 – Short Setup denkbar"
    else:
        return "❌ Kein RSI-Streak"

# === Hauptfunktion ===
def main():
    print("🔍 RSI-Streak-Check via TradingView...")
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    group_streaks = []
    group_setups = []
    group_neutral = []

    print(f"📈 Analysiere {len(SYMBOLS)} Symbole: {SYMBOLS[:5]}...")

    for symbol in SYMBOLS:
        print(f"📊 {symbol}...")
        rsi, rsi_values = get_rsi_values(symbol)

        if isinstance(rsi_values, str):
            group_neutral.append(f"❌ {symbol}: {rsi_values}")
            continue

        status = check_rsi_streak(rsi_values)
        if "✅" in status:
            group_streaks.append(f"{symbol}: {status}")
        elif "⚠️" in status:
            group_setups.append(f"{symbol}: {status}")
        else:
            group_neutral.append(f"❌ {symbol}: Kein RSI-Streak")
        time.sleep(1)

    # Telegram-Report
    report = f"📊 RSI-Streak-Report ({timestamp})\n\n"
    if group_streaks:
        report += "🔥 RSI-Streaks erkannt:\n" + "\n".join(group_streaks) + "\n\n"
    if group_setups:
        report += "⚠️ Potenzielle Setups (3/4):\n" + "\n".join(group_setups) + "\n\n"
    report += "❌ Kein RSI-Streak oder Fehler:\n" + "\n".join(group_neutral)

    send_telegram(report)
    print("✅ RSI-Analyse abgeschlossen.")

if __name__ == "__main__":
    main()
