"""3号模块：后台线程任务。"""

from __future__ import annotations

import asyncio

from PySide6.QtCore import QThread, Signal

from app.core.contracts import WeatherSummary
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
            summary: WeatherSummary = asyncio.run(WeatherService().fetch(self.city))
            self.done.emit(summary)
        except WeatherError as exc:
            self.failed.emit(str(exc))