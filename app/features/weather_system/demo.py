"""3号模块独立演示：天气、系统状态与设置。

用法：
    python -m app.features.weather_system.demo                # 打开演示窗口
    python -m app.features.weather_system.demo --set-city 北京 # 设置城市后打开窗口
"""

import sys

from PySide6.QtWidgets import QApplication, QTabWidget

from app.core.app_context import AppContext
from app.core.events import AppEvents
from app.features.weather_system.pages import (
    create_settings_page,
    create_system_page,
    create_weather_page,
)
from app.features.weather_system.services import create_services


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
    services = create_services(context)

    city = parse_args(argv)
    if city:
        services["settings"].set("city", city)

    window = QTabWidget()
    window.setWindowTitle("天气、系统状态与设置（3号独立演示）")
    window.resize(720, 480)
    window.addTab(create_weather_page(context), "天气")
    window.addTab(create_system_page(context), "系统状态")
    window.addTab(create_settings_page(context), "设置")
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())