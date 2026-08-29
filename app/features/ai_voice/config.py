"""AI 模块自己的环境配置读取，不依赖新增第三方库（手写极简 .env 解析）。"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

_ENV_LOADED = False


def _load_dotenv_once() -> None:
    """把仓库根目录 .env 中尚未设置的变量补进 os.environ（不覆盖已有值）。"""
    global _ENV_LOADED
    if _ENV_LOADED:
        return
    _ENV_LOADED = True

    env_path = Path(__file__).resolve().parents[3] / ".env"
    if not env_path.exists():
        return

    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            os.environ.setdefault(key, value)


@dataclass(frozen=True, slots=True)
class AIConfig:
    llama_host: str
    ollama_host: str
    ollama_model: str
    openrouter_api_key: str
    openrouter_model: str
    backend_order: tuple[str, ...]
    request_timeout: float


def load_ai_config() -> AIConfig:
    _load_dotenv_once()

    order_raw = os.environ.get("AI_BACKEND_ORDER", "llamacpp,ollama,openrouter")
    backend_order = tuple(part.strip() for part in order_raw.split(",") if part.strip())

    try:
        timeout = float(os.environ.get("AI_REQUEST_TIMEOUT", "20"))
    except ValueError:
        timeout = 20.0

    return AIConfig(
        llama_host=os.environ.get("LLAMA_CPP_HOST", "http://127.0.0.1:11435"),
        ollama_host=os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434"),
        ollama_model=os.environ.get("OLLAMA_MODEL", "qwen2.5:7b-instruct"),
        openrouter_api_key=os.environ.get("OPENROUTER_API_KEY", ""),
        openrouter_model=os.environ.get("OPENROUTER_MODEL", ""),
        backend_order=backend_order or ("llamacpp", "ollama", "openrouter"),
        request_timeout=timeout,
    )
