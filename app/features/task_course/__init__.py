"""1号：任务、课表和提醒。"""

from app.features.task_course.pages import create_course_page, create_task_page
from app.features.task_course.services import create_services

__all__ = [
    "create_course_page",
    "create_services",
    "create_task_page",
]
