import os
from datetime import date, datetime, timedelta

import pytest
from PySide6.QtWidgets import QApplication, QScrollArea

from app.application import build_context, build_window, shutdown
from app.core.contracts import SystemSummary, TaskDraft, WeatherSummary


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
    course_page = window.pages.widget(2)
    scroll = course_page.findChild(QScrollArea)
    assert scroll is not None and scroll.widgetResizable() is True
    week_start = date.today() - timedelta(days=date.today().weekday())
    next_week_start = week_start + timedelta(days=7)
    assert course_page.week_range_label.text().startswith(week_start.isoformat())
    assert course_page.next_week_range_label.text().startswith(next_week_start.isoformat())
    assert week_start.strftime("%m-%d") in course_page.grid.itemAtPosition(0, 0).widget().text()
    assert next_week_start.strftime("%m-%d") in (
        course_page.next_week_grid.itemAtPosition(0, 0).widget().text()
    )
    assert window.desktop_pet.popup is not None

    home_page = window.pages.widget(0)
    assert home_page._value_labels["待办任务"].text() == "0 项待完成"
    context.get_service("task").create(
        TaskDraft(title="同步测试", due_at=datetime.now() + timedelta(hours=1))
    )
    assert home_page._value_labels["待办任务"].text() == "1 项待完成"

    today = date.today()
    csv_path = tmp_path / "today.csv"
    csv_path.write_text(
        "weekday,start_time,end_time,name,room\n"
        f"{today.isoweekday()},08:00,09:40,同步课程,N101\n",
        encoding="utf-8",
    )
    context.get_service("course").import_csv(str(csv_path))
    context.get_service("weather").get_cached = lambda _city: WeatherSummary(
        city="武汉", temperature_c=26, description="晴"
    )
    context.get_service("system").snapshot = lambda: SystemSummary(
        memory_percent=45, disk_percent=30, cpu_percent=12
    )
    window.navigation.setCurrentRow(2)
    window.navigation.setCurrentRow(0)
    assert home_page._value_labels["今日课程"].text() == "1 节课"
    assert home_page._value_labels["今日天气"].text() == "晴 26°C"
    assert home_page._value_labels["系统状态"].text() == "CPU 12% · 内存 45%"
    assert window.pages.widget(3).service.config.openrouter_api_key == "test-key"
    assert all(
        "PlaceholderPage" not in type(window.pages.widget(index)).__name__
        for index in range(7)
    )

    shutdown(context)
    window.desktop_pet.close()
    window._tray_icon.hide()
    window.close()
