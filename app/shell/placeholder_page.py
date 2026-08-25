from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


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

