from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass(frozen=True, slots=True)
class Task:
    id: str
    title: str
    due_at: datetime
    completed: bool = False
    category: str = "任务"


@dataclass(frozen=True, slots=True)
class TaskDraft:
    title: str
    due_at: datetime
    category: str = "任务"
    confidence: float = 1.0


@dataclass(frozen=True, slots=True)
class Course:
    id: str
    name: str
    weekday: int
    start_time: str
    end_time: str = ""
    room: str = ""

    def __post_init__(self) -> None:
        if not 1 <= self.weekday <= 7:
            raise ValueError("weekday 必须在 1 到 7 之间")


@dataclass(frozen=True, slots=True)
class WeatherSummary:
    city: str
    temperature_c: float
    description: str
    rain_probability: int | None = None


@dataclass(frozen=True, slots=True)
class SystemSummary:
    memory_percent: float
    disk_percent: float
    cpu_percent: float | None = None


class TaskServiceProtocol(Protocol):
    def create(self, draft: TaskDraft) -> Task: ...

    def list_all(self) -> list[Task]: ...

    def complete(self, task_id: str) -> None: ...

    def delete(self, task_id: str) -> None: ...


class CourseServiceProtocol(Protocol):
    def import_csv(self, path: str) -> int: ...

    def list_week(self) -> list[Course]: ...

    def list_tomorrow(self) -> list[Course]: ...

