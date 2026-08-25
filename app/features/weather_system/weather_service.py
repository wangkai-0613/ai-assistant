"""3号模块：天气查询服务。

使用免费的 wttr.in 接口，按城市名查询天气，返回公共 WeatherSummary。
- 带 TTL 缓存：短时间内重复查询直接返回缓存，不重复请求。
- 断网回退：网络失败时如有缓存则返回缓存，否则抛出 WeatherError。
- 缓存持久化到用户目录，重启后可读取最近一次结果。
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import httpx

from app.core.contracts import WeatherSummary

WTTR_URL = "https://wttr.in/{city}?format=j1"
TIMEOUT_SECONDS = 10.0
CACHE_TTL_SECONDS = 1800  # 30 分钟
_CACHE_FILENAME = "weather_cache.json"


class WeatherError(Exception):
    """天气查询失败。"""


def _cache_path() -> Path:
    path = Path.home() / ".xiao_assistant"
    path.mkdir(parents=True, exist_ok=True)
    return path / _CACHE_FILENAME


class WeatherService:
    def __init__(self, cache_path: Path | None = None) -> None:
        self._cache_path = cache_path or _cache_path()
        self._cache: dict[str, dict[str, Any]] = {}
        self._load_cache()

    def _load_cache(self) -> None:
        if not self._cache_path.exists():
            return
        try:
            data = json.loads(self._cache_path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                self._cache = data
        except (json.JSONDecodeError, OSError):
            pass

    def _save_cache(self) -> None:
        try:
            self._cache_path.write_text(
                json.dumps(self._cache, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except OSError:
            pass

    def _cached_summary(self, city: str) -> WeatherSummary | None:
        entry = self._cache.get(city)
        if not entry:
            return None
        age = time.time() - entry.get("fetched_at", 0)
        if age > CACHE_TTL_SECONDS:
            return None
        try:
            return WeatherSummary(
                city=entry["city"],
                temperature_c=float(entry["temperature_c"]),
                description=entry["description"],
                rain_probability=entry.get("rain_probability"),
            )
        except (KeyError, TypeError, ValueError):
            return None

    def _any_cached(self, city: str) -> WeatherSummary | None:
        entry = self._cache.get(city)
        if not entry:
            return None
        try:
            return WeatherSummary(
                city=entry["city"],
                temperature_c=float(entry["temperature_c"]),
                description=entry["description"],
                rain_probability=entry.get("rain_probability"),
            )
        except (KeyError, TypeError, ValueError):
            return None

    def get_cached(self, city: str) -> WeatherSummary | None:
        """读取缓存（不校验时效），供断网或展示上次结果使用。"""
        return self._any_cached(city)

    async def fetch(self, city: str) -> WeatherSummary:
        cached = self._cached_summary(city)
        if cached is not None:
            return cached

        url = WTTR_URL.format(city=city)
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPError as exc:
            stale = self._any_cached(city)
            if stale is not None:
                return stale
            raise WeatherError(f"无法连接天气服务：{exc}") from exc
        except ValueError as exc:
            raise WeatherError("天气服务返回了无法解析的数据") from exc

        try:
            current = data["current_condition"][0]
            today = data["weather"][0]
            rain_hours = [int(item.get("chanceofrain", 0)) for item in today.get("hourly", [])]
            rain = max(rain_hours) if rain_hours else None
            city_name = data["nearest_area"][0]["areaName"][0]["value"]
            summary = WeatherSummary(
                city=city_name,
                temperature_c=float(current["temp_C"]),
                description=current["weatherDesc"][0]["value"],
                rain_probability=rain,
            )
        except (KeyError, IndexError, ValueError) as exc:
            raise WeatherError("天气服务返回的数据缺少必要字段") from exc

        self._cache[city] = {
            "city": summary.city,
            "temperature_c": summary.temperature_c,
            "description": summary.description,
            "rain_probability": summary.rain_probability,
            "fetched_at": time.time(),
        }
        self._save_cache()
        return summary