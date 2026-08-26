from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMainWindow,
    QMenu,
    QStackedWidget,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
)

from app.core.app_context import AppContext
from app.shell.home_page import HomePage
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

        home_page = HomePage(navigate_callback=self._navigate_to)
        self.pages.addWidget(home_page)

        for title, owner in self.PAGE_SPECS[1:]:
            self.pages.addWidget(PlaceholderPage(title, owner))

        root_layout.addWidget(sidebar)
        root_layout.addWidget(self.pages, 1)
        self.setCentralWidget(root)

        self.navigation.currentRowChanged.connect(self.pages.setCurrentIndex)
        context.events.status_message.connect(self.statusBar().showMessage)
        self._load_stylesheet()
        self._setup_tray()

    def replace_page(self, index: int, page: QWidget) -> None:
        old_page = self.pages.widget(index)
        self.pages.removeWidget(old_page)
        old_page.deleteLater()
        self.pages.insertWidget(index, page)

    def _navigate_to(self, index: int) -> None:
        if 0 <= index < self.navigation.count():
            self.navigation.setCurrentRow(index)

    def _load_stylesheet(self) -> None:
        style_path = Path(__file__).resolve().parents[1] / "resources" / "style_dark.qss"
        if style_path.exists():
            self.setStyleSheet(style_path.read_text(encoding="utf-8"))

    def _setup_tray(self) -> None:
        self._tray_icon = QSystemTrayIcon(self)
        self._tray_icon.setIcon(self._make_tray_icon())
        self._tray_icon.setToolTip("小云桌面助手")

        tray_menu = QMenu()

        show_action = QAction("显示主窗口", self)
        show_action.triggered.connect(self._show_from_tray)

        exit_action = QAction("退出", self)
        exit_action.triggered.connect(self._real_quit)

        tray_menu.addAction(show_action)
        tray_menu.addSeparator()
        tray_menu.addAction(exit_action)

        self._tray_icon.setContextMenu(tray_menu)
        self._tray_icon.activated.connect(self._on_tray_activated)
        self._tray_icon.show()

        self._first_hide = True

    def _make_tray_icon(self) -> QIcon:
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(Qt.GlobalColor.white)
        painter.setPen(Qt.GlobalColor.darkGray)
        painter.drawEllipse(8, 8, 48, 48)
        painter.setPen(Qt.GlobalColor.darkGray)
        font = painter.font()
        font.setPixelSize(28)
        painter.setFont(font)
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "🐱")
        painter.end()
        return QIcon(pixmap)

    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._show_from_tray()

    def _show_from_tray(self) -> None:
        self.showNormal()
        self.activateWindow()
        self.raise_()

    def _real_quit(self) -> None:
        self._tray_icon.hide()
        QApplication.instance().quit()

    def closeEvent(self, event) -> None:
        if self._tray_icon.isVisible():
            if self._first_hide:
                self._tray_icon.showMessage(
                    "小云桌面助手",
                    "程序已最小化到系统托盘，双击图标可重新打开。",
                    QSystemTrayIcon.MessageIcon.Information,
                    2000,
                )
                self._first_hide = False
            self.hide()
            event.ignore()
        else:
            event.accept()