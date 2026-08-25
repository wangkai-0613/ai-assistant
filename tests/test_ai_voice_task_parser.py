from datetime import datetime

from app.features.ai_voice.task_parser import (
    fallback_parse_task,
    looks_like_task_request,
)


def test_fallback_parse_task_extracts_title_and_time() -> None:
    now = datetime(2026, 8, 25, 10, 0)
    draft = fallback_parse_task("明天下午三点提醒我交报告", now)

    assert draft is not None
    assert draft.title == "交报告"
    assert draft.due_at == datetime(2026, 8, 26, 15, 0)
    assert draft.category == "任务"


def test_fallback_parse_task_handles_today_and_minutes() -> None:
    now = datetime(2026, 8, 25, 8, 0)
    draft = fallback_parse_task("今天晚上8点半记得开会", now)

    assert draft is not None
    assert draft.due_at == datetime(2026, 8, 25, 20, 30)
    assert draft.title == "开会"


def test_fallback_parse_task_returns_none_without_time() -> None:
    now = datetime(2026, 8, 25, 8, 0)
    assert fallback_parse_task("今天天气怎么样", now) is None


def test_looks_like_task_request() -> None:
    assert looks_like_task_request("提醒我交报告")
    assert not looks_like_task_request("今天天气怎么样")
