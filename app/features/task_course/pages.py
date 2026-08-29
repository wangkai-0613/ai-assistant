"""1号模块：任务与课表页面。"""

from __future__ import annotations

from datetime import date, datetime, timedelta

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDateTimeEdit,
    QDialog,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLayout,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app.core.app_context import AppContext
from app.core.contracts import TaskDraft
from app.features.task_course.course_service import WEEKDAY_NAMES


class _Section(QFrame):
    """带标题的卡片分区。"""

    def __init__(self, title: str, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("sectionCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        heading = QLabel(title)
        heading.setObjectName("sectionTitle")
        layout.addWidget(heading)


class TaskDialog(QDialog):
    """新建任务对话框。"""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("新建任务")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        form = QFormLayout()
        form.setSpacing(10)
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("任务标题，如：提交作业")
        self.due_input = QDateTimeEdit()
        self.due_input.setDisplayFormat("yyyy-MM-dd HH:mm")
        self.due_input.setCalendarPopup(True)
        self.due_input.setDateTime(datetime.now() + timedelta(hours=1))
        self.category_input = QLineEdit("任务")
        form.addRow("标题", self.title_input)
        form.addRow("到期时间", self.due_input)
        form.addRow("分类", self.category_input)
        layout.addLayout(form)

        buttons = QHBoxLayout()
        buttons.addStretch(1)
        self.save_button = QPushButton("保存")
        self.cancel_button = QPushButton("取消")
        buttons.addWidget(self.save_button)
        buttons.addWidget(self.cancel_button)
        layout.addLayout(buttons)

        self.save_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

    def draft(self) -> TaskDraft | None:
        title = self.title_input.text().strip()
        if not title:
            return None
        return TaskDraft(
            title=title,
            due_at=self.due_input.dateTime().toPython(),
            category=self.category_input.text().strip() or "任务",
        )


class TaskPage(QWidget):
    def __init__(self, context: AppContext, parent=None) -> None:
        super().__init__(parent)
        self.context = context

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(14)

        heading = QLabel("任务")
        heading.setObjectName("pageTitle")
        layout.addWidget(heading)

        card = _Section("任务列表")
        card_layout = card.layout()

        toolbar = QHBoxLayout()
        self.new_button = QPushButton("新建任务")
        toolbar.addWidget(self.new_button)
        toolbar.addStretch(1)
        card_layout.addLayout(toolbar)

        self.task_list = QListWidget()
        self.task_list.setAlternatingRowColors(True)
        card_layout.addWidget(self.task_list, 1)

        actions = QHBoxLayout()
        self.complete_button = QPushButton("标记完成")
        self.delete_button = QPushButton("删除")
        actions.addWidget(self.complete_button)
        actions.addWidget(self.delete_button)
        actions.addStretch(1)
        card_layout.addLayout(actions)

        self.status_label = QLabel("")
        self.status_label.setObjectName("mutedText")
        card_layout.addWidget(self.status_label)

        layout.addWidget(card, 1)

        self.new_button.clicked.connect(self._on_new)
        self.complete_button.clicked.connect(self._on_complete)
        self.delete_button.clicked.connect(self._on_delete)
        context.events.task_created.connect(lambda _task: self.refresh())
        self.refresh()

    def refresh(self) -> None:
        service = self.context.get_service("task")
        self.task_list.clear()
        for task in service.list_all():
            mark = "✅" if task.completed else "⬜"
            due = task.due_at.strftime("%m-%d %H:%M")
            item = QListWidgetItem(f"{mark} {task.title}　截止 {due}　[{task.category}]")
            item.setData(Qt.ItemDataRole.UserRole, task.id)
            if task.completed:
                item.setForeground(Qt.GlobalColor.gray)
            self.task_list.addItem(item)
        self.status_label.setText(f"共 {self.task_list.count()} 条任务")

    def _selected_task_id(self) -> str | None:
        item = self.task_list.currentItem()
        return item.data(Qt.ItemDataRole.UserRole) if item is not None else None

    def _on_new(self) -> None:
        dialog = TaskDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        draft = dialog.draft()
        if draft is None:
            self.status_label.setText("标题不能为空")
            return
        self.context.get_service("task").create(draft)
        self.status_label.setText(f"已创建：{draft.title}")

    def _on_complete(self) -> None:
        task_id = self._selected_task_id()
        if task_id is None:
            return
        self.context.get_service("task").complete(task_id)
        self.refresh()

    def _on_delete(self) -> None:
        task_id = self._selected_task_id()
        if task_id is None:
            return
        self.context.get_service("task").delete(task_id)
        self.refresh()


class CoursePage(QWidget):
    def __init__(self, context: AppContext, parent=None) -> None:
        super().__init__(parent)
        self.context = context

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(14)
        layout.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)
        scroll.setWidget(content)
        outer_layout.addWidget(scroll)
        heading = QLabel("课表")
        heading.setObjectName("pageTitle")
        layout.addWidget(heading)

        tomorrow_card = _Section("明日课程")
        self.tomorrow_label = QLabel("暂无课程数据")
        self.tomorrow_label.setWordWrap(True)
        tomorrow_card.layout().addWidget(self.tomorrow_label)
        layout.addWidget(tomorrow_card)

        week_card = _Section("本周课表")
        week_layout = week_card.layout()

        toolbar = QHBoxLayout()
        self.import_button = QPushButton("导入课表")
        toolbar.addWidget(self.import_button)
        toolbar.addStretch(1)
        week_layout.addLayout(toolbar)

        self.week_range_label = QLabel("")
        self.week_range_label.setObjectName("mutedText")
        week_layout.addWidget(self.week_range_label)
        self.grid = QGridLayout()
        self.grid.setSpacing(8)
        week_layout.addLayout(self.grid)

        self.status_label = QLabel("")
        self.status_label.setObjectName("mutedText")
        week_layout.addWidget(self.status_label)
        layout.addWidget(week_card)

        next_week_card = _Section("下一周课表")
        next_week_layout = next_week_card.layout()
        self.next_week_range_label = QLabel("")
        self.next_week_range_label.setObjectName("mutedText")
        next_week_layout.addWidget(self.next_week_range_label)
        self.next_week_grid = QGridLayout()
        self.next_week_grid.setSpacing(8)
        next_week_layout.addLayout(self.next_week_grid)
        layout.addWidget(next_week_card)
        self.import_button.clicked.connect(self._on_import)
        self.refresh()

    def refresh(self) -> None:
        service = self.context.get_service("course")
        today = date.today()

        tomorrow = service.list_tomorrow(today)
        if tomorrow:
            lines = [
                f"{course.start_time} {course.name}"
                + (f"（{course.room}）" if course.room else "")
                for course in tomorrow
            ]
            self.tomorrow_label.setText("　｜　".join(lines))
        else:
            self.tomorrow_label.setText("明天没有课程安排")

        self._populate_week(
            self.grid,
            self.week_range_label,
            service.list_week(today),
            today,
        )
        next_week = today + timedelta(days=7)
        self._populate_week(
            self.next_week_grid,
            self.next_week_range_label,
            service.list_week(next_week),
            next_week,
        )

    def _populate_week(self, grid, range_label, courses, reference: date) -> None:
        while grid.count():
            widget = grid.takeAt(0).widget()
            if widget is not None:
                widget.deleteLater()

        week_start = reference - timedelta(days=reference.weekday())
        week_end = week_start + timedelta(days=6)
        range_label.setText(f"{week_start:%Y-%m-%d} — {week_end:%Y-%m-%d}")

        courses_by_day = {weekday: [] for weekday in range(1, 8)}
        for course in courses:
            courses_by_day[course.weekday].append(course)

        for index, name in enumerate(WEEKDAY_NAMES):
            day = week_start + timedelta(days=index)
            day_label = QLabel(f"{name}\n{day:%m-%d}")
            day_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            day_label.setObjectName("sectionTitle")
            day_label.setMinimumWidth(125)
            grid.setColumnStretch(index, 1)
            grid.addWidget(day_label, 0, index)

            day_courses = courses_by_day[index + 1]
            if not day_courses:
                empty = QLabel("无课")
                empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
                empty.setObjectName("mutedText")
                grid.addWidget(empty, 1, index)
                continue
            for row, course in enumerate(day_courses, start=1):
                cell = QLabel(self._format_course(course))
                cell.setWordWrap(True)
                cell.setAlignment(Qt.AlignmentFlag.AlignTop)
                cell.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
                cell.setMinimumHeight(96)
                cell.setObjectName("courseCell")
                grid.addWidget(cell, row, index)
    @staticmethod
    def _format_course(course) -> str:
        span = course.start_time
        if course.end_time:
            span += f"-{course.end_time}"
        text = f"{span}\n{course.name}"
        if course.room:
            text += f"\n{course.room}"
        return text

    def _on_import(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "选择课表文件",
            "",
            "课表文件 (*.xlsx *.csv);;Excel 工作簿 (*.xlsx);;CSV 文件 (*.csv)",
        )
        if not path:
            return
        try:
            count = self.context.get_service("course").import_file(path)
        except (OSError, ValueError) as exc:
            message = f"导入失败：{exc}"
            self.status_label.setText(message)
            self.context.events.status_message.emit(message)
            return
        message = f"已导入 {count} 门课程"
        self.status_label.setText(message)
        self.context.events.status_message.emit(message)
        self.refresh()


def create_task_page(context: AppContext) -> TaskPage:
    return TaskPage(context)


def create_course_page(context: AppContext) -> CoursePage:
    return CoursePage(context)
