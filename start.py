if task == "rsi":
    print("▶️ Starte RSI-Streak-Bot...")
    result = subprocess.run(["python", "phemex_rsi_streak.py"], capture_output=True, text=True)
    print(result.stdout)
    print(result.stderr)
