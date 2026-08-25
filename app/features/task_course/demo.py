import sys

from PySide6.QtWidgets import QApplication

from app.shell.placeholder_page import PlaceholderPage


def main() -> int:
    app = QApplication.instance() or QApplication(sys.argv)
    window = PlaceholderPage("任务、课表与提醒独立演示", "1号 arcadiamuran-web")
    window.resize(720, 480)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())

