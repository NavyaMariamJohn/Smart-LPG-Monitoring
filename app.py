
import os
import random
import re
import sqlite3
import threading
import time
from datetime import datetime

import serial
from flask import Flask, jsonify, render_template, request, send_from_directory

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "lpg_monitor.db")

SERIAL_PORT = "COM7"
BAUD_RATE = 9600

app = Flask(__name__)

MODE_BASE = {
    "normal": 200,
    "warning": 400,
    "danger": 650,
}
JITTER = 10

_lock = threading.Lock()
_state = {
    "source": "hardware",
    "mode": "normal",
    "threshold": 300,
    "latest_reading": None,
    "last_reading_time": None,
    "serial_connected": False,
    "serial_error": None,
}


# ---------- DATABASE ----------

def get_db():
    connection = sqlite3.connect(DB_PATH, timeout=10)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    with get_db() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                gas_reading INTEGER NOT NULL,
                mode TEXT NOT NULL,
                status TEXT NOT NULL,
                threshold INTEGER NOT NULL,
                simulated INTEGER NOT NULL DEFAULT 1,
                timestamp TEXT NOT NULL
            )
        """)
        connection.commit()


# ---------- STATUS AND READINGS ----------

def get_status(reading, threshold):
    if reading >= threshold + 200:
        return "DANGER"
    if reading >= threshold:
        return "CAUTION"
    return "NORMAL"


def save_reading(reading, mode, threshold, simulated):
    timestamp = datetime.now().isoformat(timespec="seconds")
    status = get_status(reading, threshold)

    with get_db() as connection:
        connection.execute("""
            INSERT INTO readings
            (gas_reading, mode, status, threshold, simulated, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            reading, mode, status, threshold,
            1 if simulated else 0, timestamp
        ))
        connection.commit()

    return {
        "reading": reading,
        "mode": mode,
        "status": status,
        "threshold": threshold,
        "simulated": simulated,
        "timestamp": timestamp,
    }


def make_reading(mode):
    return max(
        0,
        MODE_BASE[mode] + random.randint(-JITTER, JITTER)
    )


def get_threshold():
    try:
        value = int(request.args.get("threshold", 300))
        return max(100, min(800, value))
    except (ValueError, TypeError):
        return 300


# ---------- ARDUINO SERIAL READER ----------

def serial_reader():
    """Read actual numeric sensor readings from the Arduino."""
    pattern = re.compile(r"Gas sensor reading:\s*(\d+)", re.IGNORECASE)

    while True:
        try:
            print(f"Connecting to Arduino on {SERIAL_PORT}...")

            with serial.Serial(
                SERIAL_PORT,
                BAUD_RATE,
                timeout=2
            ) as arduino:
                # Opening serial may reset the Arduino.
                time.sleep(2)
                arduino.reset_input_buffer()

                with _lock:
                    _state["serial_connected"] = True
                    _state["serial_error"] = None

                print(f"Arduino connected on {SERIAL_PORT}")

                while True:
                    line = arduino.readline().decode(
                        "utf-8", errors="replace"
                    ).strip()

                    match = pattern.search(line)
                    if not match:
                        continue

                    reading = int(match.group(1))

                    # Arduino UNO analogRead normally returns 0–1023.
                    if not 0 <= reading <= 1023:
                        print("Ignoring invalid reading:", reading)
                        continue

                    timestamp = datetime.now().isoformat(
                        timespec="seconds"
                    )

                    with _lock:
                        threshold = _state["threshold"]
                        source = _state["source"]
                        _state["latest_reading"] = reading
                        _state["last_reading_time"] = timestamp

                    # Save hardware readings only when hardware mode
                    # is selected. Simulation remains independent.
                    if source == "hardware":
                        save_reading(
                            reading,
                            "hardware",
                            threshold,
                            simulated=False
                        )

        except (serial.SerialException, OSError) as error:
            with _lock:
                _state["serial_connected"] = False
                _state["serial_error"] = str(error)

            print("Arduino serial connection unavailable:", error)
            print("Retrying in 3 seconds...")
            time.sleep(3)


# ---------- WEB PAGE ----------

@app.route("/")
def index():
    if os.path.exists(
        os.path.join(BASE_DIR, "templates", "dashboard.html")
    ):
        return render_template("dashboard.html")

    return send_from_directory(BASE_DIR, "dashboard.html")


# ---------- LATEST READING ----------

@app.route("/api/reading")
def get_reading():
    threshold = get_threshold()

    with _lock:
        _state["threshold"] = threshold
        source = _state["source"]
        mode = _state["mode"]
        reading = _state["latest_reading"]
        timestamp = _state["last_reading_time"]
        connected = _state["serial_connected"]
        error = _state["serial_error"]

    if source == "simulation":
        reading = make_reading(mode)
        payload = save_reading(
            reading, mode, threshold, simulated=True
        )
        payload["source"] = "simulation"
        payload["connected"] = connected
        return jsonify(payload)

    if reading is None:
        return jsonify({
            "reading": 0,
            "mode": "hardware",
            "status": "WAITING",
            "threshold": threshold,
            "simulated": False,
            "source": "hardware",
            "connected": connected,
            "error": error,
            "timestamp": timestamp,
        })

    return jsonify({
        "reading": reading,
        "mode": "hardware",
        "status": get_status(reading, threshold),
        "threshold": threshold,
        "simulated": False,
        "source": "hardware",
        "connected": connected,
        "timestamp": timestamp,
    })


# ---------- SWITCH DATA SOURCE ----------

@app.route("/api/source", methods=["POST"])
def set_source():
    data = request.get_json(silent=True) or {}
    source = data.get("source")

    if source not in ("hardware", "simulation"):
        return jsonify({
            "error": "source must be hardware or simulation"
        }), 400

    with _lock:
        _state["source"] = source

    return jsonify({
        "source": source,
        "message": f"Data source changed to {source}"
    })


# ---------- EXISTING SIMULATION BUTTONS ----------

@app.route("/api/simulate", methods=["POST"])
def simulate():
    data = request.get_json(silent=True) or {}
    mode = data.get("mode")

    if mode not in MODE_BASE:
        return jsonify({
            "error": "mode must be normal, warning or danger"
        }), 400

    try:
        threshold = int(data.get("threshold", 300))
        threshold = max(100, min(800, threshold))
    except (ValueError, TypeError):
        threshold = 300

    with _lock:
        _state["source"] = "simulation"
        _state["mode"] = mode
        _state["threshold"] = threshold

    reading = make_reading(mode)
    payload = save_reading(
        reading, mode, threshold, simulated=True
    )
    payload["source"] = "simulation"
    return jsonify(payload)


# ---------- DATABASE HISTORY ----------

@app.route("/api/history")
def get_history():
    try:
        limit = int(request.args.get("limit", 50))
        limit = max(1, min(500, limit))
    except (ValueError, TypeError):
        limit = 50

    with get_db() as connection:
        rows = connection.execute("""
            SELECT id, gas_reading, mode, status,
                   threshold, simulated, timestamp
            FROM readings
            ORDER BY id DESC
            LIMIT ?
        """, (limit,)).fetchall()

    return jsonify([dict(row) for row in rows])


@app.route("/api/stats")
def get_stats():
    with get_db() as connection:
        result = connection.execute("""
            SELECT COUNT(*) AS total_readings,
                   MAX(gas_reading) AS highest_reading
            FROM readings
        """).fetchone()

    return jsonify({
        "total_readings": result["total_readings"],
        "highest_reading": result["highest_reading"],
        "database": os.path.basename(DB_PATH),
    })


# ---------- START APPLICATION ----------

if __name__ == "__main__":
    init_db()

    reader_thread = threading.Thread(
        target=serial_reader,
        daemon=True
    )
    reader_thread.start()

    print("SQLite database:", DB_PATH)
    print("Arduino port:", SERIAL_PORT)
    print("Dashboard: http://127.0.0.1:5000")

    # Disable the reloader so it doesn't create a second serial reader.
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True,
        use_reloader=False
    )
