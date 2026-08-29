"""1号模块：到期提醒服务。

每 30 秒轮询一次：
- 到期未完成任务 -> 提醒弹窗（完成 / 稍后提醒 5 分钟）；
- 当天课程开始前 15 分钟 -> 课程提醒弹窗（每门课每天只提醒一次）。
提醒触发时按设置中的 voice_enabled 开关决定是否语音播报。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from datetime import time as dtime

from PySide6.QtCore import QObject, QTimer
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

from app.core.contracts import Course, Task
from app.features.task_course import voice
from app.features.task_course.task_service import SNOOZE_MINUTES

CHECK_INTERVAL_SECONDS = 30
COURSE_LEAD_MINUTES = 15


@dataclass(frozen=True, slots=True)
class CourseAlert:
    course: Course
    start_at: datetime


class ReminderService(QObject):
    def __init__(
        self,
        context,
        clock=None,
        check_interval: int = CHECK_INTERVAL_SECONDS,
        lead_minutes: int = COURSE_LEAD_MINUTES,
    ) -> None:
        super().__init__()
        self._context = context
        self._clock = clock or datetime.now
        self._lead = timedelta(minutes=lead_minutes)
        self._notified_courses: set[str] = set()
        self._open_dialogs: list[QDialog] = []

        self._timer = QTimer(self)
        self._timer.setInterval(check_interval * 1000)
        self._timer.timeout.connect(self.tick)

    # ---- 生命周期 ----

    def start(self) -> None:
        self._timer.start()

    def stop(self) -> None:
        self._timer.stop()

    # ---- 巡检 ----

    def tick(self) -> None:
        """执行一次到期检查并弹出提醒，异常全部吞掉，不影响主程序。"""
        try:
            now = self._clock()
            due_tasks = self._context.get_service("task").due_pending(now)
            course_alerts = self.collect_course_alerts(now)
        except Exception:  # noqa: BLE001 巡检失败不应崩溃主程序
            return
        if not due_tasks and not course_alerts:
            return

        lines: list[str] = []
        for task in due_tasks:
            lines.append(f"任务 {task.title} 已到期")
            self._show_task_dialog(task)
        for alert in course_alerts:
            minutes = max(0, round((alert.start_at - now).total_seconds() / 60))
            lines.append(f"{alert.course.name} 将在 {minutes} 分钟后开始")
            self._show_course_dialog(alert)

        if self._voice_enabled():
            voice.speak("。".join(lines))

    def collect_course_alerts(self, now: datetime) -> list[CourseAlert]:
        """返回需要课前提醒的课程，并记录已提醒避免重复。"""
        alerts: list[CourseAlert] = []
        for course in self._context.get_service("course").list_week(now.date()):
            if course.weekday != now.isoweekday():
                continue
            start_at = datetime.combine(now.date(), _parse_time(course.start_time))
            if not now <= start_at <= now + self._lead:
                continue
            key = f"{course.id}@{now.date().isoformat()}"
            if key in self._notified_courses:
                continue
            self._notified_courses.add(key)
            alerts.append(CourseAlert(course=course, start_at=start_at))
        return alerts

    # ---- 弹窗 ----

    def _show_task_dialog(self, task: Task) -> None:
        dialog = self._build_dialog(f"任务提醒：{task.title}", "该任务已到期")
        handled = False

        def on_complete() -> None:
            nonlocal handled
            handled = True
            self._context.get_service("task").complete(task.id)
            dialog.accept()

        def on_snooze() -> None:
            nonlocal handled
            handled = True
            self._context.get_service("task").snooze(task.id, now=self._clock())
            dialog.accept()

        def on_finished(_result: int) -> None:
            # 直接关窗等同"稍后提醒"，避免同一任务反复弹窗
            if not handled:
                self._context.get_service("task").snooze(task.id, now=self._clock())
            self._discard(dialog)

        complete_button = QPushButton("完成")
        snooze_button = QPushButton(f"稍后提醒（{SNOOZE_MINUTES}分钟）")
        complete_button.clicked.connect(on_complete)
        snooze_button.clicked.connect(on_snooze)
        dialog.buttons_layout.addWidget(complete_button)
        dialog.buttons_layout.addWidget(snooze_button)
        dialog.finished.connect(on_finished)
        self._present(dialog)

    def _show_course_dialog(self, alert: CourseAlert) -> None:
        course = alert.course
        when = alert.start_at.strftime("%H:%M")
        where = f"，地点：{course.room}" if course.room else ""
        dialog = self._build_dialog(
            f"课前提醒：{course.name}",
            f"{when} 开始{where}，请提前做好准备",
        )
        ok_button = QPushButton("知道了")
        ok_button.clicked.connect(dialog.accept)
        dialog.buttons_layout.addWidget(ok_button)
        dialog.finished.connect(lambda _result: self._discard(dialog))
        self._present(dialog)

    def _build_dialog(self, title: str, message: str) -> QDialog:
        dialog = QDialog()
        dialog.setWindowTitle(title)
        dialog.setModal(False)
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)
        message_label = QLabel(message)
        message_label.setWordWrap(True)
        layout.addWidget(message_label)
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch(1)
        layout.addLayout(buttons_layout)
        dialog.buttons_layout = buttons_layout  # type: ignore[attr-defined]
        self._open_dialogs.append(dialog)
        return dialog

    def _present(self, dialog: QDialog) -> None:
        try:
            dialog.show()
            dialog.raise_()
            dialog.activateWindow()
        except RuntimeError:  # 应用已退出等边界情况
            self._discard(dialog)

    def _discard(self, dialog: QDialog) -> None:
        if dialog in self._open_dialogs:
            self._open_dialogs.remove(dialog)
        dialog.deleteLater()

    # ---- 设置 ----

    def _voice_enabled(self) -> bool:
        try:
            settings = self._context.get_service("settings")
        except LookupError:
            return True
        return bool(settings.get("voice_enabled", True))


def _parse_time(raw: str) -> dtime:
    hours, minutes = raw.split(":")
    return dtime(int(hours), int(minutes))
