"""两个具体的 AI 后端（本地 Ollama / 云端 OpenRouter）与一个按顺序尝试的路由器。

本地优先：默认顺序是先试本地 Ollama，再退回云端 OpenRouter，都失败则由
上层 ai_service.py 使用离线规则兜底，任何一步失败都不应让程序崩溃。
"""

from __future__ import annotations

from dataclasses import dataclass

import httpx


class AIBackendError(Exception):
    """单个 AI 后端调用失败（未配置、网络失败、超时、返回异常等）。"""


@dataclass(frozen=True, slots=True)
class ChatMessage:
    role: str
    content: str


class AIBackend:
    name = "backend"

    def chat(self, messages: list[ChatMessage], timeout: float) -> str:
        raise NotImplementedError


class OllamaBackend(AIBackend):
    """本地部署模型，通过 Ollama 的 REST API（默认 127.0.0.1:11434）访问。"""

    name = "ollama"

    def __init__(self, host: str, model: str):
        self.host = host.rstrip("/")
        self.model = model

    def chat(self, messages: list[ChatMessage], timeout: float) -> str:
        if not self.model:
            raise AIBackendError("未配置本地模型名称（OLLAMA_MODEL）")

        payload = {
            "model": self.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": False,
        }
        try:
            response = httpx.post(f"{self.host}/api/chat", json=payload, timeout=timeout)
            response.raise_for_status()
        except httpx.ConnectError as exc:
            raise AIBackendError(
                f"本地模型服务未启动或无法连接（{self.host}），请先运行 `ollama serve`"
            ) from exc
        except httpx.TimeoutException as exc:
            raise AIBackendError("本地模型响应超时") from exc
        except httpx.HTTPStatusError as exc:
            raise AIBackendError(f"本地模型返回错误：HTTP {exc.response.status_code}") from exc
        except httpx.HTTPError as exc:
            raise AIBackendError(f"本地模型请求失败：{exc}") from exc

        try:
            data = response.json()
            content = data.get("message", {}).get("content")
        except ValueError as exc:
            raise AIBackendError("本地模型返回内容不是合法 JSON") from exc

        if not content:
            raise AIBackendError("本地模型返回空内容")
        return content


class OpenRouterBackend(AIBackend):
    """云端兜底：仅在本地模型不可用且配置了 API Key 时才会被调用。"""

    name = "openrouter"
    API_URL = "https://openrouter.ai/api/v1/chat/completions"

    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model

    def chat(self, messages: list[ChatMessage], timeout: float) -> str:
        if not self.api_key:
            raise AIBackendError("未配置 OPENROUTER_API_KEY")
        if not self.model:
            raise AIBackendError("未配置 OPENROUTER_MODEL")

        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload = {
            "model": self.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
        }
        try:
            response = httpx.post(self.API_URL, headers=headers, json=payload, timeout=timeout)
            response.raise_for_status()
        except httpx.ConnectError as exc:
            raise AIBackendError("无法连接 OpenRouter，请检查网络") from exc
        except httpx.TimeoutException as exc:
            raise AIBackendError("OpenRouter 请求超时") from exc
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            if status == 401:
                raise AIBackendError("OpenRouter API Key 无效") from exc
            raise AIBackendError(f"OpenRouter 返回错误：HTTP {status}") from exc
        except httpx.HTTPError as exc:
            raise AIBackendError(f"OpenRouter 请求失败：{exc}") from exc

        try:
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except (ValueError, KeyError, IndexError) as exc:
            raise AIBackendError("OpenRouter 返回内容为空或格式异常") from exc


class AIRouter:
    """依配置顺序依次尝试各后端，第一个成功的结果即为最终结果。"""

    def __init__(self, backends: list[AIBackend], timeout: float = 20.0):
        self.backends = backends
        self.timeout = timeout

    def chat(self, messages: list[ChatMessage]) -> tuple[str, str]:
        errors: list[str] = []
        for backend in self.backends:
            try:
                content = backend.chat(messages, self.timeout)
                return content, backend.name
            except AIBackendError as exc:
                errors.append(f"{backend.name}: {exc}")
        raise AIBackendError("；".join(errors) if errors else "未配置任何可用的 AI 后端")
