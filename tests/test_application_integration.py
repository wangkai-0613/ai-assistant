import os

import pytest
from PySide6.QtWidgets import QApplication

from app.application import build_context, build_window, shutdown


@pytest.fixture(scope="module")
def integration_qapp():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    app = QApplication.instance() or QApplication([])
    yield app


def test_main_application_registers_services_and_real_pages(
    integration_qapp, monkeypatch, tmp_path
) -> None:
    monkeypatch.setattr(
        "app.features.task_course.database.default_db_path",
        lambda: tmp_path / "assistant.db",
    )
    monkeypatch.setattr(
        "app.features.weather_system.settings_service.default_config_path",
        lambda: tmp_path / "settings.json",
    )
    monkeypatch.setattr(
        "app.features.weather_system.weather_service._cache_path",
        lambda: tmp_path / "weather.json",
    )

    context = build_context()
    context.get_service("settings").set("openrouter_key", "test-key")
    window = build_window(context)

    assert set(context.services) == {
        "autostart",
        "course",
        "local_ai",
        "reminder",
        "settings",
        "system",
        "task",
        "weather",
    }
    assert window.pages.count() == 7
    assert window.desktop_pet.popup is not None
    assert window.pages.widget(3).service.config.openrouter_api_key == "test-key"
    assert all(
        "PlaceholderPage" not in type(window.pages.widget(index)).__name__
        for index in range(7)
    )

    shutdown(context)
    window.desktop_pet.close()
    window._tray_icon.hide()
    window.close()
