"""桌宠悬浮入口 — 鼠标悬停小猫显示功能菜单。

DesktopPet: 桌面宠物小猫，可拖拽，悬停弹出功能菜单。
PetPopup: 弹出菜单面板，包含功能快捷入口。
"""

from pathlib import Path

from PySide6.QtCore import QPoint, Qt, QTimer, Signal
from PySide6.QtGui import (
    QBrush,
    QColor,
    QMouseEvent,
    QPainter,
    QPainterPath,
    QPen,
)
from PySide6.QtWidgets import (
    QApplication,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class PetPopup(QWidget):
    navigate = Signal(int)

    FEATURES = (
        ("🏠", "首页", 0),
        ("📋", "任务", 1),
        ("📅", "课表", 2),
        ("🤖", "AI 助手", 3),
        ("🌤️", "天气", 4),
        ("💻", "系统", 5),
        ("⚙️", "设置", 6),
    )

    def __init__(self, owner, parent=None):
        super().__init__(parent)
        self._owner = owner
        self.setObjectName("petPopup")
        self.setFixedWidth(148)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(2)

        for icon, label, index in self.FEATURES:
            btn = QPushButton(f"  {icon}  {label}")
            btn.setObjectName("petMenuButton")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, idx=index: self._on_click(idx))
            layout.addWidget(btn)

        self._load_stylesheet()

    def _load_stylesheet(self):
        style_path = Path(__file__).resolve().parents[1] / "resources" / "style.qss"
        if style_path.exists():
            self.setStyleSheet(style_path.read_text(encoding="utf-8"))

    def _on_click(self, index: int):
        self.navigate.emit(index)
        self.hide()
        self._owner._on_popup_hidden()

    def enterEvent(self, event):
        self._owner._cancel_hide()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._owner._schedule_hide()
        super().leaveEvent(event)

class DesktopPet(QWidget):
    clicked = Signal()
    _DRAG_THRESHOLD = 5
    _POPUP_DELAY_MS = 250
    _PET_SIZE = 90

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("desktopPet")
        self.setFixedSize(self._PET_SIZE, self._PET_SIZE)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        self._popup = PetPopup(owner=self)
        self._popup_visible = False

        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self._try_hide_popup)

        self._drag_pos: QPoint | None = None
        self._dragging = False

    @property
    def popup(self):
        return self._popup

    def _cancel_hide(self):
        self._hide_timer.stop()

    def _schedule_hide(self):
        self._hide_timer.start(self._POPUP_DELAY_MS)

    def enterEvent(self, event):
        self._cancel_hide()
        self._show_popup()
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._schedule_hide()
        super().leaveEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        s = self._PET_SIZE
        m = 4
        r = (s - m * 2) / 2

        center_x = s / 2
        center_y = s / 2 + 3

        body_color = QColor("#FFB74D")
        body_dark = QColor("#F57C00")
        ear_inner = QColor("#FFCCBC")
        eye_white = QColor("#FFFFFF")
        eye_pupil = QColor("#3E2723")
        nose_color = QColor("#FF8A80")
        mouth_color = QColor("#795548")
        whisker_color = QColor("#BCAAA4")

        # ---- ears ----
        ear_path = QPainterPath()
        ear_path.moveTo(center_x - r * 0.3, center_y - r * 0.75)
        ear_path.lineTo(center_x - r * 0.85, center_y - r * 1.05)
        ear_path.lineTo(center_x - r * 0.7, center_y - r * 0.35)
        ear_path.closeSubpath()
        painter.setPen(QPen(body_dark, 2))
        painter.setBrush(QBrush(body_color))
        painter.drawPath(ear_path)

        ear_path2 = QPainterPath()
        ear_path2.moveTo(center_x + r * 0.3, center_y - r * 0.75)
        ear_path2.lineTo(center_x + r * 0.85, center_y - r * 1.05)
        ear_path2.lineTo(center_x + r * 0.7, center_y - r * 0.35)
        ear_path2.closeSubpath()
        painter.drawPath(ear_path2)

        ear_inner1 = QPainterPath()
        ear_inner1.moveTo(center_x - r * 0.35, center_y - r * 0.7)
        ear_inner1.lineTo(center_x - r * 0.72, center_y - r * 0.92)
        ear_inner1.lineTo(center_x - r * 0.6, center_y - r * 0.42)
        ear_inner1.closeSubpath()
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(ear_inner))
        painter.drawPath(ear_inner1)

        ear_inner2 = QPainterPath()
        ear_inner2.moveTo(center_x + r * 0.35, center_y - r * 0.7)
        ear_inner2.lineTo(center_x + r * 0.72, center_y - r * 0.92)
        ear_inner2.lineTo(center_x + r * 0.6, center_y - r * 0.42)
        ear_inner2.closeSubpath()
        painter.drawPath(ear_inner2)

        # ---- face ----
        painter.setPen(QPen(body_dark, 2.5))
        painter.setBrush(QBrush(body_color))
        painter.drawEllipse(QPoint(int(center_x), int(center_y)), int(r), int(r))

        # ---- eyes ----
        eye_rad = r * 0.22
        painter.setPen(QPen(body_dark, 1.5))
        painter.setBrush(QBrush(eye_white))
        painter.drawEllipse(QPoint(int(center_x - r * 0.35), int(center_y - r * 0.15)), int(eye_rad), int(eye_rad * 1.15))
        painter.drawEllipse(QPoint(int(center_x + r * 0.35), int(center_y - r * 0.15)), int(eye_rad), int(eye_rad * 1.15))

        pupil_rad = eye_rad * 0.55
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(eye_pupil))
        painter.drawEllipse(QPoint(int(center_x - r * 0.35), int(center_y - r * 0.15)), int(pupil_rad), int(pupil_rad * 1.1))
        painter.drawEllipse(QPoint(int(center_x + r * 0.35), int(center_y - r * 0.15)), int(pupil_rad), int(pupil_rad * 1.1))

        eye_shine = r * 0.06
        painter.setBrush(QBrush(QColor("#FFFFFF")))
        painter.drawEllipse(QPoint(int(center_x - r * 0.35 - eye_rad * 0.3), int(center_y - r * 0.15 - eye_rad * 0.4)), int(eye_shine), int(eye_shine))
        painter.drawEllipse(QPoint(int(center_x + r * 0.35 - eye_rad * 0.3), int(center_y - r * 0.15 - eye_rad * 0.4)), int(eye_shine), int(eye_shine))

        # ---- nose ----
        nose_size = r * 0.12
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(nose_color))
        nose_path = QPainterPath()
        nose_path.moveTo(center_x, center_y + r * 0.15 - nose_size)
        nose_path.lineTo(center_x - nose_size, center_y + r * 0.15 + nose_size * 0.6)
        nose_path.lineTo(center_x + nose_size, center_y + r * 0.15 + nose_size * 0.6)
        nose_path.closeSubpath()
        painter.drawPath(nose_path)

        # ---- mouth ----
        painter.setPen(QPen(mouth_color, 1.5))
        mouth_y = center_y + r * 0.22
        painter.drawLine(QPoint(int(center_x - r * 0.15), int(mouth_y + r * 0.12)), QPoint(int(center_x), int(mouth_y)))
        painter.drawLine(QPoint(int(center_x), int(mouth_y)), QPoint(int(center_x + r * 0.15), int(mouth_y + r * 0.12)))

        # ---- whiskers ----
        painter.setPen(QPen(whisker_color, 1.2))
        wx = center_x - r * 0.3
        wy = center_y + r * 0.05
        painter.drawLine(QPoint(int(wx - r * 0.5), int(wy - r * 0.1)), QPoint(int(wx), int(wy)))
        painter.drawLine(QPoint(int(wx - r * 0.5), int(wy + r * 0.05)), QPoint(int(wx), int(wy + r * 0.05)))
        painter.drawLine(QPoint(int(wx - r * 0.45), int(wy + r * 0.2)), QPoint(int(wx), int(wy + r * 0.1)))

        wx = center_x + r * 0.3
        painter.drawLine(QPoint(int(wx + r * 0.5), int(wy - r * 0.1)), QPoint(int(wx), int(wy)))
        painter.drawLine(QPoint(int(wx + r * 0.5), int(wy + r * 0.05)), QPoint(int(wx), int(wy + r * 0.05)))
        painter.drawLine(QPoint(int(wx + r * 0.45), int(wy + r * 0.2)), QPoint(int(wx), int(wy + r * 0.1)))

        painter.end()

    def _show_popup(self):
        if self._popup_visible:
            return
        self._popup_visible = True
        screen = self.screen()
        if screen is None:
            screen = QApplication.primaryScreen()
        screen_geom = screen.availableGeometry()
        top_left = self.mapToGlobal(QPoint(0, 0))
        gap = 10
        popup_w = self._popup.width()
        popup_h = self._popup.height()

        if top_left.x() + self.width() + gap + popup_w <= screen_geom.right():
            popup_x = top_left.x() + self.width() + gap
        else:
            popup_x = top_left.x() - popup_w - gap

        popup_y = top_left.y() - (popup_h - self.height()) // 2
        if popup_y < screen_geom.top():
            popup_y = screen_geom.top() + gap
        elif popup_y + popup_h > screen_geom.bottom():
            popup_y = screen_geom.bottom() - popup_h - gap

        self._popup.move(popup_x, popup_y)
        self._popup.show()
    def _try_hide_popup(self):
        if self._popup.isVisible():
            self._popup.hide()
        self._popup_visible = False

    def _on_popup_hidden(self):
        self._popup_visible = False

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint()
            self._dragging = False
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._drag_pos is not None:
            delta = event.globalPosition().toPoint() - self._drag_pos
            if abs(delta.x()) > self._DRAG_THRESHOLD or abs(delta.y()) > self._DRAG_THRESHOLD:
                self._dragging = True
            if self._dragging:
                self.move(self.pos() + delta)
                self._drag_pos = event.globalPosition().toPoint()
                if self._popup_visible:
                    self._popup.hide()
                    self._on_popup_hidden()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton and not self._dragging:
            self._show_popup()
        self._drag_pos = None
        self._dragging = False
        super().mouseReleaseEvent(event)