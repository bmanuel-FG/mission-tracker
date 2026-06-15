"""Dashboard page — summary cards + tables."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox, QHBoxLayout, QLabel, QScrollArea,
    QSizePolicy, QVBoxLayout, QWidget,
)

from app.database import models
from .widgets import SectionHeader, SummaryCard, fill_table, make_table
from .styles import (
    ACCENT, SUCCESS, INFO, WARNING, DANGER, TEXT_SECONDARY,
    STATUS_COLORS,
)


class DashboardPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._filters: dict = {}
        self._build_ui()

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 20, 24, 20)
        outer.setSpacing(16)

        outer.addWidget(SectionHeader("Dashboard", "Mission portfolio overview"))

        # ── Filters ──────────────────────────────────────────────────────────
        filter_row = QHBoxLayout()
        filter_row.setSpacing(10)

        self._client_cb = QComboBox()
        self._client_cb.addItem("All Clients")
        self._portfolio_cb = QComboBox()
        self._portfolio_cb.addItem("All Portfolios")

        for cb, lbl in [(self._client_cb, "Client"), (self._portfolio_cb, "Portfolio")]:
            filter_row.addWidget(QLabel(lbl + ":"))
            cb.setFixedWidth(180)
            filter_row.addWidget(cb)
            cb.currentIndexChanged.connect(self._on_filter_change)

        filter_row.addStretch()
        outer.addLayout(filter_row)

        # ── Summary cards ─────────────────────────────────────────────────
        cards_row = QHBoxLayout()
        cards_row.setSpacing(12)

        self._cards: dict[str, SummaryCard] = {}
        card_defs = [
            ("total",       "Total Missions", ACCENT),
            ("completed",   "Completed",      SUCCESS),
            ("invoiced",    "Invoiced",       INFO),
            ("planning",    "Planning",       WARNING),
            ("cancelled",   "Cancelled",      DANGER),
            ("in_progress", "In Progress",    "#9C27B0"),
            ("open_tickets","Open Tickets",   "#FF5722"),
        ]
        for key, label, color in card_defs:
            card = SummaryCard(label, "—", color)
            self._cards[key] = card
            cards_row.addWidget(card)

        outer.addLayout(cards_row)

        # ── Two-column lower section ──────────────────────────────────────
        lower = QHBoxLayout()
        lower.setSpacing(16)

        # By status
        left = QVBoxLayout()
        left.addWidget(QLabel("Status Breakdown"))
        self._status_table = make_table(["Status", "Count"])
        self._status_table.setMaximumHeight(240)
        left.addWidget(self._status_table)
        lower.addLayout(left)

        # By portfolio
        right = QVBoxLayout()
        right.addWidget(QLabel("Portfolio Progress"))
        self._portfolio_table = make_table(["Portfolio", "Total", "Done", "%"])
        self._portfolio_table.setMaximumHeight(240)
        right.addWidget(self._portfolio_table)
        lower.addLayout(right)

        outer.addLayout(lower)

        # ── Recent missions ───────────────────────────────────────────────
        outer.addWidget(QLabel("Recently Updated Missions"))
        self._recent_table = make_table(
            ["Mission ID", "Status", "Client", "Portfolio", "Updated"]
        )
        self._recent_table.setMaximumHeight(280)
        outer.addWidget(self._recent_table)
        outer.addStretch()

    def refresh(self) -> None:
        self._load_filters()
        self._reload()

    def _load_filters(self) -> None:
        clients = ["All Clients"] + [c["name"] for c in models.list_clients()]
        portfolios = ["All Portfolios"] + [p["name"] for p in models.list_portfolios()]

        for cb, items in [(self._client_cb, clients), (self._portfolio_cb, portfolios)]:
            cb.blockSignals(True)
            current = cb.currentText()
            cb.clear()
            cb.addItems(items)
            idx = cb.findText(current)
            if idx >= 0:
                cb.setCurrentIndex(idx)
            cb.blockSignals(False)

    def _build_filters(self) -> dict:
        f: dict = {}
        c = self._client_cb.currentText()
        p = self._portfolio_cb.currentText()
        if c != "All Clients":
            f["client"] = c
        if p != "All Portfolios":
            f["portfolio"] = p
        return f

    def _on_filter_change(self) -> None:
        self._reload()

    def _reload(self) -> None:
        metrics = models.get_dashboard_metrics(self._build_filters())

        for key, card in self._cards.items():
            card.set_value(metrics.get(key, 0) or 0)

        # status table
        fill_table(self._status_table,
                   metrics.get("by_status", []),
                   ["status", "cnt"])
        self._status_table.setHorizontalHeaderLabels(["Status", "Count"])

        # portfolio table
        portfolio_rows = []
        for r in metrics.get("by_portfolio", []):
            total = r.get("total") or 0
            done = r.get("done") or 0
            pct = f"{int(done/total*100)}%" if total else "—"
            portfolio_rows.append({
                "portfolio": r.get("portfolio") or "—",
                "total": total,
                "done": done,
                "pct": pct,
            })
        fill_table(self._portfolio_table, portfolio_rows, ["portfolio", "total", "done", "pct"])
        self._portfolio_table.setHorizontalHeaderLabels(["Portfolio", "Total", "Done", "%"])

        # recent missions
        recent_rows = []
        for r in metrics.get("recent_missions", []):
            recent_rows.append({
                "mission_id": r.get("mission_id"),
                "status": r.get("status"),
                "client_name": r.get("client_name") or "—",
                "portfolio_name": r.get("portfolio_name") or "—",
                "updated_at": (r.get("updated_at") or "")[:16],
            })
        fill_table(self._recent_table, recent_rows,
                   ["mission_id", "status", "client_name", "portfolio_name", "updated_at"])
        self._recent_table.setHorizontalHeaderLabels(
            ["Mission ID", "Status", "Client", "Portfolio", "Updated"])
