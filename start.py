import sys
import subprocess

print("📢 Starte Start-Skript...")

if len(sys.argv) > 1:
    task = sys.argv[1]
    print(f"📦 TASK: {task}")

    if task == "rsi":
        print("▶️ Starte RSI-Skript...")
        subprocess.run(["python", "phemex_rsi_auth.py"])
    elif task == "watchdog":
        print("▶️ Starte Watchdog-Skript...")
        subprocess.run(["python", "phemex_watchdog.py"])
    else:
        print(f"❌ Unbekannte Aufgabe: {task}")
else:
    print("❌ Kein Argument übergeben. Bitte z. B. 'rsi' oder 'watchdog' angeben.")
