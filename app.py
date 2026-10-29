
import os
import random
import sqlite3
from datetime import datetime
from threading import Lock

from flask import Flask, jsonify, render_template, request, send_from_directory

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "lpg_monitor.db")

app = Flask(__name__)

MODE_BASE = {
    "normal": 200,
    "warning": 400,
    "danger": 650
}
JITTER = 10

_state = {"mode": "normal"}
_lock = Lock()


# ---------- DATABASE SETUP ----------

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


# ---------- SENSOR SIMULATION ----------

def make_reading(mode):
    base = MODE_BASE[mode]
    return max(0, base + random.randint(-JITTER, JITTER))


def get_status(reading, threshold):
    if reading >= threshold + 200:
        return "DANGER"
    if reading >= threshold:
        return "CAUTION"
    return "NORMAL"


def save_reading(reading, mode, threshold):
    timestamp = datetime.now().isoformat(timespec="seconds")
    status = get_status(reading, threshold)

    with get_db() as connection:
        connection.execute("""
            INSERT INTO readings
            (gas_reading, mode, status, threshold, simulated, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (reading, mode, status, threshold, 1, timestamp))
        connection.commit()

    return {
        "reading": reading,
        "mode": mode,
        "status": status,
        "threshold": threshold,
        "simulated": True,
        "timestamp": timestamp
    }


def reading_payload(mode, threshold=300):
    reading = make_reading(mode)
    return save_reading(reading, mode, threshold)


# ---------- WEB PAGES ----------

@app.route("/")
def index():
    if os.path.exists(os.path.join(BASE_DIR, "templates", "dashboard.html")):
        return render_template("dashboard.html")
    return send_from_directory(BASE_DIR, "dashboard.html")


# ---------- API: LATEST READING ----------

@app.route("/api/reading")
def get_reading():
    with _lock:
        mode = _state["mode"]

    try:
        threshold = int(request.args.get("threshold", 300))
        threshold = max(100, min(800, threshold))
    except (ValueError, TypeError):
        threshold = 300

    return jsonify(reading_payload(mode, threshold))


# ---------- API: SIMULATION BUTTONS ----------

@app.route("/api/simulate", methods=["POST"])
def simulate():
    data = request.get_json(silent=True) or {}
    mode = data.get("mode")

    if mode not in MODE_BASE:
        return jsonify({
            "error": "mode must be normal, warning or danger"
        }), 400

    with _lock:
        _state["mode"] = mode

    try:
        threshold = int(data.get("threshold", 300))
        threshold = max(100, min(800, threshold))
    except (ValueError, TypeError):
        threshold = 300

    return jsonify(reading_payload(mode, threshold))


# ---------- API: DATABASE HISTORY ----------

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
        "database": os.path.basename(DB_PATH)
    })


if __name__ == "__main__":
    init_db()
    print("SQLite database:", DB_PATH)
    print("Dashboard: http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=True)
