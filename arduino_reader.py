
import serial
import time

PORT = "COM7"
BAUD_RATE = 9600

try:
    with serial.Serial(PORT, BAUD_RATE, timeout=2) as arduino:
        print(f"Connected to Arduino on {PORT}")
        print("Reading sensor output... Press Ctrl+C to stop.\n")

        # Arduino may reset when the serial port opens.
        time.sleep(2)
        arduino.reset_input_buffer()

        while True:
            line = arduino.readline().decode(
                "utf-8", errors="replace"
            ).strip()

            if line:
                print("Arduino:", line)

except serial.SerialException as error:
    print(f"Serial connection error: {error}")
    print("Check the COM port and close Arduino Serial Monitor.")

except KeyboardInterrupt:
    print("\nStopped reading Arduino.")
