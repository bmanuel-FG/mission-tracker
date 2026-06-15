# Mission Tracker

A professional Windows desktop application for tracking client mission portfolio progress, weekly updates, and incident tickets.

## Features

- **Dashboard** — Summary cards, status breakdowns, portfolio progress
- **Missions** — Full mission table with search, sort, and filter
- **Portfolios** — Per-portfolio progress and completion tracking
- **Weekly Update** — Diff view comparing latest import to previous
- **Tickets / Incidents** — Issue tracking linked to mission records
- **Import / Export** — CSV import from external systems; CSV export for all views

## Requirements

- Python 3.11+
- Windows 10/11 (for `.exe` packaging)

## Setup (Development)

```bash
# 1. Clone the repo
git clone <repo-url>
cd mission-tracker

# 2. Create virtual environment
python -m venv .venv
.venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the app
python -m app.main
```

The SQLite database is created automatically at `data/mission_tracker.db` on first launch.

## CSV Import Format

The import expects a CSV with at minimum these columns (column names are flexible — mapped during import):

| Column | Description |
|---|---|
| Mission ID | Unique mission identifier |
| Client | Client name |
| Portfolio | Portfolio name |
| Status | Current mission status |
| Date | Mission date or created date |

Additional columns are stored as-is.

## Build (Windows .exe)

```bash
# Activate venv first, then:
python build.py
```

Output: `dist/MissionTracker.exe`

## Project Structure

```
mission-tracker/
├── app/
│   ├── main.py              # Entry point
│   ├── database/
│   │   ├── schema.py        # SQLite schema & auto-creation
│   │   └── models.py        # Data access layer
│   ├── ui/
│   │   ├── main_window.py   # Main window + sidebar
│   │   ├── dashboard.py
│   │   ├── missions.py
│   │   ├── portfolios.py
│   │   ├── weekly_update.py
│   │   ├── tickets.py
│   │   └── import_export.py
│   └── services/
│       ├── csv_import.py    # Import + diff engine
│       └── csv_export.py    # All export formats
├── data/                    # Local DB (gitignored)
├── requirements.txt
├── build.py                 # PyInstaller build script
└── README.md
```

## Commit History

| Milestone | Tag |
|---|---|
| Initial project setup | v0.1 |
| Database schema | v0.2 |
| CSV import/export | v0.3 |
| Dashboard UI | v0.4 |
| Portfolio tracking | v0.5 |
| Weekly update tracking | v0.6 |
| Ticketing system | v0.7 |
| Packaging / build | v0.8 |
