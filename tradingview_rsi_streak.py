import os
import datetime
from tradingview_ta import TA_Handler, Interval, Exchange
import requests

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

TOP_SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "XRPUSDT", "BNBUSDT", "SOLUSDT", "DOGEUSDT", "ADAUSDT",
    "AVAXUSDT", "LINKUSDT", "UNIUSDT", "LTCUSDT", "TRXUSDT", "DOTUSDT", "SHIBUSDT",
    "BCHUSDT", "AAVEUSDT", "MATICUSDT", "FTMUSDT", "EOSUSDT", "MASKUSDT", "COMPUSDT",
    "SANDUSDT", "GRTUSDT", "NEARUSDT", "APTUSDT", "RNDRUSDT", "INJUSDT", "ARBUSDT",
    "STXUSDT", "LDOUSDT", "CRVUSDT", "SNXUSDT", "MKRUSDT", "IMXUSDT", "DYDXUSDT",
    "FLOWUSDT", "PEPEUSDT", "BLURUSDT", "GMTUSDT", "OPUSDT", "ATOMUSDT", "MEWUSDT"
]

def send_telegram_message(msg):
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": msg})
    else:
        print("⚠️ Telegram-Konfiguration fehlt.")

def get_rsi_values(symbol):
    handler = TA_Handler(
        symbol=symbol,
        screener="crypto",
        exchange="BINANCE",
        interval=Interval.INTERVAL_4_HOURS,
    )
    try:
        analysis = handler.get_analysis()
        rsi_data = analysis.indicators.get("RSI", None)
        if isinstance(rsi_data, list) and len(rsi_data) >= 1:
            return rsi_data[-1], rsi_data
        elif isinstance(rsi_data, (int, float)):
            return rsi_data, [rsi_data]
        else:
            return None, []
    except Exception as e:
        print(f"❌ Fehler bei {symbol}: {e}")
        return None, []

def check_rsi_streak(rsi_values):
    if not isinstance(rsi_values, list) or len(rsi_values) < 4:
        return None

    last_4 = rsi_values[-4:]
    low_count = sum(1 for r in last_4 if r < 30)
    high_count = sum(1 for r in last_4 if r > 70)

    if low_count == 4:
        return "RSI unter 30 – Long Setup möglich"
    elif high_count == 4:
        return "RSI über 70 – Short Setup möglich"
    elif low_count == 3:
        return "RSI unter 30 – ⚠️ Long Setup denkbar"
    elif high_count == 3:
        return "RSI über 70 – ⚠️ Short Setup denkbar"
    return None

def main():
    print("🔍 RSI-Streak-Check via TradingView...")

    summary = []
    streaks = []

    now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    summary.append(f"📊 RSI-Streak-Report ({now})\n")

    print(f"📈 Analysiere {len(TOP_SYMBOLS)} Symbole: {TOP_SYMBOLS[:5]}...")

    for symbol in TOP_SYMBOLS:
        print(f"📊 {symbol}...")
        rsi, rsi_values = get_rsi_values(symbol)
        if rsi is None:
            summary.append(f"❌ {symbol}: Fehler bei RSI")
            continue

        status = check_rsi_streak(rsi_values)
        if status:
            streaks.append(f"{symbol}: {status}")
        else:
            summary.append(f"❌ {symbol}: Kein RSI-Streak")

    if streaks:
        summary.insert(1, "📉 Aktuelle RSI-Streaks:")
        summary.extend(streaks)
    else:
        summary.insert(1, "❌ Kein Coin mit aktuellem RSI-Streak.")

    summary.append("✅ RSI-Analyse abgeschlossen.")
    send_telegram_message("\n".join(summary))

if __name__ == "__main__":
    main()
