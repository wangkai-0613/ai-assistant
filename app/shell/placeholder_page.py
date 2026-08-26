from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget


class PlaceholderPage(QWidget):
    def __init__(self, title: str, owner: str, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)

        heading = QLabel(title)
        heading.setObjectName("pageTitle")
        message = QLabel(f"该页面由{owner}负责，目前使用占位内容。")
        message.setObjectName("mutedText")

        layout.addWidget(heading)
        layout.addWidget(message)
        layout.addStretch(1)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)


class EmptyStatePage(QWidget):
    def __init__(
        self,
        icon: str = "📭",
        title: str = "暂无内容",
        description: str = "这里还没有任何数据，请稍后再来看看。",
        action_text: str | None = None,
        on_action: object = None,
        parent=None,
    ):
        super().__init__(parent)
        self.setObjectName("emptyState")

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(12)

        icon_label = QLabel(icon)
        icon_label.setObjectName("emptyStateIcon")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title_label = QLabel(title)
        title_label.setObjectName("emptyStateTitle")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        desc_label = QLabel(description)
        desc_label.setObjectName("emptyStateText")
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setWordWrap(True)

        layout.addStretch(2)
        layout.addWidget(icon_label)
        layout.addWidget(title_label)
        layout.addWidget(desc_label)

        if action_text and on_action:
            btn = QPushButton(action_text)
            btn.setObjectName("primaryButton")
            btn.clicked.connect(on_action)
            layout.addSpacing(8)
            layout.addWidget(btn, 0, Qt.AlignmentFlag.AlignCenter)

        layout.addStretch(3)


class ErrorStatePage(QWidget):
    def __init__(
        self,
        icon: str = "⚠️",
        title: str = "加载失败",
        description: str = "数据加载时遇到问题，请检查网络连接后重试。",
        retry_text: str = "重试",
        on_retry: object = None,
        parent=None,
    ):
        super().__init__(parent)
        self.setObjectName("errorState")

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(12)

        icon_label = QLabel(icon)
        icon_label.setObjectName("errorStateIcon")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title_label = QLabel(title)
        title_label.setObjectName("errorStateTitle")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        desc_label = QLabel(description)
        desc_label.setObjectName("errorStateText")
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setWordWrap(True)

        layout.addStretch(2)
        layout.addWidget(icon_label)
        layout.addWidget(title_label)
        layout.addWidget(desc_label)

        if on_retry:
            btn = QPushButton(retry_text)
            btn.setObjectName("primaryButton")
            btn.clicked.connect(on_retry)
            layout.addSpacing(8)
            layout.addWidget(btn, 0, Qt.AlignmentFlag.AlignCenter)

        layout.addStretch(3)