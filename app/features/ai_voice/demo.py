import sys

from PySide6.QtWidgets import QApplication

from app.shell.placeholder_page import PlaceholderPage


def main() -> int:
    app = QApplication.instance() or QApplication(sys.argv)
    window = PlaceholderPage("AI与语音输入独立演示", "2号 muzi2887")
    window.resize(720, 480)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())

