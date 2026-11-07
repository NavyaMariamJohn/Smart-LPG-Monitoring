# Smart LPG Monitoring System

An Arduino-based LPG gas leakage detection and alert prototype with a Flask web dashboard. An MQ-2 gas sensor is read by an Arduino Uno, which sounds a buzzer and lights an LED when the reading crosses a threshold. The same readings are sent over USB serial to a Flask application that logs them in SQLite and displays them on a live dashboard.

The circuit was first simulated in Wokwi and then built and tested on physical hardware. The dashboard also has a simulation mode for demonstration without the Arduino.

> **Educational prototype.** Sensor readings are raw 10-bit ADC values (0-1023), not calibrated gas concentrations, and the thresholds have not been calibrated against known LPG concentrations. This is not a certified safety device. Do not rely on it for real-world gas leak protection.

## System Overview

```
MQ-2 sensor --(A0)--> Arduino Uno --(D9)--> Buzzer
                          |        --(D8)--> Red LED (220 ohm resistor)
                          |
                  USB serial, 9600 baud
                          |
                          v
             Flask backend (pyserial thread)
                          |
                    SQLite database
                          |
                  Web dashboard (browser)
```

The local alert is produced by the Arduino alone and works without a computer. The Flask application only receives and displays readings; it cannot control the Arduino.

## Hardware

| Component | Arduino pin | Role |
|---|---|---|
| MQ-2 gas sensor module (analog output) | A0 | Gas sensing |
| 5 V active buzzer | D9 | Audible alert |
| Red LED with 220 ohm series resistor | D8 | Visual alert |

The circuit is assembled on a breadboard with jumper wires and powered from the Arduino's 5 V supply over USB.

## Arduino Program

The sketch reads the sensor with `analogRead(A0)` every 500 ms and sends the result over serial at 9600 baud:

- If the reading is greater than the threshold of **100**, the buzzer and LED are switched on and the sketch prints `WARNING: Gas level high!`.
- Otherwise both are switched off and it prints `Status: Normal`.
- Each reading is also printed as `Gas sensor reading: <value>`, which is the line the Flask application parses.

The threshold of 100 is a raw ADC count. The comparison is strictly "greater than", and there is no hysteresis or latching.

<!-- TODO: link the .ino sketch here once it is added to the repository. -->

## Wokwi Simulation

The circuit and sketch were first built and tested in the [Wokwi](https://wokwi.com/) simulator, using the same pin assignments as the physical circuit (sensor on A0, LED on D8, buzzer on D9). In simulation the sensor value is set manually, so it shows the logic of the design but not real sensor behaviour.

## Flask Monitoring Dashboard

### What it does

- **Hardware mode (default):** a background thread reads the Arduino over serial (default port `COM7`, 9600 baud), keeps only lines matching `Gas sensor reading: <n>` with `n` between 0 and 1023, and saves each reading to SQLite. If the port is lost, it retries every 3 seconds.
- **Simulation mode:** Flask generates normal, warning or danger readings itself, so the dashboard can be demonstrated without hardware.
- **Live dashboard:** polls the backend every 2 seconds and shows the current reading, a NORMAL / CAUTION / DANGER status, a Chart.js trend chart (last 30 readings) with caution and danger lines, and a hardware-connected or disconnected banner.
- **Adjustable threshold:** a slider sets the dashboard threshold from 100 to 800 (default 300). CAUTION starts at the threshold and DANGER at threshold + 200.
- **Data source controls:** buttons to switch between real hardware and simulation, and to generate Normal, Warning or Danger simulated readings.
- **History and statistics:** the latest 50 saved readings with source, status and threshold, plus the total number of saved readings and the highest recorded reading.
- **Session events:** a list of status changes during the current browser session and a count of times the status rose to CAUTION or DANGER.

### API endpoints

| Endpoint | Method | Purpose |
|---|---|---|
| `/` | GET | Serves the dashboard page |
| `/api/reading` | GET | Latest reading (hardware or simulated) |
| `/api/source` | POST | Switch between `hardware` and `simulation` |
| `/api/simulate` | POST | Generate a `normal`, `warning` or `danger` reading |
| `/api/history` | GET | Saved readings (default 50, maximum 500) |
| `/api/stats` | GET | Total readings and highest reading |

### Database

Readings are stored in a local SQLite file, `lpg_monitor.db`, created automatically on first run and excluded from Git. The `readings` table stores the reading, mode, status, threshold, a simulated flag and a timestamp.

### Two separate thresholds

The Arduino alert threshold (**100**) and the dashboard threshold (default **300**) are independent and are not synchronised. With the defaults, a hardware reading between 101 and 299 turns on the buzzer and LED while the dashboard still shows NORMAL. Dashboard statistics include both simulated and hardware readings.

## Technologies

| Technology | Use |
|---|---|
| Arduino Uno, MQ-2 sensor, buzzer, LED | Sensing and local alert (C/C++ sketch) |
| Wokwi | Circuit simulation |
| Python, Flask | Backend and REST API |
| pyserial | Reading Arduino data over USB serial |
| SQLite | Local storage of readings |
| HTML, CSS, JavaScript, Chart.js 4.4.1 | Dashboard (Chart.js is loaded from a CDN, so the chart needs an internet connection) |

## Getting Started

### Prerequisites

- Python 3
- A web browser
- For hardware mode: an Arduino Uno with the circuit above, connected over USB

### Run

```bash
git clone https://github.com/NavyaMariamJohn/Smart-LPG-Monitoring.git
cd Smart-LPG-Monitoring
python -m venv .venv
.venv\Scripts\Activate.ps1        # Windows PowerShell
pip install flask pyserial
python app.py
```

Open http://127.0.0.1:5000 in your browser.

- **Hardware mode:** set `SERIAL_PORT` in `app.py` to your Arduino's port (it is `COM7` by default), upload the sketch, and keep the Arduino connected.
- **Simulation mode:** click **Use Simulation** or one of the **Simulate** buttons. `pyserial` is still imported at startup, so install it even for simulation-only use.

## Testing Summary

| Test | Result |
|---|---|
| Wokwi simulation | Reading 364 gave `Status: Normal` with outputs off; reading 840 gave `WARNING: Gas level high!` with LED and pins on |
| Physical circuit, clean air | Readings of about 45-47 with `Status: Normal` |
| Physical circuit, gas exposure | `WARNING: Gas level high!` for every reading from 102 to 136; returned to `Status: Normal` at 99, matching the threshold of 100 |
| Local alert | LED lit and buzzer beeped while the reading stayed above the threshold, and both stopped when it returned to normal (buzzer behaviour was observed by the team, not recorded) |
| Dashboard logging | Arduino readings received over serial and saved to SQLite |

The gas source, distance and duration of exposure were not recorded. Response time, repeatability and false-alarm rate were not measured.

## Limitations

- Thresholds are raw ADC counts and have not been calibrated against known gas concentrations.
- The MQ-2 responds to smoke and several flammable gases and does not identify LPG specifically. Its readings depend on warm-up, temperature, humidity and sensor age. The sketch has no warm-up handling.
- The Arduino and dashboard thresholds are separate and not synchronised.
- The Arduino-to-computer link is one-way, and the dashboard cannot control the buzzer or LED.
- Local prototype only: fixed serial port, no authentication, Flask debug mode enabled, unbounded database growth, and a CDN-hosted chart library.
- Local alerts only: no remote notifications or automatic gas shut-off.
- Breadboard construction is suitable for a prototype, not a permanent installation. The sensor heater runs hot, so do not test near flames or sparks.

## Future Work

- Calibrate the sensor against known concentrations and set thresholds in ppm.
- Use one threshold for the Arduino and the dashboard, with hysteresis or averaging to reduce false alarms.
- Record gas exposure tests (source, distance, duration, response time) and test repeatability.
- Drive the buzzer through a transistor if its current exceeds the Arduino pin rating.
- Keep simulated and hardware data separate, and limit database growth.
- Add remote notifications and a safe shut-off mechanism.

## Project Information

Developed as an academic minor project at Government Engineering College Idukki (APJ Abdul Kalam Technological University).

Team: Aardhra S Nair, Sisira K S, Navya Mariam John
Project guide: Dr. Santhosh Kumar S

## License

Developed for educational and academic purposes. A formal open-source license has not been specified.
