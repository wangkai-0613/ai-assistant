import sys

from PySide6.QtWidgets import QApplication

from app.shell.placeholder_page import PlaceholderPage


def main() -> int:
    app = QApplication.instance() or QApplication(sys.argv)
    window = PlaceholderPage("天气、系统状态与设置独立演示", "3号 Fysync")
    window.resize(720, 480)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())

