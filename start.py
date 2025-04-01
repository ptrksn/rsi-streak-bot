# start.py
import sys
import subprocess

if len(sys.argv) > 1:
    task = sys.argv[1]

    if task == "rsi":
        subprocess.run(["python", "phemex_rsi_auth.py"])
    elif task == "watchdog":
        subprocess.run(["python", "phemex_watchdog.py"])
    else:
        print(f"❌ Unbekannte Aufgabe: {task}")
else:
    print("❌ Kein Argument übergeben. Bitte z. B. 'rsi' oder 'watchdog' angeben.")
