"""Main application window with sidebar navigation."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QMainWindow, QPushButton,
    QSizePolicy, QStackedWidget, QVBoxLayout, QWidget,
)

from .dashboard import DashboardPage
from .missions import MissionsPage
from .portfolios import PortfoliosPage
from .weekly_update import WeeklyUpdatePage
from .tickets import TicketsPage
from .import_export import ImportExportPage
from .styles import STYLESHEET


NAV_ITEMS = [
    ("Dashboard",       "📊", DashboardPage),
    ("Missions",        "🗺️",  MissionsPage),
    ("Portfolios",      "📁", PortfoliosPage),
    ("Weekly Update",   "📅", WeeklyUpdatePage),
    ("Tickets",         "🎫", TicketsPage),
    ("Import / Export", "⬆️",  ImportExportPage),
]


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mission Tracker")
        self.setMinimumSize(1280, 800)
        self.setStyleSheet(STYLESHEET)

        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Sidebar ──────────────────────────────────────────────────────────
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(2)

        app_title = QLabel("Mission Tracker")
        app_title.setObjectName("appTitle")
        sidebar_layout.addWidget(app_title)

        self._nav_buttons: list[QPushButton] = []
        self._pages: list[QWidget] = []
        self._stack = QStackedWidget()

        for label, icon, PageClass in NAV_ITEMS:
            page = PageClass()
            self._stack.addWidget(page)
            self._pages.append(page)

            btn = QPushButton(f"  {icon}  {label}")
            btn.setCheckable(False)
            btn.clicked.connect(lambda _, i=len(self._nav_buttons): self._navigate(i))
            self._nav_buttons.append(btn)
            sidebar_layout.addWidget(btn)

        sidebar_layout.addStretch()

        # version label at bottom
        ver = QLabel("v1.0")
        ver.setAlignment(Qt.AlignCenter)
        ver.setStyleSheet("color: #404060; font-size: 11px; padding: 8px;")
        sidebar_layout.addWidget(ver)

        root.addWidget(sidebar)
        root.addWidget(self._stack)

        # start on Dashboard
        self._navigate(0)

    def _navigate(self, index: int) -> None:
        for i, btn in enumerate(self._nav_buttons):
            btn.setProperty("active", str(i == index).lower())
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        self._stack.setCurrentIndex(index)
        page = self._pages[index]
        if hasattr(page, "refresh"):
            page.refresh()
