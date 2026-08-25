import sys

from PySide6.QtWidgets import QApplication

from app.core.app_context import AppContext
from app.core.events import AppEvents
from app.shell.main_window import MainWindow


def build_context() -> AppContext:
    return AppContext(events=AppEvents())


def run() -> int:
    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName("小云桌面助手")
    app.setQuitOnLastWindowClosed(True)

    context = build_context()
    window = MainWindow(context)
    window.show()
    return app.exec()

