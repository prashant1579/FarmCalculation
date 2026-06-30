#!/usr/bin/env python3
"""
Farm Profit Clarity System — Backend
Flask + SQLite  |  Run: python server.py
API served on http://localhost:5050
"""

import sqlite3
import json
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS   # pip install flask-cors

app = Flask(__name__, static_folder=".")
CORS(app)

DB_FILE = "farm.db"


# ── Database setup ───────────────────────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    with get_db() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS reports (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            farmer_name TEXT    NOT NULL,
            county      TEXT    NOT NULL,
            year        INTEGER NOT NULL,
            created_at  TEXT    NOT NULL
        );

        CREATE TABLE IF NOT EXISTS crops (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            report_id   INTEGER NOT NULL REFERENCES reports(id) ON DELETE CASCADE,
            name        TEXT    NOT NULL,
            acres       REAL    DEFAULT 0,
            yield_bu    REAL    DEFAULT 0,
            price_bu    REAL    DEFAULT 0,
            seed        REAL    DEFAULT 0,
            fertilizer  REAL    DEFAULT 0,
            chemicals   REAL    DEFAULT 0,
            fuel        REAL    DEFAULT 0,
            labor       REAL    DEFAULT 0,
            other       REAL    DEFAULT 0,
            -- computed (stored for quick reads)
            cost_per_acre   REAL DEFAULT 0,
            income_per_acre REAL DEFAULT 0,
            margin_per_acre REAL DEFAULT 0,
            total_margin    REAL DEFAULT 0,
            cost_per_bu     REAL DEFAULT 0,
            break_even      REAL DEFAULT 0,
            relation        TEXT DEFAULT ''
        );
        """)


def relation_label(price, break_even):
    if break_even <= 0:
        return "N/A"
    ratio = price / break_even
    if ratio >= 1.15:
        return "Favorable"
    elif ratio >= 0.95:
        return "Tight"
    else:
        return "Unfavorable"


def compute_crop(c: dict) -> dict:
    cost = c["seed"] + c["fertilizer"] + c["chemicals"] + c["fuel"] + c["labor"] + c["other"]
    income = c["yield_bu"] * c["price_bu"]
    margin = income - cost
    total  = margin * c["acres"]
    cpb    = cost / c["yield_bu"] if c["yield_bu"] > 0 else 0
    be     = cpb
    return {
        **c,
        "cost_per_acre":   round(cost,   4),
        "income_per_acre": round(income, 4),
        "margin_per_acre": round(margin, 4),
        "total_margin":    round(total,  4),
        "cost_per_bu":     round(cpb,    4),
        "break_even":      round(be,     4),
        "relation":        relation_label(c["price_bu"], be),
    }


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/api/reports")
def list_reports():
    with get_db() as db:
        rows = db.execute(
            "SELECT * FROM reports ORDER BY created_at DESC LIMIT 100"
        ).fetchall()
    return jsonify([dict(r) for r in rows])


@app.post("/api/reports")
def create_report():
    body = request.get_json(force=True)
    farmer = body.get("farmer_name", "").strip() or "Unknown"
    county = body.get("county", "").strip() or "-"
    year   = int(body.get("year", datetime.now().year))
    crops  = body.get("crops", [])

    if not crops:
        return jsonify({"error": "At least one crop is required."}), 400

    now = datetime.utcnow().isoformat()
    with get_db() as db:
        cur = db.execute(
            "INSERT INTO reports (farmer_name, county, year, created_at) VALUES (?,?,?,?)",
            (farmer, county, year, now)
        )
        report_id = cur.lastrowid

        for raw in crops:
            c = {
                "report_id":  report_id,
                "name":       raw.get("name", "Crop").strip(),
                "acres":      float(raw.get("acres", 0)),
                "yield_bu":   float(raw.get("yield_bu", 0)),
                "price_bu":   float(raw.get("price_bu", 0)),
                "seed":       float(raw.get("seed", 0)),
                "fertilizer": float(raw.get("fertilizer", 0)),
                "chemicals":  float(raw.get("chemicals", 0)),
                "fuel":       float(raw.get("fuel", 0)),
                "labor":      float(raw.get("labor", 0)),
                "other":      float(raw.get("other", 0)),
            }
            c = compute_crop(c)
            db.execute("""
                INSERT INTO crops
                  (report_id, name, acres, yield_bu, price_bu,
                   seed, fertilizer, chemicals, fuel, labor, other,
                   cost_per_acre, income_per_acre, margin_per_acre,
                   total_margin, cost_per_bu, break_even, relation)
                VALUES
                  (:report_id,:name,:acres,:yield_bu,:price_bu,
                   :seed,:fertilizer,:chemicals,:fuel,:labor,:other,
                   :cost_per_acre,:income_per_acre,:margin_per_acre,
                   :total_margin,:cost_per_bu,:break_even,:relation)
            """, c)
        db.commit()

    return get_report(report_id)


@app.get("/api/reports/<int:rid>")
def get_report(rid):
    with get_db() as db:
        r = db.execute("SELECT * FROM reports WHERE id=?", (rid,)).fetchone()
        if not r:
            return jsonify({"error": "Not found"}), 404
        crops = db.execute(
            "SELECT * FROM crops WHERE report_id=? ORDER BY id", (rid,)
        ).fetchall()
    return jsonify({"report": dict(r), "crops": [dict(c) for c in crops]})


@app.delete("/api/reports/<int:rid>")
def delete_report(rid):
    with get_db() as db:
        db.execute("DELETE FROM reports WHERE id=?", (rid,))
        db.commit()
    return jsonify({"deleted": rid})


# Serve the frontend
@app.get("/")
def index():
    return send_from_directory(".", "index.html")


if __name__ == "__main__":
    init_db()
    print("Farm DB ready -", DB_FILE)
    print("Server: http://localhost:5050")
    app.run(port=5050, debug=True)
