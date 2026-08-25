from datetime import datetime

import pytest

from app.core.contracts import Course, TaskDraft


def test_task_draft_keeps_datetime() -> None:
    due_at = datetime(2026, 8, 25, 15, 0)
    draft = TaskDraft(title="交报告", due_at=due_at)
    assert draft.due_at == due_at


def test_course_rejects_invalid_weekday() -> None:
    with pytest.raises(ValueError):
        Course(id="c1", name="高数", weekday=0, start_time="08:00")

