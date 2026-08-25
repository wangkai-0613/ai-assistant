import sys

from PySide6.QtWidgets import QApplication

from app.core.app_context import AppContext
from app.core.contracts import TaskDraft
from app.core.events import AppEvents
from app.features.ai_voice.chat_page import create_page


def _print_draft(draft: TaskDraft) -> None:
    print("[假接收器] 收到 TaskDraft:")
    print(f"  title      = {draft.title}")
    print(f"  due_at     = {draft.due_at:%Y-%m-%d %H:%M}")
    print(f"  category   = {draft.category}")
    print(f"  confidence = {draft.confidence}")


def _print_status(message: str) -> None:
    print(f"[状态] {message}")


def main() -> int:
    app = QApplication.instance() or QApplication(sys.argv)

    context = AppContext(events=AppEvents())
    context.events.task_draft_created.connect(_print_draft)
    context.events.status_message.connect(_print_status)

    window = create_page(context)
    window.setWindowTitle("AI与语音输入独立演示 - 2号 muzi2887")
    window.resize(720, 560)
    window.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
