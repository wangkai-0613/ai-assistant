from datetime import datetime

from app.features.ai_voice.ai_client import ChatMessage
from app.features.ai_voice.ai_service import AIService


class _RecordingRouter:
    def __init__(self) -> None:
        self.calls: list[list[ChatMessage]] = []

    def chat(self, messages: list[ChatMessage]) -> tuple[str, str]:
        self.calls.append(messages)
        return '{"type":"chat","reply":"好的"}', "ollama"


def test_previous_turn_is_sent_to_model() -> None:
    service = AIService()
    router = _RecordingRouter()
    service.router = router
    now = datetime(2026, 8, 29, 16, 0)

    service.handle_message("我叫小王", now=now)
    service.handle_message("我叫什么？", now=now)

    second_call = router.calls[1]
    assert [(message.role, message.content) for message in second_call[1:]] == [
        ("user", "我叫小王"),
        ("assistant", '{"type":"chat","reply":"好的"}'),
        ("user", "我叫什么？"),
    ]