from PySide6.QtCore import QObject, Signal


class AppEvents(QObject):
    task_draft_created = Signal(object)
    task_created = Signal(object)
    task_reminder = Signal(object, str)
    daily_summary = Signal(str)
    settings_changed = Signal()
    status_message = Signal(str)

