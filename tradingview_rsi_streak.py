import os
import datetime
from tradingview_ta import TA_Handler, Interval, Exchange
from dotenv import load_dotenv
import requests

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
CMC_API_KEY = os.getenv("CMC_API_KEY")

RSI_PERIODS = 4  # Anzahl der 4h-Kerzen
LONG_THRESHOLD = 30
SHORT_THRESHOLD = 70

PH_SUPPORTED = [  # Gültige Phemex-Perpetuals
    "BTCUSDT", "ETHUSDT", "XRPUSDT", "LINKUSDT", "LTCUSDT",
    "ADAUSDT", "DOTUSDT", "UNIUSDT", "AAVEUSDT", "BCHUSDT"
]


def get_top_cmc_symbols(limit=50):
    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"
    headers = {"X-CMC_PRO_API_KEY": CMC_API_KEY}
    params = {"sort": "volume_24h", "limit": limit}
    try:
        response = requests.get(url, headers=headers, params=params)
        data = response.json()["data"]
        symbols = [entry["symbol"] + "USDT" for entry in data]
        return [s for s in symbols if s in PH_SUPPORTED]
    except Exception as e:
        print(f"❌ Fehler bei CMC: {e}")
        return []


def get_rsi_values(symbol):
    handler = TA_Handler(
        symbol=symbol,
        exchange="BINANCE",
        screener="crypto",
        interval=Interval.INTERVAL_4_HOURS,
    )
    try:
        analysis = handler.get_analysis()
        rsi_list = analysis.indicators.get("RSI", None)
        if isinstance(rsi_list, list):
            return rsi_list[-RSI_PERIODS:]
        else:
            return [rsi_list] * RSI_PERIODS
    except Exception as e:
        print(f"❌ Fehler bei {symbol}: {e}")
        return None


def detect_rsi_streak(rsi_values):
    below_30 = [r < LONG_THRESHOLD for r in rsi_values]
    above_70 = [r > SHORT_THRESHOLD for r in rsi_values]
    
    if all(below_30):
        return ("LONG", RSI_PERIODS)
    elif all(above_70):
        return ("SHORT", RSI_PERIODS)
    elif sum(below_30) in [2, 3] and below_30[-1]:
        return ("LONG_POSSIBLE", sum(below_30))
    elif sum(above_70) in [2, 3] and above_70[-1]:
        return ("SHORT_POSSIBLE", sum(above_70))
    else:
        return None


def send_telegram_report(full_message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Telegram-Konfiguration fehlt.")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": full_message})
    except Exception as e:
        print(f"❌ Telegram-Fehler: {e}")


def main():
    print("🔍 RSI-Streak-Check via TradingView...")
    symbols = get_top_cmc_symbols(50)
    print(f"📈 Analysiere {len(symbols)} Symbole: {symbols}...")

    results = []
    possible_setups = []

    for symbol in symbols:
        print(f"📊 {symbol}...")
        rsi_vals = get_rsi_values(symbol)
        if not rsi_vals or len(rsi_vals) < RSI_PERIODS:
            results.append(f"❌ {symbol}: Keine oder zu wenig RSI-Daten.")
            continue

        current_rsi = rsi_vals[-1]
        streak_info = detect_rsi_streak(rsi_vals)

        if streak_info:
            kind, count = streak_info
            if kind == "LONG":
                results.append(f"✅ {symbol}: {count}x RSI < 30 → Long Setup aktiv!")
            elif kind == "SHORT":
                results.append(f"✅ {symbol}: {count}x RSI > 70 → Short Setup aktiv!")
            elif kind == "LONG_POSSIBLE":
                possible_setups.append(f"- {symbol}: {count}x RSI < 30 → Long Setup möglich")
            elif kind == "SHORT_POSSIBLE":
                possible_setups.append(f"- {symbol}: {count}x RSI > 70 → Short Setup denkbar")
        else:
            results.append(f"❌ {symbol}: Kein RSI-Streak")

    now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    message = f"📊 RSI-Streak-Report ({now})\n"

    if possible_setups:
        message += "\n🚀 Mögliche Setups:\n" + "\n".join(possible_setups)
    message += "\n\n📉 Aktuelle RSI-Streaks:\n" + "\n".join(results)

    send_telegram_report(message)
    print(message)


if __name__ == "__main__":
    main()
