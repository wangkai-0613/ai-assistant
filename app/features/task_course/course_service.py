"""1号模块：课表服务（CSV/XLSX 导入与查询）。

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
from app.features.task_course.xlsx_import import parse_xlsx

_TIME_PATTERN = re.compile(r"^([01]?\d|2[0-3]):[0-5]\d$")
WEEKDAY_NAMES = ("周一", "周二", "周三", "周四", "周五", "周六", "周日")


class CourseService:
    def __init__(self, db_path: Path | None = None) -> None:
        self._conn = database.connect(db_path)

    def import_file(self, path: str) -> int:
        """按扩展名导入 CSV 或 XLSX 课表。"""
        suffix = Path(path).suffix.lower()
        if suffix == ".csv":
            return self.import_csv(path)
        if suffix == ".xlsx":
            return self.import_xlsx(path)
        raise ValueError("仅支持 CSV 或 XLSX 课表文件")

    def import_csv(self, path: str) -> int:
        """导入 CSV 课表（整体替换已有数据），返回成功导入条数。"""
        courses: list[Course] = []
        with open(path, newline="", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                course = self._parse_row(row)
                if course is not None:
                    courses.append(course)
        self._replace_courses(courses)
        return len(courses)

    def import_xlsx(self, path: str) -> int:
        """导入按周分块的 XLSX 课表（整体替换已有数据）。"""
        courses = parse_xlsx(path)
        if not courses:
            raise ValueError("没有识别到课程，请确认 XLSX 是按周分块的课表格式")
        self._replace_courses(courses)
        return len(courses)

    def _replace_courses(self, courses: list[Course]) -> None:
        with self._conn:
            self._conn.execute("DELETE FROM courses")
            self._conn.executemany(
                "INSERT INTO courses"
                " (id, name, weekday, start_time, end_time, room, course_date)"
                " VALUES (?, ?, ?, ?, ?, ?, ?)",
                [
                    (
                        course.id,
                        course.name,
                        course.weekday,
                        course.start_time,
                        course.end_time,
                        course.room,
                        course.course_date.isoformat() if course.course_date else None,
                    )
                    for course in courses
                ],
            )

    def list_week(self, today: date | None = None) -> list[Course]:
        """指定日期所在周的课程；CSV 无日期课程每周都会显示。"""
        ref = today or date.today()
        week_start = ref - timedelta(days=ref.weekday())
        week_end = week_start + timedelta(days=6)
        rows = self._conn.execute(
            "SELECT id, name, weekday, start_time, end_time, room, course_date"
            " FROM courses WHERE course_date IS NULL OR course_date BETWEEN ? AND ?"
            " ORDER BY weekday, start_time",
            (week_start.isoformat(), week_end.isoformat()),
        ).fetchall()
        return [self._course_from_row(row) for row in rows]

    def list_tomorrow(self, today: date | None = None) -> list[Course]:
        """明日课程，按开始时间排序。"""
        target = (today or date.today()) + timedelta(days=1)
        rows = self._conn.execute(
            "SELECT id, name, weekday, start_time, end_time, room, course_date"
            " FROM courses WHERE (course_date IS NULL AND weekday = ?) OR course_date = ?"
            " ORDER BY start_time",
            (target.isoweekday(), target.isoformat()),
        ).fetchall()
        return [self._course_from_row(row) for row in rows]

    @staticmethod
    def _course_from_row(row) -> Course:
        raw_date = row["course_date"]
        return Course(
            id=row["id"],
            name=row["name"],
            weekday=row["weekday"],
            start_time=row["start_time"],
            end_time=row["end_time"],
            room=row["room"],
            course_date=date.fromisoformat(raw_date) if raw_date else None,
        )

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
