
import random

MODES = {
    "normal": (180, 220),
    "warning": (380, 420),
    "danger": (630, 670),
}

print("Smart LPG - Serial Simulator")
print("Choose: normal, warning, danger, or exit")

while True:
    mode = input("\nMode: ").strip().lower()

    if mode == "exit":
        print("Simulator stopped.")
        break

    if mode not in MODES:
        print("Invalid mode. Try normal, warning, or danger.")
        continue

    low, high = MODES[mode]
    reading = random.randint(low, high)

    # Simulated Arduino serial message
    print(f"Received: {reading}")
