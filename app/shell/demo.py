import sys

from PySide6.QtWidgets import QApplication

from app.core.app_context import AppContext
from app.core.events import AppEvents
from app.shell.main_window import MainWindow


def main() -> int:
    app = QApplication.instance() or QApplication(sys.argv)
    window = MainWindow(AppContext(events=AppEvents()))
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())

