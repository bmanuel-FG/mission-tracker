"""Import / Export tab."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QFileDialog, QFormLayout, QGroupBox, QHBoxLayout,
    QLabel, QMessageBox, QProgressBar, QPushButton,
    QTextEdit, QVBoxLayout, QWidget,
)

from app.database import models
from app.services.csv_import import import_csv
from app.services.csv_export import (
    export_all_missions, export_filtered_missions,
    export_tickets, export_portfolio_summary, export_weekly_update,
)
from .widgets import SectionHeader, fill_table, make_table


class ImportWorker(QThread):
    finished = Signal(dict)

    def __init__(self, path: str):
        super().__init__()
        self._path = path

    def run(self):
        result = import_csv(self._path)
        self.finished.emit(result)


class ImportExportPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(20)

        layout.addWidget(SectionHeader("Import / Export", "Load CSV data and export reports"))

        two_col = QHBoxLayout()
        two_col.setSpacing(24)

        # ── Import section ────────────────────────────────────────────────
        import_box = QGroupBox("CSV Import")
        import_box.setStyleSheet("""
            QGroupBox { border:1px solid #3A3A5C; border-radius:8px; margin-top:8px;
                        font-weight:600; color:#9090B0; padding:12px; }
            QGroupBox::title { subcontrol-origin:margin; left:10px; }
        """)
        ib_layout = QVBoxLayout(import_box)

        info = QLabel(
            "Select a CSV file exported from your mission management system.\n"
            "The app will match missions by Mission ID, detect changes, and update the database."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color:#9090B0; font-size:12px;")
        ib_layout.addWidget(info)

        select_btn = QPushButton("Select CSV File…")
        select_btn.clicked.connect(self._select_file)
        ib_layout.addWidget(select_btn)

        self._file_lbl = QLabel("No file selected")
        self._file_lbl.setStyleSheet("color:#606080; font-size:12px;")
        ib_layout.addWidget(self._file_lbl)

        self._import_btn = QPushButton("Import")
        self._import_btn.setEnabled(False)
        self._import_btn.clicked.connect(self._run_import)
        ib_layout.addWidget(self._import_btn)

        self._progress = QProgressBar()
        self._progress.setRange(0, 0)
        self._progress.setVisible(False)
        self._progress.setFixedHeight(6)
        self._progress.setStyleSheet("""
            QProgressBar { background:#2A2A3E; border-radius:3px; }
            QProgressBar::chunk { background:#4A90D9; border-radius:3px; }
        """)
        ib_layout.addWidget(self._progress)

        ib_layout.addWidget(QLabel("Import Summary:"))
        self._summary = QTextEdit()
        self._summary.setReadOnly(True)
        self._summary.setFixedHeight(180)
        ib_layout.addWidget(self._summary)

        two_col.addWidget(import_box)

        # ── Export section ────────────────────────────────────────────────
        export_box = QGroupBox("CSV Export")
        export_box.setStyleSheet(import_box.styleSheet())
        eb_layout = QVBoxLayout(export_box)

        exports = [
            ("All Missions",        self._export_all_missions),
            ("Filtered Missions",   self._export_filtered),
            ("Ticket List",         self._export_tickets),
            ("Portfolio Summary",   self._export_portfolio),
            ("Weekly Update Report",self._export_weekly),
        ]
        for label, handler in exports:
            btn = QPushButton(f"Export — {label}")
            btn.setObjectName("secondary")
            btn.clicked.connect(handler)
            eb_layout.addWidget(btn)

        eb_layout.addStretch()
        two_col.addWidget(export_box)

        layout.addLayout(two_col)

        # ── Import history ────────────────────────────────────────────────
        layout.addWidget(QLabel("<b>Import History</b>"))
        self._history_table = make_table(
            ["Filename", "Imported At", "Total", "Added", "Updated", "Unchanged"]
        )
        self._history_table.setMaximumHeight(240)
        layout.addWidget(self._history_table)

        self._file_path: str | None = None

    def refresh(self) -> None:
        self._load_history()

    def _load_history(self) -> None:
        imports = models.list_imports()
        rows = []
        for i in imports:
            rows.append({
                "filename":    i.get("filename"),
                "imported_at": (i.get("imported_at") or "")[:16],
                "rows_total":  i.get("rows_total"),
                "rows_added":  i.get("rows_added"),
                "rows_updated":i.get("rows_updated"),
                "rows_unchanged":i.get("rows_unchanged"),
            })
        fill_table(self._history_table, rows,
                   ["filename", "imported_at", "rows_total", "rows_added", "rows_updated", "rows_unchanged"])
        self._history_table.setHorizontalHeaderLabels(
            ["Filename", "Imported At", "Total", "Added", "Updated", "Unchanged"])

    def _select_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Select Mission CSV", "", "CSV Files (*.csv)")
        if path:
            self._file_path = path
            self._file_lbl.setText(Path(path).name)
            self._import_btn.setEnabled(True)

    def _run_import(self) -> None:
        if not self._file_path:
            return
        self._import_btn.setEnabled(False)
        self._progress.setVisible(True)
        self._summary.setPlainText("Importing…")

        self._worker = ImportWorker(self._file_path)
        self._worker.finished.connect(self._on_import_done)
        self._worker.start()

    def _on_import_done(self, result: dict) -> None:
        self._progress.setVisible(False)
        self._import_btn.setEnabled(True)

        if not result.get("success"):
            self._summary.setPlainText(f"ERROR:\n{result.get('error')}")
            return

        lines = [
            f"File:      {result['filename']}",
            f"Total:     {result['total']}",
            f"Added:     {result['added']}",
            f"Updated:   {result['updated']}",
            f"Unchanged: {result['unchanged']}",
            "",
            "Status Transitions:",
        ]
        for status, mids in result.get("status_transitions", {}).items():
            lines.append(f"  → {status}: {len(mids)} mission(s)")
            for mid in mids[:5]:
                lines.append(f"       {mid}")
            if len(mids) > 5:
                lines.append(f"       … and {len(mids)-5} more")

        self._summary.setPlainText("\n".join(lines))
        self._load_history()

    def _save_dialog(self, default: str) -> str | None:
        path, _ = QFileDialog.getSaveFileName(self, "Save Export", default, "CSV Files (*.csv)")
        return path or None

    def _export_all_missions(self) -> None:
        p = self._save_dialog("all_missions.csv")
        if p:
            export_all_missions(p)
            QMessageBox.information(self, "Exported", f"Saved to:\n{p}")

    def _export_filtered(self) -> None:
        p = self._save_dialog("filtered_missions.csv")
        if p:
            export_filtered_missions(p, {})
            QMessageBox.information(self, "Exported", f"Saved to:\n{p}")

    def _export_tickets(self) -> None:
        p = self._save_dialog("tickets.csv")
        if p:
            export_tickets(p)
            QMessageBox.information(self, "Exported", f"Saved to:\n{p}")

    def _export_portfolio(self) -> None:
        p = self._save_dialog("portfolio_summary.csv")
        if p:
            export_portfolio_summary(p)
            QMessageBox.information(self, "Exported", f"Saved to:\n{p}")

    def _export_weekly(self) -> None:
        p = self._save_dialog("weekly_update.csv")
        if p:
            export_weekly_update(p)
            QMessageBox.information(self, "Exported", f"Saved to:\n{p}")
