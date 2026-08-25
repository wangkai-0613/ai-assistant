"""3号模块独立演示：天气、系统状态与设置。

用法：
    python -m app.features.weather_system.demo                # 打开演示窗口
    python -m app.features.weather_system.demo --set-city 北京 # 设置城市后打开窗口
"""

import asyncio
import sys

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QApplication,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.core.app_context import AppContext
from app.core.contracts import WeatherSummary
from app.core.events import AppEvents
from app.features.weather_system.weather_service import WeatherError


class WeatherFetcher(QThread):
    """在后台线程查询天气，避免阻塞 UI。"""

    done = Signal(object)
    failed = Signal(str)

    def __init__(self, city: str) -> None:
        super().__init__()
        self.city = city

    def run(self) -> None:
        from app.features.weather_system.weather_service import WeatherService

        try:
            summary = asyncio.run(WeatherService().fetch(self.city))
            self.done.emit(summary)
        except WeatherError as exc:
            self.failed.emit(str(exc))


def parse_args(argv: list[str]) -> str | None:
    city: str | None = None
    for index, arg in enumerate(argv):
        if arg == "--set-city" and index + 1 < len(argv):
            city = argv[index + 1]
    return city


def main() -> int:
    argv = sys.argv[1:]
    app = QApplication.instance() or QApplication(sys.argv)

    context = AppContext(events=AppEvents())
    from app.features.weather_system.services import create_services

    services = create_services(context)
    settings = services["settings"]

    city = parse_args(argv)
    if city:
        settings.set("city", city)

    window = QWidget()
    window.resize(720, 480)
    layout = QVBoxLayout(window)
    layout.setContentsMargins(32, 32, 32, 32)

    heading = QLabel("天气、系统状态与设置")
    heading.setObjectName("pageTitle")

    city_input = QLineEdit()
    city_input.setPlaceholderText("输入城市名，如：武汉")
    city_input.setText(settings.get("city", ""))

    query_button = QPushButton("查询天气")
    weather_label = QLabel("尚未查询")
    weather_label.setObjectName("mutedText")
    weather_label.setWordWrap(True)

    refresh_button = QPushButton("刷新系统状态")
    system_label = QLabel("尚未读取")
    system_label.setObjectName("mutedText")
    system_label.setWordWrap(True)

    layout.addWidget(heading)
    layout.addWidget(city_input)
    layout.addWidget(query_button)
    layout.addWidget(weather_label)
    layout.addWidget(refresh_button)
    layout.addWidget(system_label)
    layout.addStretch(1)
    layout.setAlignment(Qt.AlignmentFlag.AlignTop)

    def on_refresh_clicked() -> None:
        summary = services["system"].snapshot()
        cpu = f"CPU {summary.cpu_percent}%" if summary.cpu_percent is not None else "CPU 未启用"
        system_label.setText(f"内存 {summary.memory_percent}%\n磁盘 {summary.disk_percent}%\n{cpu}")

    refresh_button.clicked.connect(on_refresh_clicked)

    window._weather_fetchers: list[WeatherFetcher] = []

    def on_query_clicked() -> None:
        city_name = city_input.text().strip()
        if not city_name:
            weather_label.setText("请输入城市名")
            return
        settings.set("city", city_name)
        weather_label.setText("正在查询天气…")
        query_button.setEnabled(False)
        fetcher = WeatherFetcher(city_name)
        window._weather_fetchers.append(fetcher)

        def cleanup() -> None:
            if fetcher in window._weather_fetchers:
                window._weather_fetchers.remove(fetcher)

        def on_done(summary: WeatherSummary) -> None:
            rain = f"降雨概率 {summary.rain_probability}%" if summary.rain_probability is not None else "无降雨数据"
            weather_label.setText(
                f"{summary.city} {summary.temperature_c}°C\n{summary.description}\n{rain}"
            )
            query_button.setEnabled(True)
            cleanup()

        def on_failed(message: str) -> None:
            weather_label.setText(f"查询失败：{message}")
            query_button.setEnabled(True)
            cleanup()

        fetcher.done.connect(on_done)
        fetcher.failed.connect(on_failed)
        fetcher.start()

    query_button.clicked.connect(on_query_clicked)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())