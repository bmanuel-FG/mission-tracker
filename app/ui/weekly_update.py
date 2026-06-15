"""Weekly Update tab — diff between latest two imports."""
from __future__ import annotations

from pathlib import Path

# pyrefly: ignore [missing-import]
from PySide6.QtWidgets import (
    QComboBox, QFileDialog, QHBoxLayout, QLabel,
    QPushButton, QTabWidget, QVBoxLayout, QWidget,
)

from app.database import models
from app.services.csv_export import export_weekly_update
from .widgets import SectionHeader, fill_table, make_table


class WeeklyUpdatePage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._diff: dict = {}
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        layout.addWidget(SectionHeader("Weekly Update", "Changes since the previous import"))

        # ── Import selector ───────────────────────────────────────────────
        top = QHBoxLayout()
        top.setSpacing(10)
        top.addWidget(QLabel("Compare import:"))
        self._import_cb = QComboBox()
        self._import_cb.setMinimumWidth(320)
        top.addWidget(self._import_cb)
        reload_btn = QPushButton("Refresh")
        reload_btn.setObjectName("secondary")
        reload_btn.clicked.connect(self.refresh)
        top.addWidget(reload_btn)
        export_btn = QPushButton("Export CSV")
        export_btn.clicked.connect(self._export)
        top.addWidget(export_btn)
        top.addStretch()
        layout.addLayout(top)

        self._summary_lbl = QLabel("")
        self._summary_lbl.setStyleSheet("color: #9090B0; font-size: 12px;")
        layout.addWidget(self._summary_lbl)

        # ── Tabs ──────────────────────────────────────────────────────────
        tabs = QTabWidget()
        layout.addWidget(tabs)

        # New missions
        new_w = QWidget()
        new_l = QVBoxLayout(new_w)
        self._new_table = make_table(["Mission ID"])
        new_l.addWidget(self._new_table)
        tabs.addTab(new_w, "New Missions")

        # Completed
        comp_w = QWidget()
        comp_l = QVBoxLayout(comp_w)
        self._comp_table = make_table(["Mission ID", "Previous Status", "New Status"])
        comp_l.addWidget(self._comp_table)
        tabs.addTab(comp_w, "Completed")



        # Cancelled
        can_w = QWidget()
        can_l = QVBoxLayout(can_w)
        self._can_table = make_table(["Mission ID", "Previous Status", "New Status"])
        can_l.addWidget(self._can_table)
        tabs.addTab(can_w, "Cancelled")

        # Still planning
        plan_w = QWidget()
        plan_l = QVBoxLayout(plan_w)
        self._plan_table = make_table(["Mission ID", "Portfolio"])
        plan_l.addWidget(self._plan_table)
        tabs.addTab(plan_w, "Still Planning")

        # All status changes
        all_w = QWidget()
        all_l = QVBoxLayout(all_w)
        self._all_table = make_table(["Mission ID", "Old Status", "New Status", "Client", "Portfolio"])
        all_l.addWidget(self._all_table)
        tabs.addTab(all_w, "All Status Changes")

        # Open tickets
        otick_w = QWidget()
        otick_l = QVBoxLayout(otick_w)
        self._open_tick_table = make_table(["Ticket ID", "Mission ID", "Priority", "Status", "Description"])
        otick_l.addWidget(self._open_tick_table)
        tabs.addTab(otick_w, "Open Tickets")

        # Resolved tickets
        rtick_w = QWidget()
        rtick_l = QVBoxLayout(rtick_w)
        self._resolved_tick_table = make_table(["Ticket ID", "Mission ID", "Status", "Resolved At"])
        rtick_l.addWidget(self._resolved_tick_table)
        tabs.addTab(rtick_w, "Resolved Tickets")

    def refresh(self) -> None:
        imports = models.list_imports()
        self._import_cb.blockSignals(True)
        self._import_cb.clear()
        for imp in imports:
            self._import_cb.addItem(
                f"{imp['imported_at'][:16]}  —  {imp['filename']}  ({imp['rows_added']} added, {imp['rows_updated']} updated)",
                userData=imp["id"],
            )
        self._import_cb.blockSignals(False)

        current_id, previous_id = models.get_latest_two_import_ids()
        if current_id is None:
            self._summary_lbl.setText("No imports yet. Go to Import / Export to load data.")
            return

        self._diff = models.get_weekly_diff(current_id, previous_id)
        self._populate()

    def _populate(self) -> None:
        d = self._diff

        fill_table(self._new_table, d.get("added", []), ["mission_id"])
        self._new_table.setHorizontalHeaderLabels(["Mission ID"])

        def _fill_transitions(table, rows):
            fill_table(table, rows, ["mission_id", "old_value", "new_value"])
            table.setHorizontalHeaderLabels(["Mission ID", "Previous Status", "New Status"])

        _fill_transitions(self._comp_table, d.get("now_completed", []))
        _fill_transitions(self._can_table, d.get("now_cancelled", []))

        fill_table(self._plan_table, d.get("still_planning", []), ["mission_id", "portfolio_name"])
        self._plan_table.setHorizontalHeaderLabels(["Mission ID", "Portfolio"])

        fill_table(self._all_table, d.get("status_changes", []),
                   ["mission_id", "old_value", "new_value", "client_name", "portfolio_name"])
        self._all_table.setHorizontalHeaderLabels(
            ["Mission ID", "Old Status", "New Status", "Client", "Portfolio"])

        open_rows = []
        for t in d.get("open_tickets", []):
            open_rows.append({
                "ticket_id":   t.get("ticket_id"),
                "mission_id":  t.get("mission_id"),
                "priority":    t.get("priority"),
                "status":      t.get("status"),
                "description": t.get("description", "")[:80],
            })
        fill_table(self._open_tick_table, open_rows,
                   ["ticket_id", "mission_id", "priority", "status", "description"])

        res_rows = []
        for t in d.get("resolved_tickets", []):
            res_rows.append({
                "ticket_id":   t.get("ticket_id"),
                "mission_id":  t.get("mission_id"),
                "status":      t.get("status"),
                "resolved_at": (t.get("resolved_at") or "")[:16],
            })
        fill_table(self._resolved_tick_table, res_rows,
                   ["ticket_id", "mission_id", "status", "resolved_at"])

        counts = (
            f"New: {len(d.get('added', []))}  |  "
            f"Completed: {len(d.get('now_completed', []))}  |  "
            f"Cancelled: {len(d.get('now_cancelled', []))}  |  "
            f"Still Planning: {len(d.get('still_planning', []))}  |  "
            f"Open Tickets: {len(d.get('open_tickets', []))}"
        )
        self._summary_lbl.setText(counts)

    def _export(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Export Weekly Update", "weekly_update.csv", "CSV Files (*.csv)")
        if path:
            export_weekly_update(path)
