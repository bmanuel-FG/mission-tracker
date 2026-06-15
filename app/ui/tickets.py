"""Tickets / Incidents tab."""
from __future__ import annotations

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QComboBox, QDialog, QDialogButtonBox, QFormLayout,
    QHBoxLayout, QLabel, QLineEdit, QMessageBox,
    QPushButton, QSplitter, QTextEdit, QVBoxLayout, QWidget,
)

from app.database import models
from .widgets import SectionHeader, fill_table, make_table


STATUSES = ["Open", "In Progress", "Waiting on Pilot", "Waiting on Client", "Resolved", "Closed"]
PRIORITIES = ["Low", "Medium", "High", "Critical"]
CATEGORIES = ["", "Data Issue", "Flight Issue", "Billing", "Client Communication",
              "Technical", "Scheduling", "Other"]

COLS    = ["ticket_id", "mission_id", "priority", "status", "category", "client", "portfolio", "created_at", "description"]
HEADERS = ["Ticket ID", "Mission ID", "Priority", "Status", "Category", "Client", "Portfolio", "Created", "Description"]


class TicketsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        layout.addWidget(SectionHeader("Tickets / Incidents", "Issue tracking linked to mission records"))

        # ── Action bar ────────────────────────────────────────────────────
        bar = QHBoxLayout()
        bar.setSpacing(10)

        new_btn = QPushButton("+ New Ticket")
        new_btn.clicked.connect(self._open_new_dialog)

        self._search = QLineEdit()
        self._search.setPlaceholderText("Search ticket ID, mission ID, description…")
        self._search.setFixedWidth(280)
        self._search.textChanged.connect(self._schedule_reload)

        self._status_cb = QComboBox()
        self._status_cb.addItem("All Statuses")
        self._status_cb.addItems(STATUSES)
        self._status_cb.currentIndexChanged.connect(self._schedule_reload)

        self._priority_cb = QComboBox()
        self._priority_cb.addItem("All Priorities")
        self._priority_cb.addItems(PRIORITIES)
        self._priority_cb.currentIndexChanged.connect(self._schedule_reload)

        self._count_lbl = QLabel("")
        self._count_lbl.setStyleSheet("color: #9090B0; font-size: 12px;")

        bar.addWidget(new_btn)
        bar.addWidget(QLabel("Search:"))
        bar.addWidget(self._search)
        bar.addWidget(QLabel("Status:"))
        bar.addWidget(self._status_cb)
        bar.addWidget(QLabel("Priority:"))
        bar.addWidget(self._priority_cb)
        bar.addStretch()
        bar.addWidget(self._count_lbl)
        layout.addLayout(bar)

        # ── Table ─────────────────────────────────────────────────────────
        self._table = make_table(HEADERS)
        self._table.doubleClicked.connect(self._open_edit_dialog)
        layout.addWidget(self._table)

        self._timer = QTimer()
        self._timer.setSingleShot(True)
        self._timer.setInterval(300)
        self._timer.timeout.connect(self._reload)

    def refresh(self) -> None:
        self._reload()

    def _build_filters(self) -> dict:
        f: dict = {}
        s = self._search.text().strip()
        if s:
            f["search"] = s
        st = self._status_cb.currentText()
        if st != "All Statuses":
            f["status"] = st
        pr = self._priority_cb.currentText()
        if pr != "All Priorities":
            f["priority"] = pr
        return f

    def _schedule_reload(self) -> None:
        self._timer.start()

    def _reload(self) -> None:
        rows = models.list_tickets(self._build_filters())
        display = []
        for r in rows:
            display.append({
                "ticket_id":   r.get("ticket_id"),
                "mission_id":  r.get("mission_id"),
                "priority":    r.get("priority"),
                "status":      r.get("status"),
                "category":    r.get("category") or "—",
                "client":      r.get("client") or "—",
                "portfolio":   r.get("portfolio") or "—",
                "created_at":  (r.get("created_at") or "")[:16],
                "description": (r.get("description") or "")[:80],
            })
        fill_table(self._table, display, COLS)
        self._table.setHorizontalHeaderLabels(HEADERS)
        self._count_lbl.setText(f"{len(rows)} ticket(s)")

    def _open_new_dialog(self) -> None:
        dlg = TicketDialog(parent=self)
        if dlg.exec() == QDialog.Accepted:
            self._reload()

    def _open_edit_dialog(self) -> None:
        row = self._table.currentRow()
        item = self._table.item(row, 0)
        if not item:
            return
        ticket_id = item.text()
        dlg = TicketDialog(ticket_id=ticket_id, parent=self)
        if dlg.exec() == QDialog.Accepted:
            self._reload()


class TicketDialog(QDialog):
    """Create or edit a ticket."""

    def __init__(self, ticket_id: str | None = None, parent=None):
        super().__init__(parent)
        self._ticket_id = ticket_id
        self._is_new = ticket_id is None
        self.setWindowTitle("New Ticket" if self._is_new else f"Edit Ticket — {ticket_id}")
        self.setMinimumSize(560, 620)
        self.setStyleSheet(parent.styleSheet() if parent else "")
        self._build_ui()
        if not self._is_new:
            self._load_data()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignRight)

        # Mission ID — auto-populates client/portfolio
        self._mission_id = QLineEdit()
        self._mission_id.setPlaceholderText("Enter mission ID to auto-populate")
        self._mission_id.editingFinished.connect(self._auto_populate)
        form.addRow("Mission ID *", self._mission_id)

        self._client = QLineEdit()
        self._client.setReadOnly(True)
        form.addRow("Client", self._client)

        self._portfolio = QLineEdit()
        self._portfolio.setReadOnly(True)
        form.addRow("Portfolio", self._portfolio)

        self._mission_status = QLineEdit()
        self._mission_status.setReadOnly(True)
        form.addRow("Mission Status", self._mission_status)

        self._description = QTextEdit()
        self._description.setFixedHeight(100)
        self._description.setPlaceholderText("Describe the issue…")
        form.addRow("Description *", self._description)

        self._category = QComboBox()
        self._category.addItems(CATEGORIES)
        form.addRow("Category", self._category)

        self._priority = QComboBox()
        self._priority.addItems(PRIORITIES)
        self._priority.setCurrentText("Medium")
        form.addRow("Priority", self._priority)

        self._status = QComboBox()
        self._status.addItems(STATUSES)
        form.addRow("Status", self._status)

        self._owner = QLineEdit()
        self._owner.setPlaceholderText("Assigned to…")
        form.addRow("Assigned To", self._owner)

        layout.addLayout(form)

        # Notes section (edit mode)
        if not self._is_new:
            layout.addWidget(QLabel("<b>Notes / History:</b>"))
            self._notes_list = QTextEdit()
            self._notes_list.setReadOnly(True)
            self._notes_list.setFixedHeight(100)
            layout.addWidget(self._notes_list)

            note_row = QHBoxLayout()
            self._note_input = QLineEdit()
            self._note_input.setPlaceholderText("Add a note…")
            add_note_btn = QPushButton("Add Note")
            add_note_btn.setObjectName("secondary")
            add_note_btn.clicked.connect(self._add_note)
            note_row.addWidget(self._note_input)
            note_row.addWidget(add_note_btn)
            layout.addLayout(note_row)

        btns = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        btns.accepted.connect(self._save)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _auto_populate(self) -> None:
        mid = self._mission_id.text().strip().upper()
        if not mid:
            return
        mission = models.get_mission(mid)
        if mission:
            self._client.setText(mission.get("client_name") or "")
            self._portfolio.setText(mission.get("portfolio_name") or "")
            self._mission_status.setText(mission.get("status") or "")
        else:
            self._client.setText("Mission not found")

    def _load_data(self) -> None:
        t = models.get_ticket(self._ticket_id)
        if not t:
            return
        self._mission_id.setText(t.get("mission_id", ""))
        self._client.setText(t.get("client", ""))
        self._portfolio.setText(t.get("portfolio", ""))
        self._mission_status.setText(t.get("mission_status", ""))
        self._description.setPlainText(t.get("description", ""))
        self._category.setCurrentText(t.get("category") or "")
        self._priority.setCurrentText(t.get("priority", "Medium"))
        self._status.setCurrentText(t.get("status", "Open"))
        self._owner.setText(t.get("assigned_owner") or "")

        notes = models.get_ticket_notes(self._ticket_id)
        self._notes_list.setPlainText(
            "\n".join(f"[{n['created_at'][:16]}]  {n['note']}" for n in notes) or "No notes yet."
        )

    def _add_note(self) -> None:
        note = self._note_input.text().strip()
        if note and self._ticket_id:
            models.add_ticket_note(self._ticket_id, note)
            self._note_input.clear()
            notes = models.get_ticket_notes(self._ticket_id)
            self._notes_list.setPlainText(
                "\n".join(f"[{n['created_at'][:16]}]  {n['note']}" for n in notes)
            )

    def _save(self) -> None:
        mid = self._mission_id.text().strip().upper()
        desc = self._description.toPlainText().strip()
        if not mid or not desc:
            QMessageBox.warning(self, "Required", "Mission ID and Description are required.")
            return

        data = {
            "mission_id":    mid,
            "description":   desc,
            "category":      self._category.currentText(),
            "priority":      self._priority.currentText(),
            "status":        self._status.currentText(),
            "assigned_owner":self._owner.text().strip(),
        }

        if self._is_new:
            models.create_ticket(data)
        else:
            models.update_ticket(self._ticket_id, data)

        self.accept()
