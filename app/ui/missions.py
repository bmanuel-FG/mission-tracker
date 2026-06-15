"""Missions tab — searchable, filterable, sortable mission table."""
from __future__ import annotations

# pyrefly: ignore [missing-import]
from PySide6.QtCore import Qt, QTimer
# pyrefly: ignore [missing-import]
from PySide6.QtWidgets import (
    QComboBox, QDialog, QDialogButtonBox, QFormLayout,
    QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTextEdit, QVBoxLayout, QWidget,
)

from app.database import models
from .widgets import SectionHeader, fill_table, make_table


COLS = ["mission_id", "status", "client_name", "portfolio_name", "mission_date", "location", "pilot", "ticket_id", "updated_at"]
HEADERS = ["Mission ID", "Status", "Client", "Portfolio", "Date", "Location", "Pilot", "Ticket", "Updated"]
STATUSES = ["All", "Planning", "In Progress", "Completed", "Invoiced", "Cancelled", "Unknown"]


class MissionsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        layout.addWidget(SectionHeader("Missions", "Search, filter, and view all missions"))

        # ── Filter bar ────────────────────────────────────────────────────
        bar = QHBoxLayout()
        bar.setSpacing(10)

        self._search = QLineEdit()
        self._search.setPlaceholderText("Search mission ID, location, pilot…")
        self._search.setFixedWidth(280)
        self._search.textChanged.connect(self._schedule_reload)

        self._status_cb = QComboBox()
        self._status_cb.addItems(STATUSES)
        self._status_cb.currentIndexChanged.connect(self._schedule_reload)

        self._client_cb = QComboBox()
        self._client_cb.addItem("All Clients")
        self._client_cb.currentIndexChanged.connect(self._schedule_reload)

        self._portfolio_cb = QComboBox()
        self._portfolio_cb.addItem("All Portfolios")
        self._portfolio_cb.currentIndexChanged.connect(self._schedule_reload)

        clear_btn = QPushButton("Clear")
        clear_btn.setObjectName("secondary")
        clear_btn.clicked.connect(self._clear_filters)

        self._count_lbl = QLabel("")
        self._count_lbl.setStyleSheet("color: #9090B0; font-size: 12px;")

        bar.addWidget(QLabel("Search:"))
        bar.addWidget(self._search)
        bar.addWidget(QLabel("Status:"))
        bar.addWidget(self._status_cb)
        bar.addWidget(QLabel("Client:"))
        bar.addWidget(self._client_cb)
        bar.addWidget(QLabel("Portfolio:"))
        bar.addWidget(self._portfolio_cb)
        bar.addWidget(clear_btn)
        bar.addStretch()
        bar.addWidget(self._count_lbl)
        layout.addLayout(bar)

        # ── Table ─────────────────────────────────────────────────────────
        self._table = make_table(HEADERS)
        self._table.doubleClicked.connect(self._on_row_double_click)
        layout.addWidget(self._table)

        self._timer = QTimer()
        self._timer.setSingleShot(True)
        self._timer.setInterval(300)
        self._timer.timeout.connect(self._reload)

    def refresh(self) -> None:
        self._load_combos()
        self._reload()

    def _load_combos(self) -> None:
        clients = ["All Clients"] + [c["name"] for c in models.list_clients()]
        portfolios = ["All Portfolios"] + [p["name"] for p in models.list_portfolios()]

        for cb, items in [(self._client_cb, clients), (self._portfolio_cb, portfolios)]:
            cb.blockSignals(True)
            current = cb.currentText()
            cb.clear()
            cb.addItems(items)
            idx = cb.findText(current)
            cb.setCurrentIndex(max(0, idx))
            cb.blockSignals(False)

    def _build_filters(self) -> dict:
        f: dict = {}
        s = self._search.text().strip()
        if s:
            f["search"] = s
        st = self._status_cb.currentText()
        if st != "All":
            f["status"] = st
        c = self._client_cb.currentText()
        if c != "All Clients":
            f["client"] = c
        p = self._portfolio_cb.currentText()
        if p != "All Portfolios":
            f["portfolio"] = p
        return f

    def _schedule_reload(self) -> None:
        self._timer.start()

    def _reload(self) -> None:
        rows = models.list_missions(self._build_filters())
        display = []
        for r in rows:
            mid = r.get("mission_id")
            open_ticket = models.get_open_ticket_for_mission(mid) if mid else None
            display.append({
                "mission_id":     mid,
                "status":         r.get("status"),
                "client_name":    r.get("client_name") or "—",
                "portfolio_name": r.get("portfolio_name") or "—",
                "mission_date":   r.get("mission_date") or "—",
                "location":       r.get("location") or "—",
                "pilot":          r.get("pilot") or "—",
                "ticket_id":      open_ticket or "—",
                "updated_at":     (r.get("updated_at") or "")[:16],
            })
        fill_table(self._table, display, COLS)
        self._table.setHorizontalHeaderLabels(HEADERS)
        self._count_lbl.setText(f"{len(rows)} mission(s)")

    def _clear_filters(self) -> None:
        self._search.clear()
        self._status_cb.setCurrentIndex(0)
        self._client_cb.setCurrentIndex(0)
        self._portfolio_cb.setCurrentIndex(0)

    def _on_row_double_click(self, index) -> None:
        row = self._table.currentRow()
        mission_id_item = self._table.item(row, 0)
        if not mission_id_item:
            return
        mission_id = mission_id_item.text()
        dlg = MissionDetailDialog(mission_id, self)
        dlg.exec()


class MissionDetailDialog(QDialog):
    def __init__(self, mission_id: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Mission — {mission_id}")
        self.setMinimumSize(560, 460)
        self.setStyleSheet(parent.styleSheet() if parent else "")

        data = models.get_mission(mission_id)
        history = models.get_mission_status_history(mission_id)
        tickets = models.list_tickets({"mission_id": mission_id})

        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.setSpacing(8)

        for label, key in [
            ("Mission ID",  "mission_id"),
            ("Status",      "status"),
            ("Client",      "client_name"),
            ("Portfolio",   "portfolio_name"),
            ("Date",        "mission_date"),
            ("Location",    "location"),
            ("Pilot",       "pilot"),
        ]:
            val = str(data.get(key) or "—")
            lbl = QLabel(val)
            lbl.setStyleSheet("color: #E0E0F0;")
            form.addRow(f"<b>{label}:</b>", lbl)

        layout.addLayout(form)

        # Status history
        layout.addWidget(QLabel("<b>Status History:</b>"))
        hist_txt = QTextEdit()
        hist_txt.setReadOnly(True)
        hist_txt.setMaximumHeight(100)
        hist_lines = [f"{h['changed_at'][:16]}  {h['old_status'] or 'New'} → {h['new_status']}" for h in history]
        hist_txt.setPlainText("\n".join(hist_lines) or "No history")
        layout.addWidget(hist_txt)

        # Linked tickets
        layout.addWidget(QLabel(f"<b>Linked Tickets ({len(tickets)}):</b>"))
        tick_txt = QTextEdit()
        tick_txt.setReadOnly(True)
        tick_txt.setMaximumHeight(80)
        tick_lines = [f"{t['ticket_id']}  [{t['priority']}]  {t['status']}  {t['description'][:60]}" for t in tickets]
        tick_txt.setPlainText("\n".join(tick_lines) or "None")
        layout.addWidget(tick_txt)

        btn = QDialogButtonBox(QDialogButtonBox.Close)
        btn.rejected.connect(self.reject)
        layout.addWidget(btn)
