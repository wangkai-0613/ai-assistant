import json

import pytest

from app.features.weather_system.settings_service import SettingsService


def test_defaults_when_file_missing(tmp_path) -> None:
    service = SettingsService(path=tmp_path / "missing.json")
    assert service.get("city") == "武汉"
    assert service.get("voice_enabled") is True
    assert service.get("theme") == "dark"


def test_set_and_reload(tmp_path) -> None:
    path = tmp_path / "settings.json"
    service = SettingsService(path=path)
    service.set("city", "上海")
    service.set("voice_enabled", False)
    service.set("theme", "light")

    reloaded = SettingsService(path=path)
    assert reloaded.get("city") == "上海"
    assert reloaded.get("voice_enabled") is False
    assert reloaded.get("theme") == "light"


def test_save_writes_json_file(tmp_path) -> None:
    path = tmp_path / "settings.json"
    service = SettingsService(path=path)
    service.set("city", "广州")

    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["city"] == "广州"


def test_unknown_key_raises(tmp_path) -> None:
    service = SettingsService(path=tmp_path / "settings.json")
    with pytest.raises(KeyError):
        service.set("not_a_setting", 1)


def test_corrupted_file_falls_back_to_defaults(tmp_path) -> None:
    path = tmp_path / "settings.json"
    path.write_text("{ broken json", encoding="utf-8")
    service = SettingsService(path=path)
    assert service.get("city") == "武汉"


def test_load_ignores_unknown_keys_from_file(tmp_path) -> None:
    path = tmp_path / "settings.json"
    path.write_text(json.dumps({"city": "深圳", "evil_key": "x"}), encoding="utf-8")
    service = SettingsService(path=path)
    assert service.get("city") == "深圳"
    assert "evil_key" not in service._data