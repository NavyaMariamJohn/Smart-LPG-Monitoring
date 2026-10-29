
import random
import time

MODES = {
    "normal": (180, 220),
    "warning": (380, 420),
    "danger": (630, 670),
}

print("Smart LPG - Serial Simulator")
print("Choose a mode: normal, warning, danger")
print("Type 'exit' to stop.\n")

mode = "normal"

try:
    while True:
        user_input = input(
            "Mode (Enter keeps current mode): "
        ).strip().lower()

        if user_input == "exit":
            break

        if user_input in MODES:
            mode = user_input
        elif user_input:
            print("Invalid mode. Choose normal, warning or danger.")
            continue

        low, high = MODES[mode]
        reading = random.randint(low, high)

        # Imitate one line sent by an Arduino.
        print(f"Arduino would send: {reading}")
        time.sleep(0.5)

except KeyboardInterrupt:
    print("\nSimulator stopped.")

print("Goodbye!")
