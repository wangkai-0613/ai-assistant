import os
from datetime import datetime

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtWidgets import QApplication

from app.core.app_context import AppContext
from app.core.contracts import TaskDraft
from app.core.events import AppEvents
from app.features.task_course.course_service import CourseService
from app.features.task_course.reminder_service import ReminderService
from app.features.task_course.task_service import TaskService

# 2026-08-26 是周三
WEDNESDAY = 3
COURSE_CSV = "weekday,start_time,end_time,name,room\n3,10:00,11:40,高等数学,N101\n"


class _FakeSettings:
    def __init__(self, voice_enabled: bool) -> None:
        self._voice_enabled = voice_enabled

    def get(self, key: str, default=None):
        if key == "voice_enabled":
            return self._voice_enabled
        return default


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


def _build_context(tmp_path, voice_enabled: bool = False) -> AppContext:
    context = AppContext(events=AppEvents())
    context.register_service(
        "task",
        TaskService(db_path=tmp_path / "db.sqlite", events=context.events),
    )
    course_service = CourseService(db_path=tmp_path / "db.sqlite")
    csv_path = tmp_path / "courses.csv"
    csv_path.write_text(COURSE_CSV, encoding="utf-8")
    course_service.import_csv(str(csv_path))
    context.register_service("course", course_service)
    context.register_service("settings", _FakeSettings(voice_enabled))
    return context


def test_course_alert_within_lead_window(tmp_path) -> None:
    context = _build_context(tmp_path)
    reminder = ReminderService(context, clock=lambda: datetime(2026, 8, 26, 9, 50))

    alerts = reminder.collect_course_alerts(datetime(2026, 8, 26, 9, 50))

    assert len(alerts) == 1
    assert alerts[0].course.name == "高等数学"
    assert alerts[0].start_at == datetime(2026, 8, 26, 10, 0)


def test_course_alert_not_repeated(tmp_path) -> None:
    context = _build_context(tmp_path)
    reminder = ReminderService(context, clock=lambda: datetime(2026, 8, 26, 9, 50))

    reminder.collect_course_alerts(datetime(2026, 8, 26, 9, 50))
    assert reminder.collect_course_alerts(datetime(2026, 8, 26, 9, 52)) == []


def test_course_alert_outside_lead_window(tmp_path) -> None:
    context = _build_context(tmp_path)
    reminder = ReminderService(context)

    # 距开课还有 60 分钟，超出 15 分钟提前量
    assert reminder.collect_course_alerts(datetime(2026, 8, 26, 9, 0)) == []
    # 课程已经开始
    assert reminder.collect_course_alerts(datetime(2026, 8, 26, 10, 5)) == []


def test_course_alert_other_weekday(tmp_path) -> None:
    context = _build_context(tmp_path)
    reminder = ReminderService(context)

    # 2026-08-27 是周四
    assert reminder.collect_course_alerts(datetime(2026, 8, 27, 9, 50)) == []


def test_tick_without_alerts_is_silent(tmp_path) -> None:
    context = _build_context(tmp_path)
    reminder = ReminderService(context, clock=lambda: datetime(2026, 8, 26, 9, 0))

    reminder.tick()

    assert reminder._open_dialogs == []


def test_tick_opens_dialog_and_close_snoozes(qapp, tmp_path) -> None:
    context = _build_context(tmp_path)
    now = datetime(2026, 8, 26, 9, 0)
    task_service = context.get_service("task")
    task_service.create(TaskDraft(title="到期任务", due_at=datetime(2026, 8, 26, 8, 59)))
    reminder = ReminderService(context, clock=lambda: now)

    reminder.tick()

    assert len(reminder._open_dialogs) == 1
    assert task_service.due_pending(now) != []

    dialog = reminder._open_dialogs[0]
    dialog.close()
    qapp.processEvents()

    # 直接关窗等同"稍后提醒"，任务不再处于到期状态
    assert task_service.due_pending(now) == []


def test_tick_course_dialog_shows_once(qapp, tmp_path) -> None:
    context = _build_context(tmp_path)
    reminder = ReminderService(context, clock=lambda: datetime(2026, 8, 26, 9, 50))

    reminder.tick()

    assert len(reminder._open_dialogs) == 1
    dialog = reminder._open_dialogs[0]
    assert "高等数学" in dialog.windowTitle()
