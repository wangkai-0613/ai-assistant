"""对上层（chat_page.py）暴露的唯一入口：一句话进，AIResult 出。

流程：本地 Ollama -> 云端 OpenRouter -> 离线规则解析。
任意一步异常都不向外抛出，最终必定返回 AIResult，保证 UI 线程不会崩溃。
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from app.core.contracts import TaskDraft

from .ai_client import AIBackendError, AIRouter, ChatMessage, OllamaBackend, OpenRouterBackend
from .config import AIConfig, load_ai_config
from .task_parser import fallback_parse_task, looks_like_task_request

_WEEKDAY_CN = "一二三四五六日"
_JSON_FENCE = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)


@dataclass(frozen=True, slots=True)
class AIResult:
    kind: Literal["task", "chat"]
    draft: TaskDraft | None = None
    reply: str = ""
    source: str = "offline"
    note: str = ""


def _build_router(config: AIConfig) -> AIRouter:
    registry = {
        "ollama": lambda: OllamaBackend(config.ollama_host, config.ollama_model),
        "openrouter": lambda: OpenRouterBackend(config.openrouter_api_key, config.openrouter_model),
    }
    backends = [registry[name]() for name in config.backend_order if name in registry]
    return AIRouter(backends, timeout=config.request_timeout)


class AIService:
    """AI 对话与任务解析服务。默认本地模型优先，云端 OpenRouter 兜底。"""

    def __init__(self, config: AIConfig | None = None):
        self.config = config or load_ai_config()
        self.router = _build_router(self.config)

    def handle_message(self, text: str, now: datetime | None = None) -> AIResult:
        text = (text or "").strip()
        now = now or datetime.now()
        if not text:
            return AIResult(kind="chat", reply="", source="offline", note="空输入")

        try:
            content, source = self.router.chat(self._build_messages(text, now))
            parsed = self._parse_model_json(content)
        except (AIBackendError, ValueError) as exc:
            return self._fallback(text, now, warning=str(exc))

        if parsed.get("type") == "task":
            draft = self._draft_from_json(parsed)
            if draft is not None:
                return AIResult(kind="task", draft=draft, source=source)
            return self._fallback(text, now, warning="模型返回的任务字段无法解析")

        reply = str(parsed.get("reply") or "").strip() or content.strip()
        return AIResult(kind="chat", reply=reply, source=source)

    @staticmethod
    def _build_messages(text: str, now: datetime) -> list[ChatMessage]:
        weekday = _WEEKDAY_CN[now.weekday()]
        system = (
            "你是桌面助手“小云”的任务解析器。"
            f"当前时间：{now:%Y-%m-%d %H:%M}，星期{weekday}。"
            "如果用户在请求创建提醒、任务或日程，只返回如下 JSON（不要有其他文字）："
            '{"type":"task","title":"任务标题","due_at":"YYYY-MM-DD HH:MM","category":"任务"}，'
            "其中 due_at 必须基于当前时间换算成具体的将来绝对时间。"
            "如果不是任务请求，只返回如下 JSON："
            '{"type":"chat","reply":"你的简短中文回复"}。'
        )
        return [
            ChatMessage(role="system", content=system),
            ChatMessage(role="user", content=text),
        ]

    @staticmethod
    def _parse_model_json(content: str) -> dict:
        cleaned = _JSON_FENCE.sub("", content.strip()).strip()
        start, end = cleaned.find("{"), cleaned.rfind("}")
        if start == -1 or end == -1 or end < start:
            raise ValueError("模型未返回 JSON")
        try:
            return json.loads(cleaned[start : end + 1])
        except json.JSONDecodeError as exc:
            raise ValueError("模型返回的 JSON 无法解析") from exc

    @staticmethod
    def _draft_from_json(parsed: dict) -> TaskDraft | None:
        title = str(parsed.get("title") or "").strip()
        due_raw = str(parsed.get("due_at") or "").strip()
        if not title or not due_raw:
            return None

        due_at = None
        for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M"):
            try:
                due_at = datetime.strptime(due_raw, fmt)
                break
            except ValueError:
                continue
        if due_at is None:
            return None

        category = str(parsed.get("category") or "任务").strip() or "任务"
        return TaskDraft(title=title, due_at=due_at, category=category, confidence=0.9)

    @staticmethod
    def _fallback(text: str, now: datetime, warning: str) -> AIResult:
        draft = fallback_parse_task(text, now)
        if draft is not None:
            return AIResult(
                kind="task",
                draft=draft,
                source="offline",
                note=f"AI 服务不可用，已使用离线规则解析（{warning}）",
            )
        if looks_like_task_request(text):
            reply = "没能识别出具体时间，可以试试类似“明天下午三点提醒我交报告”这样的说法。"
        else:
            reply = "当前 AI 服务不可用，暂时无法自由对话。你可以说“明天下午三点提醒我交报告”来创建任务。"
        return AIResult(kind="chat", reply=reply, source="offline", note=warning)
