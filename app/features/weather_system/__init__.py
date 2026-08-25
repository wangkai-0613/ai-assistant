"""3号：天气、系统状态和设置。"""

from app.features.weather_system.pages import (
    create_settings_page,
    create_system_page,
    create_weather_page,
)
from app.features.weather_system.services import create_services

__all__ = [
    "create_services",
    "create_settings_page",
    "create_system_page",
    "create_weather_page",
]