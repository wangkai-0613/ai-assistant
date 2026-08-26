from datetime import datetime, timedelta

from app.core.contracts import TaskDraft
from app.core.events import AppEvents
from app.features.task_course.task_service import SNOOZE_MINUTES, TaskService


def _draft(minutes: int = 60, title: str = "写周报") -> TaskDraft:
    return TaskDraft(title=title, due_at=datetime.now() + timedelta(minutes=minutes))


def test_create_persists_and_emits_event(tmp_path) -> None:
    events = AppEvents()
    received: list = []
    events.task_created.connect(received.append)
    service = TaskService(db_path=tmp_path / "db.sqlite", events=events)

    task = service.create(_draft())

    assert task.title == "写周报"
    assert not task.completed
    assert [t.id for t in service.list_all()] == [task.id]
    assert [t.id for t in received] == [task.id]


def test_create_survives_reconnect(tmp_path) -> None:
    db_path = tmp_path / "db.sqlite"
    TaskService(db_path=db_path).create(_draft())

    reopened = TaskService(db_path=db_path)
    assert len(reopened.list_all()) == 1


def test_list_all_sorted_by_due_at(tmp_path) -> None:
    service = TaskService(db_path=tmp_path / "db.sqlite")
    late = service.create(_draft(minutes=120, title="晚任务"))
    early = service.create(_draft(minutes=10, title="早任务"))

    assert [t.id for t in service.list_all()] == [early.id, late.id]


def test_complete_and_delete(tmp_path) -> None:
    service = TaskService(db_path=tmp_path / "db.sqlite")
    task = service.create(_draft())

    service.complete(task.id)
    assert service.list_all()[0].completed is True

    service.delete(task.id)
    assert service.list_all() == []


def test_update_changes_fields(tmp_path) -> None:
    service = TaskService(db_path=tmp_path / "db.sqlite")
    task = service.create(_draft())

    new_due = datetime.now() + timedelta(days=2)
    updated = service.update(task.id, TaskDraft(title="改标题", due_at=new_due, category="学习"))

    assert updated is not None
    assert updated.title == "改标题"
    assert updated.category == "学习"
    assert abs((updated.due_at - new_due).total_seconds()) < 1


def test_due_pending_filters_uncompleted_overdue(tmp_path) -> None:
    service = TaskService(db_path=tmp_path / "db.sqlite")
    overdue = service.create(_draft(minutes=-10, title="已到期"))
    future = service.create(_draft(minutes=60, title="未到期"))
    done = service.create(_draft(minutes=-5, title="已完成"))
    service.complete(done.id)

    now = datetime.now()
    pending = service.due_pending(now)
    assert [t.id for t in pending] == [overdue.id]
    assert future.id not in [t.id for t in pending]


def test_snooze_moves_due_at_forward(tmp_path) -> None:
    service = TaskService(db_path=tmp_path / "db.sqlite")
    task = service.create(_draft(minutes=-10))
    now = datetime.now()

    service.snooze(task.id, now=now)

    updated = service.list_all()[0]
    expected = now + timedelta(minutes=SNOOZE_MINUTES)
    assert abs((updated.due_at - expected).total_seconds()) < 1
    assert service.due_pending(now) == []
