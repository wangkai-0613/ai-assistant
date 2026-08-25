"""3号模块：服务注册入口。

组长会在主程序中调用 create_services(context) 完成接线。
"""

from __future__ import annotations

from app.core.app_context import AppContext
from app.features.weather_system.autostart import AutoStartService
from app.features.weather_system.settings_service import SettingsService
from app.features.weather_system.system_service import SystemService
from app.features.weather_system.weather_service import WeatherService


def create_services(context: AppContext) -> dict[str, object]:
    settings = SettingsService()
    context.register_service("settings", settings)
    weather = WeatherService()
    context.register_service("weather", weather)
    system = SystemService()
    context.register_service("system", system)
    autostart = AutoStartService()
    context.register_service("autostart", autostart)
    return {
        "settings": settings,
        "weather": weather,
        "system": system,
        "autostart": autostart,
    }