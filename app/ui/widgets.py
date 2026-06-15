"""Reusable widget helpers used across all tabs."""
from __future__ import annotations

# pyrefly: ignore [missing-import]
from PySide6.QtCore import Qt
# pyrefly: ignore [missing-import]
from PySide6.QtGui import QColor
# pyrefly: ignore [missing-import]
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QSizePolicy, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget,
)

from .styles import BG_CARD, BORDER, STATUS_COLORS, PRIORITY_COLORS, TEXT_SECONDARY


class SummaryCard(QWidget):
    """A metric card: big number + label + optional coloured accent line."""

    def __init__(self, label: str, value: str = "0", color: str = "#4A90D9", parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        accent = QFrame()
        accent.setFixedHeight(3)
        accent.setStyleSheet(f"background:{color}; border-radius:2px;")

        self._value_lbl = QLabel(str(value))
        self._value_lbl.setObjectName("cardValue")

        self._label_lbl = QLabel(label.upper())
        self._label_lbl.setObjectName("cardLabel")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(4)
        layout.addWidget(accent)
        layout.addWidget(self._value_lbl)
        layout.addWidget(self._label_lbl)

    def set_value(self, v: str | int) -> None:
        self._value_lbl.setText(str(v))


class SectionHeader(QWidget):
    def __init__(self, title: str, subtitle: str = "", parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 8)
        layout.setSpacing(2)
        t = QLabel(title)
        t.setObjectName("sectionTitle")
        layout.addWidget(t)
        if subtitle:
            s = QLabel(subtitle)
            s.setObjectName("subTitle")
            layout.addWidget(s)
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        layout.addWidget(sep)


def make_table(columns: list[str]) -> QTableWidget:
    t = QTableWidget()
    t.setColumnCount(len(columns))
    t.setHorizontalHeaderLabels(columns)
    t.setEditTriggers(QTableWidget.NoEditTriggers)
    t.setSelectionBehavior(QTableWidget.SelectRows)
    t.setAlternatingRowColors(True)
    t.setStyleSheet("alternate-background-color: rgba(255,255,255,0.03);")
    t.verticalHeader().setVisible(False)
    t.horizontalHeader().setStretchLastSection(True)
    t.setSortingEnabled(True)
    return t


def fill_table(table: QTableWidget, rows: list[dict], columns: list[str]) -> None:
    table.setSortingEnabled(False)
    table.setRowCount(len(rows))
    for r, row in enumerate(rows):
        for c, col in enumerate(columns):
            val = row.get(col, "")
            item = QTableWidgetItem(str(val) if val is not None else "")
            item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)

            # colour-code status / priority cells
            if col == "status" and val in STATUS_COLORS:
                item.setForeground(QColor(STATUS_COLORS[val]))
            elif col == "priority" and val in PRIORITY_COLORS:
                item.setForeground(QColor(PRIORITY_COLORS[val]))

            table.setItem(r, c, item)
    table.setSortingEnabled(True)
