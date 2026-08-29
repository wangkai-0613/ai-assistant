from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)


class HomePage(QWidget):
    NAV_INDEX_MAP = {
        "任务": 1,
        "课表": 2,
        "AI 助手": 3,
        "天气": 4,
        "系统状态": 5,
        "设置": 6,
    }

    def __init__(self, navigate_callback, parent=None):
        super().__init__(parent)
        self._navigate = navigate_callback

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(24)

        layout.addWidget(self._build_welcome())
        layout.addWidget(self._build_quick_actions())
        layout.addWidget(self._build_cards())
        layout.addWidget(self._build_cat_section())
        layout.addStretch(1)

        scroll.setWidget(content)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

        self._setup_clock()

    def _build_welcome(self) -> QWidget:
        section = QWidget()
        section.setObjectName("welcomeSection")
        layout = QVBoxLayout(section)
        layout.setSpacing(6)

        title = QLabel("欢迎回来 👋")
        title.setObjectName("welcomeTitle")
        self._time_label = QLabel("")
        self._time_label.setObjectName("welcomeSubtitle")

        layout.addWidget(title)
        layout.addWidget(self._time_label)
        return section

    def _setup_clock(self) -> None:
        def update():
            from datetime import datetime

            now = datetime.now()
            weekday_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
            text = f"{now:%Y年%m月%d日} {weekday_names[now.weekday()]} {now:%H:%M}"
            self._time_label.setText(text)

        update()
        timer = QTimer(self)
        timer.timeout.connect(update)
        timer.start(30_000)

    def _build_quick_actions(self) -> QWidget:
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        actions = [
            ("📋 任务", "管理待办"),
            ("📅 课表", "查看课程"),
            ("🤖 AI 助手", "智能问答"),
            ("🌤️ 天气", "今日天气"),
        ]

        for label, desc in actions:
            card = self._make_quick_card(label, desc)
            layout.addWidget(card)

        return container

    def _make_quick_card(self, label: str, desc: str) -> QWidget:
        card = QWidget()
        card.setObjectName("card")
        card.setCursor(Qt.CursorShape.PointingHandCursor)
        card.setMinimumWidth(160)

        layout = QVBoxLayout(card)
        layout.setSpacing(4)

        title = QLabel(label)
        title.setObjectName("cardTitle")
        subtitle = QLabel(desc)
        subtitle.setObjectName("cardDesc")

        layout.addWidget(title)
        layout.addWidget(subtitle)

        page_name = label.split(" ")[-1]
        index = self.NAV_INDEX_MAP.get(page_name)
        if index is not None:

            def make_handler(idx):
                return lambda _=None: self._navigate(idx)

            card.mousePressEvent = make_handler(index)

        return card

    def _build_cards(self) -> QWidget:
        container = QWidget()
        grid = QGridLayout(container)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(16)

        card_data = [
            ("📋", "待办任务", "3 项待完成", "查看详情"),
            ("📅", "今日课程", "2 节课", "查看课表"),
            ("🌤️", "今日天气", "晴 26°C", "查看详情"),
            ("💻", "系统状态", "运行正常", "查看详情"),
        ]

        for i, (icon, title, value, action) in enumerate(card_data):
            card = self._make_info_card(icon, title, value, action)
            row, col = divmod(i, 2)
            grid.addWidget(card, row, col)

        return container

    def _make_info_card(
        self, icon: str, title: str, value: str, action: str
    ) -> QWidget:
        card = QWidget()
        card.setObjectName("card")
        card.setMinimumHeight(110)

        layout = QVBoxLayout(card)
        layout.setSpacing(6)

        header = QHBoxLayout()
        icon_label = QLabel(icon)
        icon_label.setFont(QFont("Microsoft YaHei UI", 18))
        title_label = QLabel(title)
        title_label.setObjectName("cardTitle")
        header.addWidget(icon_label)
        header.addWidget(title_label)
        header.addStretch()

        value_label = QLabel(value)
        value_label.setObjectName("cardValue")

        action_label = QLabel(action)
        action_label.setObjectName("cardDesc")
        action_label.setCursor(Qt.CursorShape.PointingHandCursor)

        layout.addLayout(header)
        layout.addWidget(value_label)
        layout.addWidget(action_label)
        return card

    def _build_cat_section(self) -> QWidget:
        container = QWidget()
        container.setObjectName("card")
        layout = QVBoxLayout(container)
        layout.setSpacing(8)

        title = QLabel("🐱 小云宠物")
        title.setObjectName("cardTitle")

        self._cat_label = QLabel("🐱")
        self._cat_label.setFont(QFont("Microsoft YaHei UI", 48))
        self._cat_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._cat_label.setMinimumHeight(80)
        self._cat_label.setCursor(Qt.CursorShape.OpenHandCursor)

        hint = QLabel("拖拽小猫可以移动它哦～")
        hint.setObjectName("cardDesc")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(title)
        layout.addWidget(self._cat_label)
        layout.addWidget(hint)
        return container