import os
import requests
import time
import numpy as np
from tradingview_ta import TA_Handler, Interval, Exchange

CMC_API_KEY = os.getenv("CMC_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

PHEMEX_SYMBOLS_URL = "https://api.phemex.com/exchange/public/products"
CMC_URL = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"

RSI_PERIOD = 14
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30
MAX_COINS = 50


def send_telegram(message):
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
        try:
            requests.post(url, data=payload)
        except Exception as e:
            print(f"❌ Fehler bei Telegram: {e}")


def get_top_cmc_symbols():
    try:
        response = requests.get(
            CMC_URL,
            headers={"X-CMC_PRO_API_KEY": CMC_API_KEY},
            params={"limit": MAX_COINS, "sort": "volume_24h"},
        )
        data = response.json()
        return [f"{entry['symbol']}USDT" for entry in data["data"]]
    except Exception as e:
        print(f"❌ Fehler beim Abrufen der CMC-Symbole: {e}")
        return []


def get_phemex_symbols():
    try:
        response = requests.get(PHEMEX_SYMBOLS_URL)
        data = response.json()
        symbols = [item["symbol"] for item in data["data"] if item["type"] == "Perpetual"]
        return symbols
    except Exception as e:
        print(f"❌ Fehler beim Abrufen der Phemex-Symbole: {e}")
        return []


def check_rsi_streak(symbol):
    try:
        handler = TA_Handler(
            symbol=symbol,
            exchange="BINANCE",
            screener="crypto",
            interval=Interval.INTERVAL_4_HOURS
        )
        analysis = handler.get_analysis()
        rsi_series = analysis.indicators.get("RSI")

        if rsi_series is None:
            return symbol, None, "Keine RSI-Daten"

        rsi_value = analysis.indicators["RSI"]
        streak = 0
        if rsi_value < RSI_OVERSOLD:
            for rsi in analysis.indicators.values():
                if rsi < RSI_OVERSOLD:
                    streak += 1
                else:
                    break
            return symbol, rsi_value, f"🔽 RSI < {RSI_OVERSOLD} seit {streak} Kerzen"
        elif rsi_value > RSI_OVERBOUGHT:
            for rsi in analysis.indicators.values():
                if rsi > RSI_OVERBOUGHT:
                    streak += 1
                else:
                    break
            return symbol, rsi_value, f"🔼 RSI > {RSI_OVERBOUGHT} seit {streak} Kerzen"
        else:
            return symbol, rsi_value, None

    except Exception as e:
        return symbol, None, f"Fehler: {e}"


def main():
    print("🔍 RSI-Streak-Check via TradingView & CoinMarketCap...")
    cmc_symbols = get_top_cmc_symbols()
    phemex_symbols = get_phemex_symbols()

    symbols = [s for s in cmc_symbols if s.replace(".P", "") in phemex_symbols]
    print(f"📈 Analysiere {len(symbols)} Symbole: {symbols}...")

    messages = []

    for sym in symbols:
        print(f"📊 {sym}...")
        symbol, rsi, info = check_rsi_streak(sym)
        if info:
            print(f"{info}")
            messages.append(f"{symbol} (RSI: {rsi:.2f}) - {info}")
        else:
            print("ℹ️ Kein RSI-Streak.")
        time.sleep(1)

    if messages:
        report = "📊 RSI-Streak-Report (Phemex):\n" + "\n".join(messages)
    else:
        report = "❌ Kein Coin mit aktuellem RSI-Streak."

    print(report)
    send_telegram(report)


if __name__ == "__main__":
    main()
