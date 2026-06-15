"""Portfolios tab — per-portfolio progress and mission list."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QProgressBar, QPushButton, QSplitter, QTextEdit,
    QVBoxLayout, QWidget,
)

from app.database import models
from .widgets import SectionHeader, SummaryCard, fill_table, make_table
from .styles import ACCENT, SUCCESS, INFO, WARNING, DANGER


class PortfoliosPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._summaries: list[dict] = []
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        layout.addWidget(SectionHeader("Portfolios", "Progress and mission breakdown by portfolio"))

        splitter = QSplitter(Qt.Horizontal)

        # ── Left: portfolio list ──────────────────────────────────────────
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 8, 0)
        left_layout.addWidget(QLabel("Portfolios"))
        self._list = QListWidget()
        self._list.setFixedWidth(220)
        self._list.currentRowChanged.connect(self._on_select)
        left_layout.addWidget(self._list)
        splitter.addWidget(left)

        # ── Right: detail panel ───────────────────────────────────────────
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(8, 0, 0, 0)
        right_layout.setSpacing(12)

        self._detail_title = QLabel("Select a portfolio")
        self._detail_title.setObjectName("sectionTitle")
        right_layout.addWidget(self._detail_title)

        # cards row
        cards_row = QHBoxLayout()
        cards_row.setSpacing(10)
        self._cards: dict[str, SummaryCard] = {}
        for key, label, color in [
            ("total",      "Total",      ACCENT),
            ("completed",  "Completed",  SUCCESS),
            ("invoiced",   "Invoiced",   INFO),
            ("planning",   "Planning",   WARNING),
            ("cancelled",  "Cancelled",  DANGER),
            ("in_progress","In Progress","#9C27B0"),
        ]:
            c = SummaryCard(label, "—", color)
            self._cards[key] = c
            cards_row.addWidget(c)
        right_layout.addLayout(cards_row)

        # Progress bar
        prog_row = QHBoxLayout()
        prog_row.addWidget(QLabel("Completion:"))
        self._progress = QProgressBar()
        self._progress.setRange(0, 100)
        self._progress.setFixedHeight(18)
        self._progress.setStyleSheet(f"""
            QProgressBar {{ background:#2A2A3E; border-radius:4px; border:1px solid #3A3A5C; }}
            QProgressBar::chunk {{ background:{SUCCESS}; border-radius:4px; }}
        """)
        prog_row.addWidget(self._progress)
        right_layout.addLayout(prog_row)

        # Notes
        notes_row = QHBoxLayout()
        notes_row.addWidget(QLabel("Notes:"))
        self._save_notes_btn = QPushButton("Save Notes")
        self._save_notes_btn.setObjectName("secondary")
        self._save_notes_btn.clicked.connect(self._save_notes)
        notes_row.addStretch()
        notes_row.addWidget(self._save_notes_btn)
        right_layout.addLayout(notes_row)

        self._notes_edit = QTextEdit()
        self._notes_edit.setMaximumHeight(80)
        self._notes_edit.setPlaceholderText("Add notes about this portfolio…")
        right_layout.addWidget(self._notes_edit)

        # Mission list
        right_layout.addWidget(QLabel("Missions in this portfolio"))
        self._mission_table = make_table(
            ["Mission ID", "Status", "Date", "Location", "Pilot"]
        )
        right_layout.addWidget(self._mission_table)

        splitter.addWidget(right)
        splitter.setSizes([220, 900])
        layout.addWidget(splitter)

        self._selected_portfolio_id: int | None = None

    def refresh(self) -> None:
        self._summaries = models.get_portfolio_summary()
        self._list.clear()
        for p in self._summaries:
            item = QListWidgetItem(f"{p['portfolio']}\n{p['client']}")
            item.setData(Qt.UserRole, p["id"])
            self._list.addItem(item)

        if self._summaries:
            self._list.setCurrentRow(0)

    def _on_select(self, row: int) -> None:
        if row < 0 or row >= len(self._summaries):
            return
        p = self._summaries[row]
        self._selected_portfolio_id = p["id"]
        self._detail_title.setText(f"{p['portfolio']}  —  {p['client']}")

        total = p.get("total") or 0
        done = (p.get("completed") or 0) + (p.get("invoiced") or 0)

        for key in ("total", "completed", "invoiced", "planning", "cancelled", "in_progress"):
            self._cards[key].set_value(p.get(key) or 0)

        pct = int(done / total * 100) if total else 0
        self._progress.setValue(pct)
        self._progress.setFormat(f"{pct}%  ({done}/{total})")

        self._notes_edit.setPlainText(p.get("notes") or "")

        missions = models.list_missions({"portfolio": p["portfolio"]})
        rows = []
        for m in missions:
            rows.append({
                "mission_id":  m.get("mission_id"),
                "status":      m.get("status"),
                "mission_date":m.get("mission_date") or "—",
                "location":    m.get("location") or "—",
                "pilot":       m.get("pilot") or "—",
            })
        fill_table(self._mission_table, rows,
                   ["mission_id", "status", "mission_date", "location", "pilot"])

    def _save_notes(self) -> None:
        if self._selected_portfolio_id is None:
            return
        models.update_portfolio_notes(self._selected_portfolio_id, self._notes_edit.toPlainText())
