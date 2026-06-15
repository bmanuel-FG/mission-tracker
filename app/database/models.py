"""All data-access functions — thin wrappers around SQLite."""
import json
import sqlite3
from datetime import datetime
from typing import Any

from .schema import get_connection


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def _row_to_dict(row: sqlite3.Row) -> dict:
    return dict(row) if row else {}


def _rows_to_list(rows) -> list[dict]:
    return [dict(r) for r in rows]


def now() -> str:
    return datetime.utcnow().isoformat(sep=" ", timespec="seconds")


# ─────────────────────────────────────────────
# Settings
# ─────────────────────────────────────────────

def get_setting(key: str, default: str = "") -> str:
    with get_connection() as conn:
        row = conn.execute("SELECT value FROM app_settings WHERE key=?", (key,)).fetchone()
        return row["value"] if row else default


def set_setting(key: str, value: str) -> None:
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO app_settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, value),
        )


# ─────────────────────────────────────────────
# Clients
# ─────────────────────────────────────────────

def get_or_create_client(name: str) -> int:
    name = name.strip()
    with get_connection() as conn:
        row = conn.execute("SELECT id FROM clients WHERE name=?", (name,)).fetchone()
        if row:
            return row["id"]
        cur = conn.execute("INSERT INTO clients(name) VALUES(?)", (name,))
        return cur.lastrowid


def list_clients() -> list[dict]:
    with get_connection() as conn:
        return _rows_to_list(conn.execute("SELECT * FROM clients ORDER BY name").fetchall())


# ─────────────────────────────────────────────
# Portfolios
# ─────────────────────────────────────────────

def get_or_create_portfolio(name: str, client_id: int) -> int:
    name = name.strip()
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id FROM portfolios WHERE name=? AND client_id=?", (name, client_id)
        ).fetchone()
        if row:
            return row["id"]
        cur = conn.execute(
            "INSERT INTO portfolios(name, client_id) VALUES(?,?)", (name, client_id)
        )
        return cur.lastrowid


def list_portfolios() -> list[dict]:
    with get_connection() as conn:
        return _rows_to_list(conn.execute("""
            SELECT p.*, c.name AS client_name
            FROM portfolios p
            LEFT JOIN clients c ON c.id = p.client_id
            ORDER BY c.name, p.name
        """).fetchall())


def get_portfolio_summary() -> list[dict]:
    with get_connection() as conn:
        return _rows_to_list(conn.execute("""
            SELECT
                p.id, p.name AS portfolio, c.name AS client,
                COUNT(m.id) AS total,
                SUM(CASE WHEN m.status COLLATE NOCASE IN ('ready to invoice', 'client invoiced', 'completed') THEN 1 ELSE 0 END) AS completed,
                SUM(CASE WHEN m.status COLLATE NOCASE IN ('under mc review', 'logistics coordination', 'planning') THEN 1 ELSE 0 END) AS planning,
                SUM(CASE WHEN m.status COLLATE NOCASE IN ('cancelled', 'dead') THEN 1 ELSE 0 END) AS cancelled,
                SUM(CASE WHEN m.status COLLATE NOCASE IN ('data uploading', 'awaiting flight', 'pilot checked in', 'in progress') THEN 1 ELSE 0 END) AS in_progress,
                p.notes
            FROM portfolios p
            LEFT JOIN clients c ON c.id = p.client_id
            LEFT JOIN missions m ON m.portfolio_id = p.id
            GROUP BY p.id
            ORDER BY c.name, p.name
        """).fetchall())


def update_portfolio_notes(portfolio_id: int, notes: str) -> None:
    with get_connection() as conn:
        conn.execute("UPDATE portfolios SET notes=? WHERE id=?", (notes, portfolio_id))


# ─────────────────────────────────────────────
# Missions
# ─────────────────────────────────────────────

def upsert_mission(data: dict) -> tuple[str, list[dict]]:
    """Insert or update a mission. Returns ('added'|'updated'|'unchanged', list of changes)."""
    mission_id = data["mission_id"]
    changes = []
    with get_connection() as conn:
        existing = conn.execute(
            "SELECT * FROM missions WHERE mission_id=?", (mission_id,)
        ).fetchone()

        tracked_fields = ["status", "client_id", "portfolio_id", "mission_date", "location", "pilot"]

        if existing is None:
            conn.execute("""
                INSERT INTO missions
                    (mission_id, client_id, portfolio_id, status, mission_date, location, pilot, notes, raw_data, updated_at)
                VALUES (:mission_id, :client_id, :portfolio_id, :status, :mission_date, :location, :pilot, :notes, :raw_data, :updated_at)
            """, {**data, "updated_at": now()})
            conn.execute("""
                INSERT INTO mission_status_history(mission_id, old_status, new_status)
                VALUES(?, NULL, ?)
            """, (mission_id, data.get("status", "Unknown")))
            changes.append({"field": "mission_id", "old": None, "new": mission_id, "type": "added"})
            return "added", changes

        # Check what changed
        changed_fields = []
        for field in tracked_fields:
            old_val = existing[field]
            new_val = data.get(field)
            if str(old_val or "") != str(new_val or ""):
                changed_fields.append((field, old_val, new_val))
                changes.append({"field": field, "old": old_val, "new": new_val, "type": "updated"})

        if not changed_fields:
            return "unchanged", []

        conn.execute("""
            UPDATE missions SET
                client_id=:client_id, portfolio_id=:portfolio_id, status=:status,
                mission_date=:mission_date, location=:location, pilot=:pilot,
                notes=:notes, raw_data=:raw_data, updated_at=:updated_at
            WHERE mission_id=:mission_id
        """, {**data, "updated_at": now()})

        # Record status change separately
        for field, old_val, new_val in changed_fields:
            if field == "status":
                conn.execute("""
                    INSERT INTO mission_status_history(mission_id, old_status, new_status)
                    VALUES(?,?,?)
                """, (mission_id, old_val, new_val))

        return "updated", changes


def list_missions(filters: dict | None = None) -> list[dict]:
    filters = filters or {}
    clauses, params = [], []

    if filters.get("client"):
        clauses.append("c.name = ?")
        params.append(filters["client"])
    if filters.get("portfolio"):
        clauses.append("p.name = ?")
        params.append(filters["portfolio"])
    if filters.get("status"):
        clauses.append("m.status = ?")
        params.append(filters["status"])
    if filters.get("search"):
        clauses.append("(m.mission_id LIKE ? OR m.location LIKE ? OR m.pilot LIKE ?)")
        s = f"%{filters['search']}%"
        params += [s, s, s]
    if filters.get("date_from"):
        clauses.append("m.mission_date >= ?")
        params.append(filters["date_from"])
    if filters.get("date_to"):
        clauses.append("m.mission_date <= ?")
        params.append(filters["date_to"])

    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    with get_connection() as conn:
        return _rows_to_list(conn.execute(f"""
            SELECT m.*, c.name AS client_name, p.name AS portfolio_name
            FROM missions m
            LEFT JOIN clients c ON c.id = m.client_id
            LEFT JOIN portfolios p ON p.id = m.portfolio_id
            {where}
            ORDER BY m.updated_at DESC
        """, params).fetchall())


def get_mission(mission_id: str) -> dict:
    with get_connection() as conn:
        row = conn.execute("""
            SELECT m.*, c.name AS client_name, p.name AS portfolio_name
            FROM missions m
            LEFT JOIN clients c ON c.id = m.client_id
            LEFT JOIN portfolios p ON p.id = m.portfolio_id
            WHERE m.mission_id=?
        """, (mission_id,)).fetchone()
        return _row_to_dict(row)


def get_mission_status_history(mission_id: str) -> list[dict]:
    with get_connection() as conn:
        return _rows_to_list(conn.execute(
            "SELECT * FROM mission_status_history WHERE mission_id=? ORDER BY changed_at",
            (mission_id,),
        ).fetchall())


# ─────────────────────────────────────────────
# Dashboard metrics
# ─────────────────────────────────────────────

def get_dashboard_metrics(filters: dict | None = None) -> dict:
    filters = filters or {}
    clauses, params = [], []
    if filters.get("client"):
        clauses.append("c.name = ?")
        params.append(filters["client"])
    if filters.get("portfolio"):
        clauses.append("p.name = ?")
        params.append(filters["portfolio"])
    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""

    with get_connection() as conn:
        row = conn.execute(f"""
            SELECT
                COUNT(*)                                                          AS total,
                SUM(CASE WHEN m.status COLLATE NOCASE IN ('ready to invoice', 'client invoiced', 'completed') THEN 1 ELSE 0 END) AS completed,
                SUM(CASE WHEN m.status COLLATE NOCASE IN ('under mc review', 'logistics coordination', 'planning') THEN 1 ELSE 0 END) AS planning,
                SUM(CASE WHEN m.status COLLATE NOCASE IN ('cancelled', 'dead') THEN 1 ELSE 0 END) AS cancelled,
                SUM(CASE WHEN m.status COLLATE NOCASE IN ('data uploading', 'awaiting flight', 'pilot checked in', 'in progress') THEN 1 ELSE 0 END) AS in_progress
            FROM missions m
            LEFT JOIN clients c ON c.id = m.client_id
            LEFT JOIN portfolios p ON p.id = m.portfolio_id
            {where}
        """, params).fetchone()

        open_tickets = conn.execute(
            "SELECT COUNT(*) AS cnt FROM tickets WHERE status NOT IN ('Resolved','Closed')"
        ).fetchone()["cnt"]

        recent = _rows_to_list(conn.execute(f"""
            SELECT m.mission_id, m.status, m.updated_at, c.name AS client_name, p.name AS portfolio_name
            FROM missions m
            LEFT JOIN clients c ON c.id = m.client_id
            LEFT JOIN portfolios p ON p.id = m.portfolio_id
            {where}
            ORDER BY m.updated_at DESC LIMIT 10
        """, params).fetchall())

        by_status = _rows_to_list(conn.execute(f"""
            SELECT m.status, COUNT(*) AS cnt
            FROM missions m
            LEFT JOIN clients c ON c.id = m.client_id
            LEFT JOIN portfolios p ON p.id = m.portfolio_id
            {where}
            GROUP BY m.status ORDER BY cnt DESC
        """, params).fetchall())

        by_portfolio = _rows_to_list(conn.execute(f"""
            SELECT p.name AS portfolio, COUNT(*) AS total,
                   SUM(CASE WHEN m.status COLLATE NOCASE IN ('ready to invoice', 'client invoiced', 'completed') THEN 1 ELSE 0 END) AS done
            FROM missions m
            LEFT JOIN clients c ON c.id = m.client_id
            LEFT JOIN portfolios p ON p.id = m.portfolio_id
            {where}
            GROUP BY p.name ORDER BY p.name
        """, params).fetchall())

    metrics = dict(row)
    metrics["open_tickets"] = open_tickets
    metrics["recent_missions"] = recent
    metrics["by_status"] = by_status
    metrics["by_portfolio"] = by_portfolio
    return metrics


# ─────────────────────────────────────────────
# CSV Imports
# ─────────────────────────────────────────────

def create_import_record(filename: str) -> int:
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO csv_imports(filename) VALUES(?)", (filename,)
        )
        return cur.lastrowid


def update_import_record(import_id: int, added: int, updated: int, unchanged: int, total: int) -> None:
    with get_connection() as conn:
        conn.execute("""
            UPDATE csv_imports SET rows_total=?,rows_added=?,rows_updated=?,rows_unchanged=?
            WHERE id=?
        """, (total, added, updated, unchanged, import_id))


def save_import_changes(import_id: int, mission_id: str, change_type: str, field_changes: list[dict]) -> None:
    with get_connection() as conn:
        if not field_changes:
            conn.execute("""
                INSERT INTO import_changes(import_id, mission_id, change_type)
                VALUES(?,?,?)
            """, (import_id, mission_id, change_type))
        for fc in field_changes:
            conn.execute("""
                INSERT INTO import_changes(import_id, mission_id, change_type, field_name, old_value, new_value)
                VALUES(?,?,?,?,?,?)
            """, (import_id, mission_id, change_type, fc["field"], fc.get("old"), fc.get("new")))


def list_imports() -> list[dict]:
    with get_connection() as conn:
        return _rows_to_list(conn.execute(
            "SELECT * FROM csv_imports ORDER BY imported_at DESC"
        ).fetchall())


def get_import_changes(import_id: int) -> list[dict]:
    with get_connection() as conn:
        return _rows_to_list(conn.execute(
            "SELECT * FROM import_changes WHERE import_id=? ORDER BY mission_id",
            (import_id,),
        ).fetchall())


def get_latest_two_import_ids() -> tuple[int | None, int | None]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id FROM csv_imports ORDER BY imported_at DESC LIMIT 2"
        ).fetchall()
        ids = [r["id"] for r in rows]
        current = ids[0] if ids else None
        previous = ids[1] if len(ids) > 1 else None
        return current, previous


# ─────────────────────────────────────────────
# Weekly update diff
# ─────────────────────────────────────────────

def get_weekly_diff(current_import_id: int, previous_import_id: int | None) -> dict:
    """Compare missions between two imports."""
    with get_connection() as conn:
        # missions added in current import
        added = _rows_to_list(conn.execute("""
            SELECT DISTINCT ic.mission_id
            FROM import_changes ic
            WHERE ic.import_id=? AND ic.change_type='added'
        """, (current_import_id,)).fetchall())

        # status changes in current import
        status_changes = _rows_to_list(conn.execute("""
            SELECT ic.mission_id, ic.old_value, ic.new_value,
                   m.status, c.name AS client_name, p.name AS portfolio_name
            FROM import_changes ic
            JOIN missions m ON m.mission_id = ic.mission_id
            LEFT JOIN clients c ON c.id = m.client_id
            LEFT JOIN portfolios p ON p.id = m.portfolio_id
            WHERE ic.import_id=? AND ic.change_type='updated' AND ic.field_name='status'
        """, (current_import_id,)).fetchall())

        now_completed = [r for r in status_changes if r["new_value"].lower() in ("ready to invoice", "client invoiced", "completed")]
        now_cancelled = [r for r in status_changes if r["new_value"].lower() in ("cancelled", "dead")]
        still_planning = _rows_to_list(conn.execute("""
            SELECT m.mission_id, c.name AS client_name, p.name AS portfolio_name
            FROM missions m
            LEFT JOIN clients c ON c.id = m.client_id
            LEFT JOIN portfolios p ON p.id = m.portfolio_id
            WHERE m.status COLLATE NOCASE IN ('under mc review', 'logistics coordination', 'planning')
            ORDER BY m.mission_id
        """).fetchall())

        open_tickets = _rows_to_list(conn.execute("""
            SELECT * FROM tickets WHERE status NOT IN ('Resolved','Closed')
            ORDER BY created_at DESC
        """).fetchall())

        resolved_tickets = _rows_to_list(conn.execute("""
            SELECT * FROM tickets WHERE status IN ('Resolved','Closed')
            AND resolved_at >= (SELECT MIN(imported_at) FROM csv_imports WHERE id=?)
            ORDER BY resolved_at DESC
        """, (current_import_id,)).fetchall())

    return {
        "added": added,
        "status_changes": status_changes,
        "now_completed": now_completed,
        "now_cancelled": now_cancelled,
        "still_planning": still_planning,
        "open_tickets": open_tickets,
        "resolved_tickets": resolved_tickets,
    }


# ─────────────────────────────────────────────
# Tickets
# ─────────────────────────────────────────────

def _next_ticket_id() -> str:
    counter = int(get_setting("ticket_counter", "0")) + 1
    set_setting("ticket_counter", str(counter))
    return f"TKT-{counter:04d}"


def create_ticket(data: dict) -> str:
    ticket_id = _next_ticket_id()
    mission = get_mission(data["mission_id"])
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO tickets
                (ticket_id, mission_id, client, portfolio, mission_status,
                 description, category, priority, status, assigned_owner)
            VALUES (?,?,?,?,?,?,?,?,?,?)
        """, (
            ticket_id,
            data["mission_id"],
            mission.get("client_name") or data.get("client", ""),
            mission.get("portfolio_name") or data.get("portfolio", ""),
            mission.get("status") or data.get("mission_status", ""),
            data["description"],
            data.get("category", ""),
            data.get("priority", "Medium"),
            data.get("status", "Open"),
            data.get("assigned_owner", ""),
        ))
    return ticket_id


def list_tickets(filters: dict | None = None) -> list[dict]:
    filters = filters or {}
    clauses, params = [], []
    if filters.get("status"):
        clauses.append("status = ?")
        params.append(filters["status"])
    elif filters.get("hide_closed"):
        clauses.append("status != 'Closed'")
    if filters.get("priority"):
        clauses.append("priority = ?")
        params.append(filters["priority"])
    if filters.get("mission_id"):
        clauses.append("mission_id LIKE ?")
        params.append(f"%{filters['mission_id']}%")
    if filters.get("search"):
        s = f"%{filters['search']}%"
        clauses.append("(ticket_id LIKE ? OR mission_id LIKE ? OR description LIKE ?)")
        params += [s, s, s]
    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    with get_connection() as conn:
        return _rows_to_list(conn.execute(
            f"SELECT * FROM tickets {where} ORDER BY created_at DESC", params
        ).fetchall())


def get_ticket(ticket_id: str) -> dict:
    with get_connection() as conn:
        return _row_to_dict(conn.execute(
            "SELECT * FROM tickets WHERE ticket_id=?", (ticket_id,)
        ).fetchone())


def get_open_ticket_for_mission(mission_id: str) -> str | None:
    """Return the ticket_id of the first non-Closed ticket for the mission, or None."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT ticket_id FROM tickets WHERE mission_id=? AND status != 'Closed' ORDER BY created_at LIMIT 1",
            (mission_id,),
        ).fetchone()
        return row["ticket_id"] if row else None


def update_ticket(ticket_id: str, data: dict) -> None:
    resolved_at = None
    if data.get("status") in ("Resolved", "Closed"):
        existing = get_ticket(ticket_id)
        resolved_at = existing.get("resolved_at") or now()
    with get_connection() as conn:
        conn.execute("""
            UPDATE tickets SET
                status=?, priority=?, category=?, description=?,
                assigned_owner=?, updated_at=?, resolved_at=?
            WHERE ticket_id=?
        """, (
            data.get("status"),
            data.get("priority"),
            data.get("category"),
            data.get("description"),
            data.get("assigned_owner"),
            now(),
            resolved_at,
            ticket_id,
        ))


def add_ticket_note(ticket_id: str, note: str, author: str = "") -> None:
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO ticket_notes(ticket_id, note, author) VALUES(?,?,?)",
            (ticket_id, note, author),
        )


def get_ticket_notes(ticket_id: str) -> list[dict]:
    with get_connection() as conn:
        return _rows_to_list(conn.execute(
            "SELECT * FROM ticket_notes WHERE ticket_id=? ORDER BY created_at",
            (ticket_id,),
        ).fetchall())


# ─────────────────────────────────────────────
# Weekly snapshots
# ─────────────────────────────────────────────

def save_weekly_snapshot(import_id: int) -> None:
    metrics = get_dashboard_metrics()
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO weekly_snapshots
                (snapshot_date, import_id, total_missions, completed, invoiced,
                 planning, cancelled, in_progress, summary_json)
            VALUES (date('now'), ?, ?, ?, 0, ?, ?, ?, ?)
        """, (
            import_id,
            metrics.get("total", 0),
            metrics.get("completed", 0),
            metrics.get("planning", 0),
            metrics.get("cancelled", 0),
            metrics.get("in_progress", 0),
            json.dumps(metrics.get("by_portfolio", [])),
        ))
