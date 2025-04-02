from tradingview_ta import TA_Handler, Interval, Exchange

symbol = "BTCUSDT"

handler = TA_Handler(
    symbol=symbol,
    exchange="BINANCE",
    screener="crypto",
    interval=Interval.INTERVAL_4_HOURS
)

try:
    analysis = handler.get_analysis()
    rsi = analysis.indicators["RSI"]
    print(f"📊 Aktueller RSI für {symbol} (4h): {rsi}")
except Exception as e:
    print("❌ Fehler beim Abrufen:", e)
