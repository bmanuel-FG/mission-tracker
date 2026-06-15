"""Application entry point."""
import sys

# pyrefly: ignore [missing-import]
from PySide6.QtWidgets import QApplication
# pyrefly: ignore [missing-import]
from PySide6.QtGui import QIcon

from app.database.schema import init_db
from app.ui.main_window import MainWindow


def main() -> None:
    init_db()

    app = QApplication(sys.argv)
    app.setApplicationName("Mission Tracker")
    app.setOrganizationName("MissionTracker")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
