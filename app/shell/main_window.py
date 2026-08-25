from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMainWindow,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.core.app_context import AppContext
from app.shell.placeholder_page import PlaceholderPage


class MainWindow(QMainWindow):
    PAGE_SPECS = (
        ("首页", "4号 nicheng12"),
        ("任务", "1号 arcadiamuran-web"),
        ("课表", "1号 arcadiamuran-web"),
        ("AI 助手", "2号 muzi2887"),
        ("天气", "3号 Fysync"),
        ("系统状态", "3号 Fysync"),
        ("设置", "3号 Fysync"),
    )

    def __init__(self, context: AppContext, parent=None):
        super().__init__(parent)
        self.context = context
        self.setWindowTitle("小云桌面助手")
        self.resize(1040, 700)
        self.setMinimumSize(860, 560)

        root = QWidget()
        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(190)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(16, 24, 16, 20)

        brand = QLabel("🐱  小云助手")
        brand.setObjectName("brand")
        self.navigation = QListWidget()
        self.navigation.addItems([name for name, _ in self.PAGE_SPECS])
        self.navigation.setCurrentRow(0)

        sidebar_layout.addWidget(brand)
        sidebar_layout.addSpacing(16)
        sidebar_layout.addWidget(self.navigation)

        self.pages = QStackedWidget()
        for title, owner in self.PAGE_SPECS:
            self.pages.addWidget(PlaceholderPage(title, owner))

        root_layout.addWidget(sidebar)
        root_layout.addWidget(self.pages, 1)
        self.setCentralWidget(root)

        self.navigation.currentRowChanged.connect(self.pages.setCurrentIndex)
        context.events.status_message.connect(self.statusBar().showMessage)
        self._load_stylesheet()

    def replace_page(self, index: int, page: QWidget) -> None:
        old_page = self.pages.widget(index)
        self.pages.removeWidget(old_page)
        old_page.deleteLater()
        self.pages.insertWidget(index, page)

    def _load_stylesheet(self) -> None:
        style_path = Path(__file__).resolve().parents[1] / "resources" / "style.qss"
        if style_path.exists():
            self.setStyleSheet(style_path.read_text(encoding="utf-8"))

