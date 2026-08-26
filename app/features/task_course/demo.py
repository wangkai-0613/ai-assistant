"""1号模块独立演示。

验收链路：启动后自动导入 sample_data/courses.csv（如存在），
点击"添加一分钟后的测试任务"，约一分钟后收到提醒弹窗，
选择"完成"或"稍后提醒"，在任务页可见状态变化。

运行：python -m app.features.task_course.demo
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path

from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.core.app_context import AppContext
from app.core.contracts import TaskDraft
from app.core.events import AppEvents
from app.features.task_course import (
    create_course_page,
    create_services,
    create_task_page,
)

SAMPLE_CSV = Path(__file__).resolve().parents[3] / "sample_data" / "courses.csv"


class DemoWindow(QMainWindow):
    def __init__(self, context: AppContext) -> None:
        super().__init__()
        self.context = context
        self.setWindowTitle("任务、课表与提醒独立演示（1号 arcadiamuran-web）")
        self.resize(1040, 700)

        root = QWidget()
        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        sidebar = QWidget()
        sidebar.setFixedWidth(200)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(16, 24, 16, 20)

        self.navigation = QListWidget()
        self.navigation.addItems(["任务", "课表"])
        self.navigation.setCurrentRow(0)

        self.demo_button = QPushButton("添加一分钟后的测试任务")
        self.hint_label = QLabel(
            "提示：任务到期后约 30 秒内会弹出提醒；"
            "课表页可查看一周安排与明日课程。"
        )
        self.hint_label.setWordWrap(True)

        sidebar_layout.addWidget(self.navigation)
        sidebar_layout.addSpacing(16)
        sidebar_layout.addWidget(self.demo_button)
        sidebar_layout.addWidget(self.hint_label)
        sidebar_layout.addStretch(1)

        self.pages = QStackedWidget()
        self.pages.addWidget(create_task_page(context))
        self.pages.addWidget(create_course_page(context))

        root_layout.addWidget(sidebar)
        root_layout.addWidget(self.pages, 1)
        self.setCentralWidget(root)

        self.navigation.currentRowChanged.connect(self.pages.setCurrentIndex)
        self.demo_button.clicked.connect(self._add_demo_task)

    def _add_demo_task(self) -> None:
        draft = TaskDraft(
            title="演示任务：一分钟后到期",
            due_at=datetime.now() + timedelta(minutes=1),
        )
        self.context.get_service("task").create(draft)
        self.context.events.status_message.emit("已添加一分钟后的测试任务")


def _auto_import_sample(context: AppContext) -> None:
    if SAMPLE_CSV.exists():
        try:
            count = context.get_service("course").import_csv(str(SAMPLE_CSV))
            context.events.status_message.emit(f"已自动导入示例课表（{count} 门）")
        except OSError:
            pass


def main() -> int:
    app = QApplication.instance() or QApplication(sys.argv)
    context = AppContext(events=AppEvents())
    create_services(context)
    _auto_import_sample(context)

    window = DemoWindow(context)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
