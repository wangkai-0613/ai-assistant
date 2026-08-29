import os
from datetime import date, datetime, timedelta

import pytest
from PySide6.QtWidgets import QApplication, QLabel, QScrollArea

from app.application import build_context, build_window, shutdown
from app.core.contracts import (
    SystemSummary,
    Task,
    TaskDraft,
    WeatherForecastDay,
    WeatherSummary,
)


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
    weather_page = window.pages.widget(4)
    forecast_days = [
        WeatherForecastDay(
            date=date.today() + timedelta(days=offset),
            description="有雨" if offset == 2 else "晴",
            temperature_max_c=28 + offset,
            temperature_min_c=18 + offset,
            rain_probability=80 if offset == 2 else 10,
        )
        for offset in range(7)
    ]
    weather_page._render_forecast("武汉", forecast_days)
    assert len(weather_page.forecast_cards) == 7
    assert weather_page.weather_label.text() == "武汉 · 未来 7 天"
    assert weather_page.forecast_cards[2].findChild(
        QLabel, "forecastWeather"
    ).text() == "有雨"

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
    ai_page = window.pages.widget(3)
    ai_bubbles = ai_page.findChildren(QLabel, "aiMessageBubble")
    ai_avatars = ai_page.findChildren(QLabel, "aiAvatar")
    assert len(ai_bubbles) == 1
    assert len(ai_avatars) == 1
    assert ai_avatars[0].pixmap().isNull() is False

    ai_page._append_history("我", "右侧用户消息")
    user_bubbles = ai_page.findChildren(QLabel, "userMessageBubble")
    assert len(user_bubbles) == 1
    user_row_layout = user_bubbles[0].parentWidget().layout()
    assert user_row_layout.itemAt(0).spacerItem() is not None

    assert window.desktop_pet.popup is not None
    assert window.windowIcon().isNull() is False
    assert window.brand_icon.pixmap().isNull() is False
    assert window.desktop_pet._mascot_pixmap.isNull() is False
    assert window._tray_icon.icon().isNull() is False
    home_page = window.pages.widget(0)
    assert not hasattr(home_page, "_cat_label")

    window.desktop_pet.show()
    integration_qapp.processEvents()
    available = window.desktop_pet.screen().availableGeometry()
    margin = 24
    assert window.desktop_pet.x() == (
        available.x() + available.width() - window.desktop_pet.width() - margin
    )
    assert window.desktop_pet.y() == (
        available.y() + available.height() - window.desktop_pet.height() - margin
    )

    reminder_task = Task(
        id="reminder-test",
        title="悬浮提醒测试",
        due_at=datetime.now() + timedelta(minutes=30),
    )
    context.events.task_reminder.emit(reminder_task, "early")
    integration_qapp.processEvents()
    reminder_popup = window.desktop_pet.reminder_popup
    assert reminder_popup.isVisible()
    assert "悬浮提醒测试" in reminder_popup.message_label.text()
    assert "30 分钟" in reminder_popup.message_label.text()
    assert reminder_popup.y() < window.desktop_pet.y()
    assert "background-color: #ffffff" in reminder_popup.styleSheet()
    assert "color: #000000" in reminder_popup.styleSheet()

    context.events.daily_summary.emit(
        """明日提醒
明天没有课程安排
大概率有雨，记得带伞"""
    )
    integration_qapp.processEvents()
    assert "明日提醒" in reminder_popup.message_label.text()
    assert "记得带伞" in reminder_popup.message_label.text()
    assert "#0d1117" in window.styleSheet()
    context.get_service("settings").set("theme", "light")
    context.events.settings_changed.emit()
    assert "#f7faff" in window.styleSheet()
    assert "#f7faff" in window.desktop_pet.popup.styleSheet()
    context.get_service("settings").set("theme", "dark")
    context.events.settings_changed.emit()

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
    window.desktop_pet.reminder_popup.close()
    window.desktop_pet.close()
    window._tray_icon.hide()
    window.close()
