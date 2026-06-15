"""CSV export functions for all views."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from app.database import models


def _save(df: pd.DataFrame, path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    return path


def export_all_missions(path: str | Path) -> Path:
    rows = models.list_missions()
    df = pd.DataFrame(rows)
    _clean_export_cols(df)
    return _save(df, path)


def export_filtered_missions(path: str | Path, filters: dict) -> Path:
    rows = models.list_missions(filters)
    df = pd.DataFrame(rows)
    _clean_export_cols(df)
    return _save(df, path)


def export_tickets(path: str | Path, filters: dict | None = None) -> Path:
    rows = models.list_tickets(filters)
    df = pd.DataFrame(rows)
    return _save(df, path)


def export_portfolio_summary(path: str | Path) -> Path:
    rows = models.get_portfolio_summary()
    df = pd.DataFrame(rows)
    return _save(df, path)


def export_weekly_update(path: str | Path) -> Path:
    current_id, previous_id = models.get_latest_two_import_ids()
    if current_id is None:
        df = pd.DataFrame([{"note": "No imports found"}])
        return _save(df, path)

    diff = models.get_weekly_diff(current_id, previous_id)

    rows = []
    for m in diff["added"]:
        rows.append({"section": "New Missions", "mission_id": m["mission_id"], "detail": ""})
    for m in diff["now_completed"]:
        rows.append({"section": "Completed", "mission_id": m["mission_id"], "detail": f"{m['old_value']} → {m['new_value']}"})
    for m in diff["now_invoiced"]:
        rows.append({"section": "Invoiced", "mission_id": m["mission_id"], "detail": f"{m['old_value']} → {m['new_value']}"})
    for m in diff["now_cancelled"]:
        rows.append({"section": "Cancelled", "mission_id": m["mission_id"], "detail": f"{m['old_value']} → {m['new_value']}"})
    for m in diff["still_planning"]:
        rows.append({"section": "Still Planning", "mission_id": m["mission_id"], "detail": m.get("portfolio_name", "")})
    for t in diff["open_tickets"]:
        rows.append({"section": "Open Tickets", "mission_id": t["mission_id"], "detail": t["ticket_id"]})
    for t in diff["resolved_tickets"]:
        rows.append({"section": "Resolved Tickets", "mission_id": t["mission_id"], "detail": t["ticket_id"]})

    df = pd.DataFrame(rows) if rows else pd.DataFrame([{"section": "No changes", "mission_id": "", "detail": ""}])
    return _save(df, path)


def _clean_export_cols(df: pd.DataFrame) -> None:
    """Drop internal ID columns from user-facing exports."""
    for col in ["id", "client_id", "portfolio_id", "raw_data"]:
        if col in df.columns:
            df.drop(columns=[col], inplace=True)
