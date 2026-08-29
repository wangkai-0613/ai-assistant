"""3号模块：天气、系统状态与设置页面。"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QProgressBar,
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
        fetcher = WeatherFetcher(city, self.context.get_service("weather"))
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
        self.local_ai = context.get_service("local_ai")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(14)

        heading = QLabel("设置")
        heading.setObjectName("pageTitle")
        layout.addWidget(heading)

        local_card = _Section("本地 AI（一键安装，无需 Ollama）")
        local_layout = local_card.layout()
        path_row = QHBoxLayout()
        self.ai_path_input = QLineEdit(str(self.local_ai.install_dir))
        self.ai_path_input.setPlaceholderText("选择模型保存位置，建议放在空间充足的磁盘")
        self.ai_browse_button = QPushButton("选择位置")
        path_row.addWidget(self.ai_path_input, 1)
        path_row.addWidget(self.ai_browse_button)
        local_layout.addLayout(path_row)

        self.ai_status_label = QLabel("")
        self.ai_status_label.setObjectName("mutedText")
        self.ai_status_label.setWordWrap(True)
        local_layout.addWidget(self.ai_status_label)

        self.ai_progress = QProgressBar()
        self.ai_progress.setRange(0, 100)
        self.ai_progress.setValue(0)
        self.ai_progress.setTextVisible(True)
        local_layout.addWidget(self.ai_progress)

        ai_buttons = QHBoxLayout()
        self.ai_install_button = QPushButton("一键安装本地 AI")
        self.ai_cancel_button = QPushButton("取消下载")
        self.ai_cancel_button.setEnabled(False)
        self.ai_start_button = QPushButton("启动本地 AI")
        ai_buttons.addWidget(self.ai_install_button)
        ai_buttons.addWidget(self.ai_cancel_button)
        ai_buttons.addWidget(self.ai_start_button)
        ai_buttons.addStretch(1)
        local_layout.addLayout(ai_buttons)
        layout.addWidget(local_card)

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
        card.layout().addLayout(form)

        self.save_button = QPushButton("保存设置")
        card.layout().addWidget(self.save_button, alignment=Qt.AlignmentFlag.AlignLeft)

        self.status_label = QLabel("")
        self.status_label.setObjectName("mutedText")
        card.layout().addWidget(self.status_label)

        layout.addWidget(card)
        layout.addStretch(1)

        self.save_button.clicked.connect(self._on_save)
        self.ai_browse_button.clicked.connect(self._choose_ai_path)
        self.ai_install_button.clicked.connect(self._install_local_ai)
        self.ai_cancel_button.clicked.connect(self.local_ai.cancel_install)
        self.ai_start_button.clicked.connect(self._start_local_ai)
        self.local_ai.progress.connect(self.ai_progress.setValue)
        self.local_ai.status_changed.connect(self.ai_status_label.setText)
        self.local_ai.install_finished.connect(self._on_ai_install_finished)
        self._refresh_ai_status()

    def _choose_ai_path(self) -> None:
        path = QFileDialog.getExistingDirectory(
            self, "选择本地 AI 保存位置", self.ai_path_input.text()
        )
        if path:
            self.ai_path_input.setText(path)

    def _install_local_ai(self) -> None:
        try:
            self.local_ai.set_install_dir(self.ai_path_input.text().strip())
        except (OSError, RuntimeError, ValueError) as exc:
            self.ai_status_label.setText(f"无法使用该位置：{exc}")
            return
        self.ai_progress.setValue(0)
        self.ai_install_button.setEnabled(False)
        self.ai_browse_button.setEnabled(False)
        self.ai_cancel_button.setEnabled(True)
        self.ai_status_label.setText("准备下载…")
        self.local_ai.install()

    def _on_ai_install_finished(self, success: bool, message: str) -> None:
        self.ai_install_button.setEnabled(True)
        self.ai_browse_button.setEnabled(True)
        self.ai_cancel_button.setEnabled(False)
        self.ai_status_label.setText(message)
        if success:
            self.context.events.settings_changed.emit()
        self._refresh_ai_status(keep_message=not success)

    def _start_local_ai(self) -> None:
        if self.local_ai.start():
            self.ai_status_label.setText("本地 AI 正在启动，请稍候…")
            self.context.events.settings_changed.emit()
        else:
            self.ai_status_label.setText("请先点击“一键安装本地 AI”")

    def _refresh_ai_status(self, keep_message: bool = False) -> None:
        installed = self.local_ai.is_installed()
        running = self.local_ai.is_running()
        self.ai_start_button.setEnabled(installed and not running)
        self.ai_install_button.setText("重新检查/继续安装" if installed else "一键安装本地 AI")
        if not keep_message:
            if running:
                self.ai_status_label.setText("已安装并正在运行，可直接在 AI 助手页面使用")
            elif installed:
                self.ai_status_label.setText("已安装，点击“启动本地 AI”即可使用")
            else:
                self.ai_status_label.setText(
                    "尚未安装。需要约 5GB 空间，模型从国内魔搭社区下载。"
                )

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