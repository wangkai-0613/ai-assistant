from datetime import date, datetime

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

    def __init__(self, navigate_callback, context=None, parent=None):
        super().__init__(parent)
        self._navigate = navigate_callback
        self._context = context
        self._value_labels: dict[str, QLabel] = {}

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
        layout.addStretch(1)

        scroll.setWidget(content)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

        self._setup_clock()
        self.refresh_data()
        if context is not None:
            context.events.task_created.connect(lambda _task: self.refresh_data())
            context.events.settings_changed.connect(self.refresh_data)
        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self.refresh_data)
        self._refresh_timer.start(10_000)

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
            now = datetime.now()
            weekday_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
            text = (
                f"{now:%Y}年{now:%m}月{now:%d}日 "
                f"{weekday_names[now.weekday()]} {now:%H:%M}"
            )
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
            ("📋", "待办任务", "正在读取…", "查看详情"),
            ("📅", "今日课程", "正在读取…", "查看课表"),
            ("🌤️", "今日天气", "正在读取…", "查看详情"),
            ("💻", "系统状态", "正在读取…", "查看详情"),
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
        self._value_labels[title] = value_label

        action_label = QLabel(action)
        action_label.setObjectName("cardDesc")
        action_label.setCursor(Qt.CursorShape.PointingHandCursor)
        target = {"待办任务": 1, "今日课程": 2, "今日天气": 4, "系统状态": 5}.get(title)
        if target is not None:
            action_label.mousePressEvent = lambda _event, index=target: self._navigate(index)

        layout.addLayout(header)
        layout.addWidget(value_label)
        layout.addWidget(action_label)
        return card

    def refresh_data(self) -> None:
        """从各业务服务读取首页摘要；单个服务失败不影响其他卡片。"""
        if self._context is None or not self._value_labels:
            return

        try:
            tasks = self._context.get_service("task").list_all()
            pending = sum(not task.completed for task in tasks)
            self._value_labels["待办任务"].setText(f"{pending} 项待完成")
        except (LookupError, OSError):
            self._value_labels["待办任务"].setText("暂时无法读取")

        try:
            today = date.today()
            courses = self._context.get_service("course").list_week(today)
            count = sum(
                course.course_date == today
                if course.course_date is not None
                else course.weekday == today.isoweekday()
                for course in courses
            )
            self._value_labels["今日课程"].setText(f"{count} 节课")
        except (LookupError, OSError):
            self._value_labels["今日课程"].setText("暂时无法读取")

        try:
            settings = self._context.get_service("settings")
            city = str(settings.get("city", "武汉"))
            weather = self._context.get_service("weather").get_cached(city)
            if weather is None:
                self._value_labels["今日天气"].setText("暂无天气数据")
            else:
                temperature = f"{weather.temperature_c:g}°C"
                self._value_labels["今日天气"].setText(
                    f"{weather.description} {temperature}"
                )
        except (LookupError, OSError):
            self._value_labels["今日天气"].setText("暂时无法读取")

        try:
            summary = self._context.get_service("system").snapshot()
            cpu = "--" if summary.cpu_percent is None else f"{summary.cpu_percent:.0f}%"
            self._value_labels["系统状态"].setText(
                f"CPU {cpu} · 内存 {summary.memory_percent:.0f}%"
            )
        except (LookupError, OSError):
            self._value_labels["系统状态"].setText("暂时无法读取")

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self.refresh_data()
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