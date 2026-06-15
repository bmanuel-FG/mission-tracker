"""SQLite schema creation and migration."""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[2] / "data" / "mission_tracker.db"


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def init_db() -> None:
    """Create all tables on first launch; safe to call on every launch."""
    with get_connection() as conn:
        conn.executescript("""
-- ─────────────────────────────────────────────
-- Core reference tables
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS clients (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL UNIQUE,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS portfolios (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL,
    client_id   INTEGER REFERENCES clients(id) ON DELETE SET NULL,
    notes       TEXT,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now')),
    UNIQUE(name, client_id)
);

-- ─────────────────────────────────────────────
-- Missions
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS missions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    mission_id      TEXT    NOT NULL UNIQUE,   -- external ID from CSV
    client_id       INTEGER REFERENCES clients(id) ON DELETE SET NULL,
    portfolio_id    INTEGER REFERENCES portfolios(id) ON DELETE SET NULL,
    status          TEXT    NOT NULL DEFAULT 'Unknown',
    mission_date    TEXT,
    location        TEXT,
    pilot           TEXT,
    notes           TEXT,
    raw_data        TEXT,   -- JSON blob of original CSV row
    created_at      TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_missions_status       ON missions(status);
CREATE INDEX IF NOT EXISTS idx_missions_portfolio_id ON missions(portfolio_id);
CREATE INDEX IF NOT EXISTS idx_missions_client_id    ON missions(client_id);

-- ─────────────────────────────────────────────
-- Mission status history
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS mission_status_history (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    mission_id  TEXT    NOT NULL,
    old_status  TEXT,
    new_status  TEXT    NOT NULL,
    changed_at  TEXT    NOT NULL DEFAULT (datetime('now')),
    source      TEXT    DEFAULT 'csv_import'   -- 'csv_import' | 'manual'
);

-- ─────────────────────────────────────────────
-- CSV import tracking
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS csv_imports (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    filename        TEXT    NOT NULL,
    imported_at     TEXT    NOT NULL DEFAULT (datetime('now')),
    rows_total      INTEGER NOT NULL DEFAULT 0,
    rows_added      INTEGER NOT NULL DEFAULT 0,
    rows_updated    INTEGER NOT NULL DEFAULT 0,
    rows_unchanged  INTEGER NOT NULL DEFAULT 0,
    notes           TEXT
);

CREATE TABLE IF NOT EXISTS import_changes (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    import_id       INTEGER NOT NULL REFERENCES csv_imports(id) ON DELETE CASCADE,
    mission_id      TEXT    NOT NULL,
    change_type     TEXT    NOT NULL,   -- 'added' | 'updated' | 'unchanged'
    field_name      TEXT,               -- which field changed
    old_value       TEXT,
    new_value       TEXT,
    changed_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_import_changes_import_id  ON import_changes(import_id);
CREATE INDEX IF NOT EXISTS idx_import_changes_mission_id ON import_changes(mission_id);

-- ─────────────────────────────────────────────
-- Tickets / Incidents
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS tickets (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id       TEXT    NOT NULL UNIQUE,  -- e.g. TKT-0001
    mission_id      TEXT    NOT NULL,
    client          TEXT,
    portfolio       TEXT,
    mission_status  TEXT,
    description     TEXT    NOT NULL,
    category        TEXT,
    priority        TEXT    NOT NULL DEFAULT 'Medium',
    status          TEXT    NOT NULL DEFAULT 'Open',
    assigned_owner  TEXT,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT    NOT NULL DEFAULT (datetime('now')),
    resolved_at     TEXT
);

CREATE INDEX IF NOT EXISTS idx_tickets_mission_id ON tickets(mission_id);
CREATE INDEX IF NOT EXISTS idx_tickets_status     ON tickets(status);

CREATE TABLE IF NOT EXISTS ticket_notes (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id   TEXT    NOT NULL REFERENCES tickets(ticket_id) ON DELETE CASCADE,
    note        TEXT    NOT NULL,
    author      TEXT,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- ─────────────────────────────────────────────
-- Weekly snapshots
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS weekly_snapshots (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_date   TEXT    NOT NULL,
    import_id       INTEGER REFERENCES csv_imports(id),
    total_missions  INTEGER,
    completed       INTEGER,
    invoiced        INTEGER,
    planning        INTEGER,
    cancelled       INTEGER,
    in_progress     INTEGER,
    overdue         INTEGER,
    summary_json    TEXT    -- full JSON breakdown for drill-down
);

-- ─────────────────────────────────────────────
-- App settings (key/value)
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS app_settings (
    key     TEXT PRIMARY KEY,
    value   TEXT
);

INSERT OR IGNORE INTO app_settings(key, value) VALUES
    ('theme', 'dark'),
    ('default_client', ''),
    ('ticket_counter', '0');
""")
