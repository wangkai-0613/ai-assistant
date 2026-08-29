import asyncio
import json
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.contracts import WeatherSummary
from app.features.weather_system.weather_service import (
    WeatherError,
    WeatherService,
)


def _wttr_payload() -> dict:
    return {
        "current_condition": [{"temp_C": "25", "weatherDesc": [{"value": "Sunny"}]}],
        "weather": [
            {"hourly": [{"chanceofrain": "10"}, {"chanceofrain": "60"}]},
            {
                "avgtempC": "21",
                "hourly": [
                    {
                        "chanceofrain": "20",
                        "weatherDesc": [{"value": "Cloudy"}],
                    },
                    {
                        "chanceofrain": "80",
                        "weatherDesc": [{"value": "Rain"}],
                    },
                ],
            },
        ],
        "nearest_area": [{"areaName": [{"value": "Beijing"}]}],
    }


def _open_meteo_daily_payload() -> dict:
    return {
        "daily": {
            "time": [f"2026-09-{day:02d}" for day in range(1, 8)],
            "weather_code": [0, 1, 3, 61, 80, 95, 2],
            "temperature_2m_max": [30, 29, 28, 27, 26, 25, 29],
            "temperature_2m_min": [20, 20, 19, 18, 18, 17, 19],
            "precipitation_probability_max": [0, 10, 20, 70, 80, 90, 15],
        }
    }


def _summary() -> dict:
    return {
        "city": "Beijing",
        "temperature_c": 25,
        "description": "Sunny",
        "rain_probability": 60,
        "fetched_at": time.time(),
    }


def _cached_service(tmp_path, entry: dict) -> WeatherService:
    cache_path = tmp_path / "cache.json"
    cache_path.write_text(json.dumps({"Beijing": entry}), encoding="utf-8")
    return WeatherService(cache_path=cache_path)


def _fake_response(payload: dict) -> MagicMock:
    response = MagicMock()
    response.json.return_value = payload
    return response


@patch("app.features.weather_system.weather_service.httpx.AsyncClient")
def test_fetch_parses_and_caches(mock_client, tmp_path) -> None:
    mock_client.return_value.__aenter__.return_value.get = AsyncMock(
        return_value=_fake_response(_wttr_payload())
    )
    service = WeatherService(cache_path=tmp_path / "cache.json")

    summary = asyncio.run(service.fetch("Beijing"))

    assert isinstance(summary, WeatherSummary)
    assert summary.city == "Beijing"
    assert summary.temperature_c == 25.0
    assert summary.description == "Sunny"
    assert summary.rain_probability == 60
    assert (tmp_path / "cache.json").exists()


@patch("app.features.weather_system.weather_service.httpx.AsyncClient")
def test_fetch_weekly_returns_seven_days(mock_client, tmp_path) -> None:
    geo_response = _fake_response(
        {"results": [{"name": "武汉", "latitude": 30.59, "longitude": 114.3}]}
    )
    forecast_response = _fake_response(_open_meteo_daily_payload())
    mock_client.return_value.__aenter__.return_value.get = AsyncMock(
        side_effect=[geo_response, forecast_response]
    )
    service = WeatherService(cache_path=tmp_path / "cache.json")

    city, days = asyncio.run(service.fetch_weekly("武汉"))

    assert city == "武汉"
    assert len(days) == 7
    assert days[0].description == "晴"
    assert days[3].description == "有雨"
    assert days[3].rain_probability == 70
    assert service.get_weekly_cached("武汉") == (city, days)


@patch("app.features.weather_system.weather_service.httpx.AsyncClient")
def test_fetch_tomorrow_uses_second_forecast_day(mock_client, tmp_path) -> None:
    mock_client.return_value.__aenter__.return_value.get = AsyncMock(
        return_value=_fake_response(_wttr_payload())
    )
    service = WeatherService(cache_path=tmp_path / "cache.json")

    summary = asyncio.run(service.fetch_tomorrow("Beijing"))

    assert summary.temperature_c == 21.0
    assert summary.description == "Rain"
    assert summary.rain_probability == 80
    assert service.get_tomorrow_cached("Beijing") == summary


@patch("app.features.weather_system.weather_service.httpx.AsyncClient")
def test_fetch_returns_fresh_cache_without_network(mock_client, tmp_path) -> None:
    service = _cached_service(tmp_path, _summary())
    summary = asyncio.run(service.fetch("Beijing"))

    assert summary.temperature_c == 25.0
    mock_client.assert_not_called()


@patch("app.features.weather_system.weather_service.httpx.AsyncClient")
def test_fetch_falls_back_to_stale_cache_on_network_error(mock_client, tmp_path) -> None:
    entry = _summary()
    entry["fetched_at"] = time.time() - 99999
    service = _cached_service(tmp_path, entry)
    mock_client.return_value.__aenter__.return_value.get = AsyncMock(
        side_effect=__import__("httpx").ConnectError("no network")
    )

    summary = asyncio.run(service.fetch("Beijing"))
    assert summary.temperature_c == 25.0


@patch("app.features.weather_system.weather_service.httpx.AsyncClient")
def test_fetch_raises_when_no_cache_and_network_fails(mock_client, tmp_path) -> None:
    service = WeatherService(cache_path=tmp_path / "cache.json")
    mock_client.return_value.__aenter__.return_value.get = AsyncMock(
        side_effect=__import__("httpx").ConnectError("no network")
    )

    with pytest.raises(WeatherError):
        asyncio.run(service.fetch("Beijing"))


@patch("app.features.weather_system.weather_service.httpx.AsyncClient")
def test_fetch_raises_on_bad_payload(mock_client, tmp_path) -> None:
    service = WeatherService(cache_path=tmp_path / "cache.json")
    mock_client.return_value.__aenter__.return_value.get = AsyncMock(
        return_value=_fake_response({"unexpected": "shape"})
    )

    with pytest.raises(WeatherError):
        asyncio.run(service.fetch("Beijing"))


def test_get_cached_returns_any_entry_regardless_of_age(tmp_path) -> None:
    entry = _summary()
    entry["fetched_at"] = time.time() - 99999
    service = _cached_service(tmp_path, entry)

    cached = service.get_cached("Beijing")
    assert cached is not None
    assert cached.temperature_c == 25.0