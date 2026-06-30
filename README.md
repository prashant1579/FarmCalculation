# Farm Profit Clarity System

## Quick Start

### 1. Install dependencies (one-time)
```bash
pip install flask flask-cors
```

### 2. Start the backend
```bash
python server.py
```
Server runs at **http://localhost:5050**  
SQLite database auto-creates as `farm.db` in the same folder.

### 3. Open the app
Open `index.html` in your browser, **or** visit http://localhost:5050

---

## Features
- ✅ **Unlimited crops** — Corn, Soybeans, Wheat, Cotton, Rice, any name you enter
- ✅ **Real SQLite database** via Flask backend — all reports persist between sessions
- ✅ **Full report** — margin/acre, break-even, fertilizer +10% scenario, farm totals, recommendations
- ✅ **History tab** — browse, load, and delete past reports
- ✅ **Offline fallback** — if backend isn't running, calculates in-browser (report not saved)
- ✅ **Print / PDF** — print-ready layout

## API Endpoints
| Method | Path | Description |
|--------|------|-------------|
| GET | /api/reports | List all reports |
| POST | /api/reports | Create report + crops |
| GET | /api/reports/:id | Get report with all crops |
| DELETE | /api/reports/:id | Delete report |

## Tech Stack
- **Frontend:** Vanilla HTML/CSS/JS — no framework, no build step
- **Backend:** Python Flask + SQLite (built-in)
- **Database:** `farm.db` — single file, no install needed
