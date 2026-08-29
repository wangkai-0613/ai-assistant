import sys

from PySide6.QtWidgets import QApplication

from app.core.app_context import AppContext
from app.core.events import AppEvents
from app.features.ai_voice import create_page as create_ai_page
from app.features.ai_voice.local_runtime import LocalAIManager
from app.features.task_course import (
    create_course_page,
    create_task_page,
)
from app.features.task_course import (
    create_services as create_task_services,
)
from app.features.weather_system import (
    create_services as create_weather_services,
)
from app.features.weather_system import (
    create_settings_page,
    create_system_page,
    create_weather_page,
)
from app.shell.floating_entry import DesktopPet
from app.shell.main_window import MainWindow


def build_context() -> AppContext:
    context = AppContext(events=AppEvents())
    create_weather_services(context)
    local_ai = LocalAIManager(context.get_service("settings"))
    context.register_service("local_ai", local_ai)
    if local_ai.is_installed():
        local_ai.start()
    task_services = create_task_services(context)
    context.events.task_draft_created.connect(task_services["task"].create)
    return context


def build_window(context: AppContext) -> MainWindow:
    window = MainWindow(context)
    pages = (
        create_task_page(context),
        create_course_page(context),
        create_ai_page(context),
        create_weather_page(context),
        create_system_page(context),
        create_settings_page(context),
    )
    for index, page in enumerate(pages, start=1):
        window.replace_page(index, page)
    pet = DesktopPet()
    pet.apply_theme(str(context.get_service("settings").get("theme", "dark")))
    pet.popup.navigate.connect(window._navigate_to)
    window.desktop_pet = pet
    context.events.task_reminder.connect(pet.show_task_reminder)
    context.events.daily_summary.connect(pet.show_daily_summary)
    return window


def shutdown(context: AppContext) -> None:
    local_ai = context.services.get("local_ai")
    if local_ai is not None:
        local_ai.stop()
    reminder = context.services.get("reminder")
    if reminder is not None:
        reminder.stop()


def run() -> int:
    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName("小云桌面助手")
    app.setQuitOnLastWindowClosed(True)

    context = build_context()
    app.aboutToQuit.connect(lambda: shutdown(context))
    window = build_window(context)
    window.show()
    window.desktop_pet.show()
    return app.exec()
