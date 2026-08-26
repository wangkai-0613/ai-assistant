"""1号模块：课表服务（CSV 导入与查询）。

CSV 格式与 sample_data/courses.csv 一致：
weekday, start_time, end_time, name, room（end_time / room 可缺省）。
坏行（字段缺失、星期越界、时间格式非法）自动跳过，不抛异常。
"""

from __future__ import annotations

import csv
import re
import uuid
from datetime import date, timedelta
from pathlib import Path

from app.core.contracts import Course
from app.features.task_course import database

_TIME_PATTERN = re.compile(r"^([01]?\d|2[0-3]):[0-5]\d$")
WEEKDAY_NAMES = ("周一", "周二", "周三", "周四", "周五", "周六", "周日")


class CourseService:
    def __init__(self, db_path: Path | None = None) -> None:
        self._conn = database.connect(db_path)

    def import_csv(self, path: str) -> int:
        """导入 CSV 课表（整体替换已有数据），返回成功导入条数。"""
        courses: list[Course] = []
        with open(path, newline="", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                course = self._parse_row(row)
                if course is not None:
                    courses.append(course)
        with self._conn:
            self._conn.execute("DELETE FROM courses")
            self._conn.executemany(
                "INSERT INTO courses (id, name, weekday, start_time, end_time, room)"
                " VALUES (?, ?, ?, ?, ?, ?)",
                [
                    (c.id, c.name, c.weekday, c.start_time, c.end_time, c.room)
                    for c in courses
                ],
            )
        return len(courses)

    def list_week(self) -> list[Course]:
        """全周课程，按星期和开始时间排序。"""
        rows = self._conn.execute(
            "SELECT id, name, weekday, start_time, end_time, room FROM courses"
            " ORDER BY weekday, start_time"
        ).fetchall()
        return [
            Course(
                id=row["id"],
                name=row["name"],
                weekday=row["weekday"],
                start_time=row["start_time"],
                end_time=row["end_time"],
                room=row["room"],
            )
            for row in rows
        ]

    def list_tomorrow(self, today: date | None = None) -> list[Course]:
        """明日课程，按开始时间排序。"""
        ref = (today or date.today()) + timedelta(days=1)
        return [c for c in self.list_week() if c.weekday == ref.isoweekday()]

    @staticmethod
    def _parse_row(row: dict) -> Course | None:
        try:
            weekday = int(str(row.get("weekday", "")).strip())
            start_time = str(row.get("start_time", "") or "").strip()
            name = str(row.get("name", "") or "").strip()
        except (TypeError, ValueError):
            return None
        if not 1 <= weekday <= 7 or not name or not _TIME_PATTERN.match(start_time):
            return None
        end_time = str(row.get("end_time", "") or "").strip()
        if end_time and not _TIME_PATTERN.match(end_time):
            end_time = ""
        room = str(row.get("room", "") or "").strip()
        return Course(
            id=uuid.uuid4().hex,
            name=name,
            weekday=weekday,
            start_time=start_time,
            end_time=end_time,
            room=room,
        )
