from PySide6.QtCore import QObject, Signal


class AppEvents(QObject):
    task_draft_created = Signal(object)
    task_created = Signal(object)
    settings_changed = Signal()
    status_message = Signal(str)

