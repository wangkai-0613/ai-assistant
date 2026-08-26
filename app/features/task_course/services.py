"""1号模块：服务注册入口。"""

from __future__ import annotations

from app.core.app_context import AppContext
from app.features.task_course.course_service import CourseService
from app.features.task_course.reminder_service import ReminderService
from app.features.task_course.task_service import TaskService


def create_services(context: AppContext) -> dict[str, object]:
    """注册任务、课表和提醒服务，并启动到期巡检。"""
    task_service = TaskService(events=context.events)
    course_service = CourseService()
    reminder_service = ReminderService(context)

    context.register_service("task", task_service)
    context.register_service("course", course_service)
    context.register_service("reminder", reminder_service)

    reminder_service.start()
    return {
        "task": task_service,
        "course": course_service,
        "reminder": reminder_service,
    }
