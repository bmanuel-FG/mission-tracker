"""Shared stylesheet and colour palette."""

ACCENT = "#4A90D9"
ACCENT_HOVER = "#357ABD"
BG_DARK = "#1E1E2E"
BG_MID = "#2A2A3E"
BG_CARD = "#2E2E42"
BG_TABLE = "#252535"
TEXT_PRIMARY = "#E0E0F0"
TEXT_SECONDARY = "#9090B0"
TEXT_MUTED = "#606080"
BORDER = "#3A3A5C"
SUCCESS = "#4CAF50"
WARNING = "#FF9800"
DANGER = "#F44336"
INFO = "#2196F3"

STATUS_COLORS = {
    "Completed":   "#4CAF50",
    "Invoiced":    "#2196F3",
    "Planning":    "#FF9800",
    "Cancelled":   "#F44336",
    "In Progress": "#9C27B0",
    "Unknown":     "#607D8B",
    "On Hold":     "#795548",
}

PRIORITY_COLORS = {
    "Low":      "#4CAF50",
    "Medium":   "#FF9800",
    "High":     "#F44336",
    "Critical": "#B71C1C",
}

STYLESHEET = f"""
QMainWindow, QWidget {{
    background-color: {BG_DARK};
    color: {TEXT_PRIMARY};
    font-family: 'Segoe UI', sans-serif;
    font-size: 13px;
}}

/* ── Sidebar ─────────────────────────────── */
#sidebar {{
    background-color: {BG_MID};
    border-right: 1px solid {BORDER};
    min-width: 200px;
    max-width: 200px;
}}
#sidebar QPushButton {{
    background: transparent;
    color: {TEXT_SECONDARY};
    border: none;
    border-radius: 6px;
    padding: 10px 16px;
    text-align: left;
    font-size: 13px;
}}
#sidebar QPushButton:hover {{
    background-color: rgba(74,144,217,0.15);
    color: {TEXT_PRIMARY};
}}
#sidebar QPushButton[active="true"] {{
    background-color: rgba(74,144,217,0.25);
    color: {ACCENT};
    font-weight: 600;
    border-left: 3px solid {ACCENT};
}}
#appTitle {{
    color: {ACCENT};
    font-size: 16px;
    font-weight: 700;
    padding: 20px 16px 10px 16px;
}}

/* ── Cards ───────────────────────────────── */
#card {{
    background-color: {BG_CARD};
    border: 1px solid {BORDER};
    border-radius: 8px;
    padding: 12px;
}}
#cardValue {{
    font-size: 28px;
    font-weight: 700;
    color: {TEXT_PRIMARY};
}}
#cardLabel {{
    font-size: 11px;
    color: {TEXT_SECONDARY};
    text-transform: uppercase;
    letter-spacing: 1px;
}}

/* ── Tables ──────────────────────────────── */
QTableWidget {{
    background-color: {BG_TABLE};
    border: 1px solid {BORDER};
    border-radius: 6px;
    gridline-color: {BORDER};
    color: {TEXT_PRIMARY};
    selection-background-color: rgba(74,144,217,0.3);
}}
QTableWidget::item {{
    padding: 6px 8px;
}}
QHeaderView::section {{
    background-color: {BG_MID};
    color: {TEXT_SECONDARY};
    padding: 8px;
    border: none;
    border-bottom: 1px solid {BORDER};
    font-weight: 600;
    font-size: 12px;
}}
QHeaderView::section:hover {{
    background-color: {BG_CARD};
}}

/* ── Inputs ──────────────────────────────── */
QLineEdit, QComboBox, QTextEdit, QSpinBox, QDateEdit {{
    background-color: {BG_MID};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER};
    border-radius: 4px;
    padding: 6px 8px;
}}
QLineEdit:focus, QComboBox:focus, QTextEdit:focus {{
    border-color: {ACCENT};
}}
QComboBox::drop-down {{
    border: none;
    width: 20px;
}}
QComboBox QAbstractItemView {{
    background-color: {BG_MID};
    color: {TEXT_PRIMARY};
    selection-background-color: {ACCENT};
    border: 1px solid {BORDER};
}}

/* ── Buttons ─────────────────────────────── */
QPushButton {{
    background-color: {ACCENT};
    color: white;
    border: none;
    border-radius: 5px;
    padding: 8px 18px;
    font-weight: 600;
}}
QPushButton:hover {{
    background-color: {ACCENT_HOVER};
}}
QPushButton:pressed {{
    background-color: #2A6099;
}}
QPushButton#secondary {{
    background-color: {BG_CARD};
    color: {TEXT_SECONDARY};
    border: 1px solid {BORDER};
}}
QPushButton#secondary:hover {{
    background-color: {BG_MID};
    color: {TEXT_PRIMARY};
}}
QPushButton#danger {{
    background-color: {DANGER};
}}
QPushButton#danger:hover {{
    background-color: #C62828;
}}

/* ── Labels / Section titles ─────────────── */
#sectionTitle {{
    font-size: 20px;
    font-weight: 700;
    color: {TEXT_PRIMARY};
    padding-bottom: 4px;
}}
#subTitle {{
    font-size: 13px;
    color: {TEXT_SECONDARY};
    padding-bottom: 8px;
}}

/* ── Scroll bars ─────────────────────────── */
QScrollBar:vertical {{
    background: {BG_DARK};
    width: 8px;
}}
QScrollBar::handle:vertical {{
    background: {BORDER};
    border-radius: 4px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}

/* ── Separators ──────────────────────────── */
QFrame[frameShape="4"], QFrame[frameShape="5"] {{
    color: {BORDER};
}}

/* ── Tab widget (used on some pages) ──────── */
QTabWidget::pane {{
    border: 1px solid {BORDER};
    border-radius: 6px;
    background: {BG_TABLE};
}}
QTabBar::tab {{
    background: {BG_MID};
    color: {TEXT_SECONDARY};
    padding: 8px 20px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 2px;
}}
QTabBar::tab:selected {{
    background: {BG_TABLE};
    color: {TEXT_PRIMARY};
    border-bottom: 2px solid {ACCENT};
}}
"""
