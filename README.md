# 🔥 Smart LPG Monitoring System

A web-based dashboard for monitoring LPG gas-level readings, visualizing trends, and tracking alerts. The project combines a Flask backend, an interactive dashboard, and an SQLite database to demonstrate how a gas monitoring system can work.

> **Note:** The current web dashboard uses simulated readings for demonstration. It is not yet connected to a physical gas sensor.

## ✨ Features

- **Live Dashboard Updates** – Displays automatically refreshed gas-level readings.
- **System Status Monitoring** – Shows NORMAL, CAUTION, or DANGER based on configurable thresholds.
- **Interactive Gas-Level Chart** – Visualizes readings and caution/danger thresholds over time.
- **Threshold Adjustment** – Change the warning threshold using a slider.
- **Simulation Controls** – Test Normal, Warning, and Danger scenarios without physical hardware.
- **Alert Event Tracking** – Displays status changes during a session.
- **SQLite Database** – Stores simulated readings, timestamps, thresholds, and statuses.
- **Reading History** – View previously saved readings in a table.
- **Statistics** – Displays the total number of saved readings and the highest recorded reading.

## 🛠️ Technologies Used

| Technology | Purpose |
|---|---|
| Python | Backend programming |
| Flask | Web server and API |
| HTML and CSS | Dashboard structure and styling |
| JavaScript | Dashboard interactions and automatic updates |
| Chart.js | Gas-level trend visualization |
| SQLite | Local storage of reading history |
| Arduino and MQ-2 sensor | Intended hardware integration |

## 📁 Project Structure

```text
Smart-LPG-Monitoring/
├── app.py
├── dashboard.html
├── requirements.txt
├── .gitignore
└── README.md
```

The SQLite database (`lpg_monitor.db`) is generated locally when the backend runs and is excluded from Git tracking.

## 🚀 Getting Started

### Prerequisites

- Python 3
- Git
- A web browser

### 1. Clone the repository

```bash
git clone https://github.com/NavyaMariamJohn/Smart-LPG-Monitoring.git
cd Smart-LPG-Monitoring
```

### 2. Create a virtual environment (recommended)

```bash
python -m venv .venv
```

Activate it on Windows:

```powershell
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

If you don't have a `requirements.txt` file yet, install Flask directly:

```bash
pip install Flask
```

### 4. Run the application

```bash
python app.py
```

### 5. Open the dashboard

Visit the following address in your browser:

**http://127.0.0.1:5000**

The application will create its local SQLite database automatically and begin generating simulated readings.

## 🧪 Testing the Dashboard

1. Open the dashboard in your browser.
2. Observe the current simulated reading and system status.
3. Select **Simulate Normal**, **Simulate Warning**, or **Simulate Danger**.
4. Adjust the warning threshold using the slider.
5. Observe the chart and alert events.
6. Check the saved history table and database statistics.

The default caution threshold is 300 units, with danger beginning at 500 units. These are demonstration thresholds, not calibrated LPG concentration measurements.

## 🔌 Planned Hardware Integration

The project is intended to integrate an Arduino-based gas monitoring circuit using an MQ-2 gas sensor, an LED, and a buzzer.

The planned hardware workflow is:

1. The MQ-2 sensor detects changes in gas concentration.
2. The Arduino reads the sensor output.
3. The Arduino activates local LED and buzzer alerts according to its programmed threshold.
4. Sensor readings can subsequently be sent to the Flask application for visualization and logging.

**Hardware integration is still pending.** The current web dashboard does not receive live sensor measurements.

## 🔮 Future Enhancements

- Connect the Arduino to the Flask backend using serial communication.
- Display actual sensor readings on the dashboard.
- Synchronize hardware alerts with dashboard status indicators.
- Improve historical analysis and reporting.
- Explore remote notifications for critical conditions.

## ⚠️ Safety Disclaimer

This is an educational prototype, not a certified LPG leak detection or safety device. Simulated readings do not indicate actual gas concentration. Do not rely on this project for real-world gas leak protection.

## 👩‍💻 Author

**Navya Mariam John**

GitHub: [@NavyaMariamJohn](https://github.com/NavyaMariamJohn)

## 📄 License

This project is developed for educational and academic purposes. A formal open-source license has not yet been specified.
