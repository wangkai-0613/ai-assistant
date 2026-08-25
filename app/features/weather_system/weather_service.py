"""3号模块：天气查询服务。

使用免费的 wttr.in 接口，按城市名查询天气，返回公共 WeatherSummary。
断网、超时或城市不存在时抛出 WeatherError，由调用方决定如何提示。
"""

from __future__ import annotations

import httpx

from app.core.contracts import WeatherSummary

WTTR_URL = "https://wttr.in/{city}?format=j1"
TIMEOUT_SECONDS = 10.0


class WeatherError(Exception):
    """天气查询失败。"""


class WeatherService:
    async def fetch(self, city: str) -> WeatherSummary:
        url = WTTR_URL.format(city=city)
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPError as exc:
            raise WeatherError(f"无法连接天气服务：{exc}") from exc
        except ValueError as exc:
            raise WeatherError("天气服务返回了无法解析的数据") from exc

        try:
            current = data["current_condition"][0]
            today = data["weather"][0]
            rain_hours = [int(item.get("chanceofrain", 0)) for item in today.get("hourly", [])]
            rain = max(rain_hours) if rain_hours else None
            city_name = data["nearest_area"][0]["areaName"][0]["value"]
            return WeatherSummary(
                city=city_name,
                temperature_c=float(current["temp_C"]),
                description=current["weatherDesc"][0]["value"],
                rain_probability=rain,
            )
        except (KeyError, IndexError, ValueError) as exc:
            raise WeatherError("天气服务返回的数据缺少必要字段") from exc