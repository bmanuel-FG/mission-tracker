"""Shared stylesheet and colour palette."""

ACCENT = "#6366F1"        # Indigo 500
ACCENT_HOVER = "#4F46E5"  # Indigo 600
BG_DARK = "#0F172A"       # Slate 900
BG_MID = "#1E293B"        # Slate 800
BG_CARD = "#1E293B"       # Slate 800
BG_TABLE = "#0F172A"      # Slate 900
TEXT_PRIMARY = "#E2E8F0"  # Slate 200
TEXT_SECONDARY = "#94A3B8"# Slate 400
TEXT_MUTED = "#64748B"    # Slate 500
BORDER = "#334155"        # Slate 700
SUCCESS = "#10B981"
WARNING = "#F59E0B"
DANGER = "#EF4444"
INFO = "#3B82F6"

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
    background-color: rgba(99, 102, 241, 0.15);
    color: {TEXT_PRIMARY};
}}
#sidebar QPushButton[active="true"] {{
    background-color: rgba(99, 102, 241, 0.25);
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
    alternate-background-color: {BG_MID};
    border: 1px solid {BORDER};
    border-radius: 8px;
    gridline-color: transparent;
    color: {TEXT_PRIMARY};
    selection-background-color: rgba(99, 102, 241, 0.2);
    selection-color: {TEXT_PRIMARY};
}}
QTableWidget::item {{
    padding: 8px 12px;
    border-bottom: 1px solid {BG_MID};
}}
QHeaderView::section {{
    background-color: {BG_MID};
    color: {TEXT_SECONDARY};
    padding: 10px 12px;
    border: none;
    border-bottom: 2px solid {BORDER};
    font-weight: 600;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}}
QHeaderView::section:hover {{
    background-color: {BORDER};
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
    background-color: #047857;
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
