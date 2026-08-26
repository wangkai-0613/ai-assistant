"""1号模块：任务服务（SQLite 增删改查）。

统一使用公共契约 Task / TaskDraft，保存成功后发出
context.events.task_created 事件，供其他模块订阅。
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from pathlib import Path

from app.core.contracts import Task, TaskDraft
from app.features.task_course import database

SNOOZE_MINUTES = 5


def _format(moment: datetime) -> str:
    return moment.strftime("%Y-%m-%d %H:%M:%S")


def _parse(raw: str) -> datetime:
    return datetime.strptime(raw, "%Y-%m-%d %H:%M:%S")


class TaskService:
    def __init__(self, db_path: Path | None = None, events=None) -> None:
        self._conn = database.connect(db_path)
        self._events = events

    # ---- 查 ----

    def list_all(self) -> list[Task]:
        rows = self._conn.execute(
            "SELECT id, title, due_at, completed, category FROM tasks"
            " ORDER BY due_at, id"
        ).fetchall()
        return [self._to_task(row) for row in rows]

    def due_pending(self, now: datetime) -> list[Task]:
        """返回所有未完成且已到期的任务。"""
        rows = self._conn.execute(
            "SELECT id, title, due_at, completed, category FROM tasks"
            " WHERE completed = 0 AND due_at <= ? ORDER BY due_at",
            (_format(now),),
        ).fetchall()
        return [self._to_task(row) for row in rows]

    # ---- 增 ----

    def create(self, draft: TaskDraft) -> Task:
        task = Task(
            id=uuid.uuid4().hex,
            title=draft.title,
            due_at=draft.due_at,
            category=draft.category,
        )
        self._conn.execute(
            "INSERT INTO tasks (id, title, due_at, completed, category)"
            " VALUES (?, ?, ?, 0, ?)",
            (task.id, task.title, _format(task.due_at), task.category),
        )
        self._conn.commit()
        if self._events is not None:
            self._events.task_created.emit(task)
        return task

    # ---- 改 ----

    def update(self, task_id: str, draft: TaskDraft) -> Task | None:
        self._conn.execute(
            "UPDATE tasks SET title = ?, due_at = ?, category = ? WHERE id = ?",
            (draft.title, _format(draft.due_at), draft.category, task_id),
        )
        self._conn.commit()
        return self._find(task_id)

    def complete(self, task_id: str) -> None:
        self._conn.execute(
            "UPDATE tasks SET completed = 1 WHERE id = ?", (task_id,)
        )
        self._conn.commit()

    def snooze(self, task_id: str, minutes: int = SNOOZE_MINUTES, now: datetime | None = None) -> None:
        """稍后提醒：到期时间顺延到当前时刻之后。"""
        base = now or datetime.now()
        self._conn.execute(
            "UPDATE tasks SET due_at = ? WHERE id = ?",
            (_format(base + timedelta(minutes=minutes)), task_id),
        )
        self._conn.commit()

    # ---- 删 ----

    def delete(self, task_id: str) -> None:
        self._conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        self._conn.commit()

    # ---- 内部 ----

    def _find(self, task_id: str) -> Task | None:
        row = self._conn.execute(
            "SELECT id, title, due_at, completed, category FROM tasks WHERE id = ?",
            (task_id,),
        ).fetchone()
        return self._to_task(row) if row is not None else None

    @staticmethod
    def _to_task(row) -> Task:
        return Task(
            id=row["id"],
            title=row["title"],
            due_at=_parse(row["due_at"]),
            completed=bool(row["completed"]),
            category=row["category"],
        )
