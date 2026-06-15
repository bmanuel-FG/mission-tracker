"""CSV import logic: read → clean → diff → upsert → summarize."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from app.database import models


# Mapping of common CSV column name variants → internal field names
COLUMN_MAP: dict[str, str] = {
    # job id variants
    "job id": "mission_id",
    "jobid": "mission_id",
    "job_id": "mission_id",
    "id": "mission_id",
    # client
    "customer": "client",
    "customer name": "client",
    "customername": "client",
    # portfolio
    "portfolio": "portfolio",
    "portfolio name": "portfolio",
    "portfolioname": "portfolio",
    # status
    "status": "status",
    "mission status": "status",
    # date
    "capture date": "mission_date",
    # location
    "location": "location",
    "address": "location",
    # pilot
    "pilot": "pilot",
    "pilot name": "pilot",
    "assigned pilot": "pilot",
}


def _normalise_columns(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = [c.strip().lower() for c in df.columns]
    rename = {}
    for col in df.columns:
        if col in COLUMN_MAP:
            rename[col] = COLUMN_MAP[col]
    df = df.rename(columns=rename)
    return df


def _clean_mission_id(val: str) -> str:
    return str(val).strip().replace(",", "").replace(" ", "-").upper()


def import_csv(file_path: str | Path) -> dict:
    """
    Import a CSV file. Returns a summary dict.
    """
    file_path = Path(file_path)

    # --- read ---------------------------------------------------------------
    try:
        df = pd.read_csv(file_path, dtype=str, keep_default_na=False)
    except Exception as exc:
        return {"success": False, "error": str(exc)}

    df = _normalise_columns(df)

    if "mission_id" not in df.columns:
        return {
            "success": False,
            "error": (
                "Could not find a Mission ID column. "
                "Expected one of: 'Mission ID', 'MissionID', 'ID'. "
                f"Columns found: {list(df.columns)}"
            ),
        }

    # --- create import record ------------------------------------------------
    import_id = models.create_import_record(file_path.name)

    counts = {"added": 0, "updated": 0, "unchanged": 0}

    for _, row in df.iterrows():
        mission_id = _clean_mission_id(row["mission_id"])
        if not mission_id or mission_id == "NAN":
            continue

        client_name = str(row.get("client", "Unknown")).strip() or "Unknown"
        portfolio_name = str(row.get("portfolio", "Unknown")).strip() or "Unknown"

        client_id = models.get_or_create_client(client_name)
        portfolio_id = models.get_or_create_portfolio(portfolio_name, client_id)

        raw_data = json.dumps(row.to_dict())

        data = {
            "mission_id": mission_id,
            "client_id": client_id,
            "portfolio_id": portfolio_id,
            "status": str(row.get("status", "Unknown")).strip().title(),
            "mission_date": str(row.get("mission_date", "")).strip() or None,
            "location": str(row.get("location", "")).strip() or None,
            "pilot": str(row.get("pilot", "")).strip() or None,
            "notes": None,
            "raw_data": raw_data,
        }

        change_type, field_changes = models.upsert_mission(data)
        counts[change_type] += 1
        models.save_import_changes(import_id, mission_id, change_type, field_changes)

    total = counts["added"] + counts["updated"] + counts["unchanged"]
    models.update_import_record(import_id, counts["added"], counts["updated"], counts["unchanged"], total)
    models.save_weekly_snapshot(import_id)

    # --- build summary -------------------------------------------------------
    all_changes = models.get_import_changes(import_id)
    status_transitions: dict[str, list[str]] = {}
    for c in all_changes:
        if c["field_name"] == "status" and c["new_value"]:
            status_transitions.setdefault(c["new_value"], []).append(c["mission_id"])

    summary = {
        "success": True,
        "import_id": import_id,
        "filename": file_path.name,
        "total": total,
        "added": counts["added"],
        "updated": counts["updated"],
        "unchanged": counts["unchanged"],
        "status_transitions": status_transitions,
    }
    return summary
