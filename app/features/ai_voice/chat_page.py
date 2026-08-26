"""2号模块唯一对外入口：create_page(context)。

页面职责：文字对话、自然语言转 TaskDraft、任务确认对话框、录音开始/停止。
AI 调用与语音识别都放到 QThread 里执行，避免卡住界面；用户确认任务后
只通过 `context.events.task_draft_created.emit(draft)` 与外界通信，
不导入、不依赖任务模块内部代码。
"""

from __future__ import annotations

import threading
from datetime import datetime

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.core.app_context import AppContext
from app.core.contracts import TaskDraft

from .ai_service import AIResult, AIService
from .voice_input import VoiceInputUnavailable, VoiceRecognizer

_SOURCE_LABEL = {
    "ollama": "本地模型",
    "openrouter": "云端 OpenRouter",
    "offline": "离线规则",
}


class TaskConfirmDialog(QDialog):
    """确认/编辑 AI 解析出的任务，确认后由调用方负责发出事件。"""

    def __init__(self, draft: TaskDraft, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("确认任务")
        self.result_draft: TaskDraft | None = None
        self._draft = draft

        layout = QFormLayout(self)
        self.title_edit = QLineEdit(draft.title)
        self.due_edit = QLineEdit(f"{draft.due_at:%Y-%m-%d %H:%M}")
        self.category_edit = QLineEdit(draft.category)
        layout.addRow("标题", self.title_edit)
        layout.addRow("时间", self.due_edit)
        layout.addRow("分类", self.category_edit)

        self.error_label = QLabel("")
        self.error_label.setObjectName("mutedText")
        layout.addRow(self.error_label)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def _on_accept(self) -> None:
        title = self.title_edit.text().strip()
        if not title:
            self.error_label.setText("标题不能为空")
            return
        try:
            due_at = datetime.strptime(self.due_edit.text().strip(), "%Y-%m-%d %H:%M")
        except ValueError:
            self.error_label.setText("时间格式应为 YYYY-MM-DD HH:MM，例如 2026-08-26 15:00")
            return

        self.result_draft = TaskDraft(
            title=title,
            due_at=due_at,
            category=self.category_edit.text().strip() or "任务",
            confidence=self._draft.confidence,
        )
        self.accept()


class _ChatWorker(QThread):
    finished_ok = Signal(object)

    def __init__(self, service: AIService, text: str, parent: QWidget | None = None):
        super().__init__(parent)
        self._service = service
        self._text = text

    def run(self) -> None:
        try:
            result = self._service.handle_message(self._text)
        except Exception as exc:  # noqa: BLE001 - 后台线程绝不能让程序崩溃
            result = AIResult(kind="chat", reply="", source="offline", note=str(exc))
        self.finished_ok.emit(result)


class _VoiceWorker(QThread):
    finished_ok = Signal(str, str)  # text, error

    def __init__(self, recognizer: VoiceRecognizer, parent: QWidget | None = None):
        super().__init__(parent)
        self._recognizer = recognizer
        self._stop_event = threading.Event()

    def stop(self) -> None:
        self._stop_event.set()

    def run(self) -> None:
        try:
            text = self._recognizer.listen(self._stop_event.is_set, max_seconds=30.0)
            self.finished_ok.emit(text, "")
        except VoiceInputUnavailable as exc:
            self.finished_ok.emit("", str(exc))
        except Exception as exc:  # noqa: BLE001
            self.finished_ok.emit("", str(exc))


class ChatPage(QWidget):
    def __init__(self, context: AppContext, parent: QWidget | None = None):
        super().__init__(parent)
        self.context = context
        self.service = AIService()
        self.recognizer = VoiceRecognizer()
        self._chat_thread: _ChatWorker | None = None
        self._voice_thread: _VoiceWorker | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)

        heading = QLabel("AI 助手")
        heading.setObjectName("pageTitle")
        subtitle = QLabel("本地模型优先（Ollama），云端 OpenRouter 兜底，离线仍可解析常见任务")
        subtitle.setObjectName("mutedText")
        layout.addWidget(heading)
        layout.addWidget(subtitle)

        self.history = QTextEdit()
        self.history.setReadOnly(True)
        layout.addWidget(self.history, 1)

        input_row = QHBoxLayout()
        self.input_edit = QLineEdit()
        self.input_edit.setPlaceholderText("说点什么，例如：明天下午三点提醒我交报告")
        self.input_edit.returnPressed.connect(self._on_send_clicked)

        self.mic_button = QPushButton("🎙 录音")
        self.mic_button.setCheckable(True)
        self.mic_button.clicked.connect(self._on_mic_clicked)
        if not self.recognizer.available:
            self.mic_button.setEnabled(False)
            self.mic_button.setToolTip("未检测到本地语音识别（需要 Windows + pywin32）")

        self.send_button = QPushButton("发送")
        self.send_button.clicked.connect(self._on_send_clicked)

        input_row.addWidget(self.input_edit, 1)
        input_row.addWidget(self.mic_button)
        input_row.addWidget(self.send_button)
        layout.addLayout(input_row)

        self._append_history("助手", "你好，我是小云。可以直接说需求，例如“明天下午三点提醒我交报告”。")

    # ------------------------------------------------------------------ #
    # 文字对话 / 任务解析
    # ------------------------------------------------------------------ #
    def _on_send_clicked(self) -> None:
        text = self.input_edit.text().strip()
        if not text or self._chat_thread is not None:
            return

        self._append_history("我", text)
        self.input_edit.clear()
        self.send_button.setEnabled(False)

        self._chat_thread = _ChatWorker(self.service, text, self)
        self._chat_thread.finished_ok.connect(self._on_chat_result)
        self._chat_thread.finished.connect(self._on_chat_thread_done)
        self._chat_thread.start()

    def _on_chat_thread_done(self) -> None:
        self.send_button.setEnabled(True)
        self._chat_thread = None

    def _on_chat_result(self, result: AIResult) -> None:
        source_label = _SOURCE_LABEL.get(result.source, result.source)

        if result.kind == "task" and result.draft is not None:
            self._append_history("助手", f"识别到任务请求（来源：{source_label}），请确认：")
            self._confirm_and_emit(result.draft)
        else:
            reply = result.reply or "抱歉，我没有理解这句话。"
            self._append_history("助手", reply)

        if result.note:
            self.context.events.status_message.emit(result.note)

    def _confirm_and_emit(self, draft: TaskDraft) -> None:
        dialog = TaskConfirmDialog(draft, self)
        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.result_draft is not None:
            confirmed = dialog.result_draft
            self.context.events.task_draft_created.emit(confirmed)
            self.context.events.status_message.emit(f"已创建任务：{confirmed.title}")
            self._append_history("助手", f"好的，已创建任务「{confirmed.title}」。")
        else:
            self._append_history("助手", "已取消创建任务。")

    def _append_history(self, speaker: str, text: str) -> None:
        safe_text = text.replace("<", "&lt;").replace(">", "&gt;")
        self.history.append(f"<b>{speaker}：</b>{safe_text}")

    # ------------------------------------------------------------------ #
    # 语音输入（第二优先级）
    # ------------------------------------------------------------------ #
    def _on_mic_clicked(self) -> None:
        if self._voice_thread is not None:
            self.mic_button.setChecked(True)
            self.mic_button.setText("停止中…")
            self.mic_button.setEnabled(False)
            self._voice_thread.stop()
            return

        if not self.recognizer.available:
            self.mic_button.setChecked(False)
            self.context.events.status_message.emit(
                "未检测到本地语音识别（需要 Windows + pywin32），已跳过录音"
            )
            return

        self.mic_button.setChecked(True)
        self.mic_button.setText("⏹ 停止录音")
        self.context.events.status_message.emit("正在录音，再次点击可停止…")

        self._voice_thread = _VoiceWorker(self.recognizer, self)
        self._voice_thread.finished_ok.connect(self._on_voice_result)
        self._voice_thread.finished.connect(self._on_voice_thread_done)
        self._voice_thread.start()

    def _on_voice_result(self, text: str, error: str) -> None:
        if error:
            self.context.events.status_message.emit(f"语音识别失败：{error}")
        elif text:
            existing = self.input_edit.text().strip()
            self.input_edit.setText(f"{existing} {text}".strip())
            self.context.events.status_message.emit("语音识别完成")
        else:
            self.context.events.status_message.emit("没有识别到有效语音")

    def _on_voice_thread_done(self) -> None:
        self._voice_thread = None
        self.mic_button.setChecked(False)
        self.mic_button.setText("🎙 录音")
        self.mic_button.setEnabled(True)


def create_page(context: AppContext) -> QWidget:
    return ChatPage(context)
