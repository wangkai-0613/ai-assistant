"""3号模块：后台线程任务。"""

from __future__ import annotations

import asyncio

from PySide6.QtCore import QThread, Signal

from app.core.contracts import WeatherSummary
from app.features.weather_system.weather_service import WeatherError, WeatherService


class WeatherFetcher(QThread):
    """在后台线程查询天气，避免阻塞 UI。"""

    done = Signal(object)
    failed = Signal(str)

    def __init__(self, city: str, service: WeatherService | None = None) -> None:
        super().__init__()
        self.city = city
        self.service = service or WeatherService()

    def run(self) -> None:
        try:
            summary: WeatherSummary = asyncio.run(self.service.fetch(self.city))
            self.done.emit(summary)
        except WeatherError as exc:
            self.failed.emit(str(exc))