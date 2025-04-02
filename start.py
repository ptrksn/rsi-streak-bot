import sys
import subprocess

print("📢 Starte Start-Skript...")

if len(sys.argv) > 1:
    task = sys.argv[1]
    print(f"📦 TASK: {task}")

    if task == "rsi":
        print("▶️ Starte RSI-Skript...")
        result = subprocess.run(["python3", "tradingview_rsi_streak.py"], capture_output=True, text=True)
        print(result.stdout)
        print(result.stderr)
    elif task == "watchdog":
        print("▶️ Starte Watchdog-Skript...")
        result = subprocess.run(["python3", "phemex_watchdog.py"], capture_output=True, text=True)
        print(result.stdout)
        print(result.stderr)
    elif task == "update_coins":
        print("🔁 Aktualisiere stabile Top 30 Coins...")
        result = subprocess.run(["python3", "update_stable_top30.py"], capture_output=True, text=True)
        print(result.stdout)
        print(result.stderr)
    else:
        print(f"❌ Unbekannte Aufgabe: {task}")
else:
    print("❌ Kein Argument übergeben. Bitte z. B. 'rsi', 'watchdog' oder 'update_coins' angeben.")
