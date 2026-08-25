"""3号模块：天气、系统状态与设置页面。"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.core.app_context import AppContext
from app.core.contracts import WeatherSummary
from app.features.weather_system.workers import WeatherFetcher


class _Section(QFrame):
    """带标题的卡片分区。"""

    def __init__(self, title: str, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("sectionCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        heading = QLabel(title)
        heading.setObjectName("sectionTitle")
        layout.addWidget(heading)


class WeatherPage(QWidget):
    def __init__(self, context: AppContext, parent=None) -> None:
        super().__init__(parent)
        self.context = context
        self._fetchers: list[WeatherFetcher] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(14)

        heading = QLabel("天气")
        heading.setObjectName("pageTitle")
        layout.addWidget(heading)

        card = _Section("实时天气")
        self._card_layout = card.layout()
        row = QHBoxLayout()
        row.setSpacing(10)

        self.city_input = QLineEdit()
        self.city_input.setPlaceholderText("输入城市名，如：武汉")
        settings = context.get_service("settings")
        self.city_input.setText(settings.get("city", ""))

        self.query_button = QPushButton("查询")
        row.addWidget(self.city_input, 1)
        row.addWidget(self.query_button)
        self._card_layout.addLayout(row)

        self.weather_label = QLabel("输入城市后点击查询")
        self.weather_label.setObjectName("mutedText")
        self.weather_label.setWordWrap(True)
        self._card_layout.addWidget(self.weather_label)

        self._show_cached()

        layout.addWidget(card)
        layout.addStretch(1)

        self.query_button.clicked.connect(self._on_query)

    def _show_cached(self) -> None:
        cached = self.context.get_service("weather").get_cached(self.city_input.text().strip())
        if cached is not None:
            rain = f"降雨概率 {cached.rain_probability}%" if cached.rain_probability is not None else "暂无降雨数据"
            self.weather_label.setText(
                f"{cached.city}  {cached.temperature_c}°C（缓存）\n"
                f"{cached.description}\n{rain}"
            )

    def _on_query(self) -> None:
        city = self.city_input.text().strip()
        if not city:
            self.weather_label.setText("请输入城市名")
            return
        settings = self.context.get_service("settings")
        settings.set("city", city)

        self.weather_label.setText("正在查询…")
        self.query_button.setEnabled(False)
        fetcher = WeatherFetcher(city)
        self._fetchers.append(fetcher)

        def cleanup() -> None:
            if fetcher in self._fetchers:
                self._fetchers.remove(fetcher)

        def on_done(summary: WeatherSummary) -> None:
            rain = f"降雨概率 {summary.rain_probability}%" if summary.rain_probability is not None else "暂无降雨数据"
            self.weather_label.setText(
                f"{summary.city}  {summary.temperature_c}°C\n"
                f"{summary.description}\n{rain}"
            )
            self.query_button.setEnabled(True)
            cleanup()

        def on_failed(message: str) -> None:
            self.weather_label.setText(f"查询失败：{message}")
            self.query_button.setEnabled(True)
            cleanup()

        fetcher.done.connect(on_done)
        fetcher.failed.connect(on_failed)
        fetcher.start()


class SystemPage(QWidget):
    def __init__(self, context: AppContext, parent=None) -> None:
        super().__init__(parent)
        self.context = context

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(14)

        heading = QLabel("系统状态")
        heading.setObjectName("pageTitle")
        layout.addWidget(heading)

        card = _Section("资源占用")
        self._card_layout = card.layout()

        self.memory_label = QLabel("内存：--")
        self.disk_label = QLabel("磁盘：--")
        self.cpu_label = QLabel("CPU：--")
        self._card_layout.addWidget(self.memory_label)
        self._card_layout.addWidget(self.disk_label)
        self._card_layout.addWidget(self.cpu_label)

        self.refresh_button = QPushButton("刷新")
        self._card_layout.addWidget(self.refresh_button, alignment=Qt.AlignmentFlag.AlignLeft)

        layout.addWidget(card)
        layout.addStretch(1)

        self.refresh_button.clicked.connect(self._on_refresh)
        self._on_refresh()

    def _on_refresh(self) -> None:
        summary = self.context.get_service("system").snapshot()
        self.memory_label.setText(f"内存：{summary.memory_percent}%")
        self.disk_label.setText(f"磁盘：{summary.disk_percent}%")
        if summary.cpu_percent is not None:
            self.cpu_label.setText(f"CPU：{summary.cpu_percent}%")


class SettingsPage(QWidget):
    def __init__(self, context: AppContext, parent=None) -> None:
        super().__init__(parent)
        self.context = context
        self.settings = context.get_service("settings")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(14)

        heading = QLabel("设置")
        heading.setObjectName("pageTitle")
        layout.addWidget(heading)

        card = _Section("偏好设置")
        form = QFormLayout()
        form.setContentsMargins(0, 12, 0, 0)
        form.setSpacing(12)

        self.city_input = QLineEdit(self.settings.get("city", ""))
        self.key_input = QLineEdit(self.settings.get("openrouter_key", ""))
        self.key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.key_input.setPlaceholderText("OpenRouter API Key（可选，不会写入仓库）")
        self.voice_check = QCheckBox("启用语音提示")
        self.voice_check.setChecked(bool(self.settings.get("voice_enabled", True)))
        self.autostart_check = QCheckBox("开机自启")
        self.autostart_check.setChecked(context.get_service("autostart").is_enabled())

        form.addRow("默认城市", self.city_input)
        form.addRow("OpenRouter Key", self.key_input)
        form.addRow("", self.voice_check)
        form.addRow("", self.autostart_check)
        self._card_layout = card.layout()
        self._card_layout.addLayout(form)

        self.save_button = QPushButton("保存设置")
        self._card_layout.addWidget(self.save_button, alignment=Qt.AlignmentFlag.AlignLeft)

        self.status_label = QLabel("")
        self.status_label.setObjectName("mutedText")
        self._card_layout.addWidget(self.status_label)

        layout.addWidget(card)
        layout.addStretch(1)

        self.save_button.clicked.connect(self._on_save)

    def _on_save(self) -> None:
        self.settings.set("city", self.city_input.text().strip() or "武汉")
        self.settings.set("openrouter_key", self.key_input.text().strip())
        self.settings.set("voice_enabled", self.voice_check.isChecked())
        self.context.get_service("autostart").set_enabled(self.autostart_check.isChecked())
        self.context.events.settings_changed.emit()
        self.status_label.setText("已保存")


def create_weather_page(context: AppContext) -> WeatherPage:
    return WeatherPage(context)


def create_system_page(context: AppContext) -> SystemPage:
    return SystemPage(context)


def create_settings_page(context: AppContext) -> SettingsPage:
    return SettingsPage(context)