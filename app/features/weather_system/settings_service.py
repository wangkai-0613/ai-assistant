"""3号模块：配置存储服务。

使用独立 JSON 文件保存设置，不与其他模块争用 SQLite。
文件位置：用户主目录下 .xiao_assistant/settings.json（不入库）。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DEFAULT_SETTINGS: dict[str, Any] = {
    "city": "武汉",
    "theme": "dark",
    "openrouter_key": "",
    "local_ai_dir": "",
    "voice_enabled": True,
    "auto_start": False,
    "cpu_monitor": False,
}


def default_config_path() -> Path:
    path = Path.home() / ".xiao_assistant"
    path.mkdir(parents=True, exist_ok=True)
    return path / "settings.json"


class SettingsService:
    def __init__(self, path: Path | None = None) -> None:
        self._path = path or default_config_path()
        self._data: dict[str, Any] = dict(DEFAULT_SETTINGS)
        self.load()

    @property
    def path(self) -> Path:
        return self._path

    def load(self) -> None:
        if not self._path.exists():
            return
        try:
            saved = json.loads(self._path.read_text(encoding="utf-8"))
            for key, value in saved.items():
                if key in DEFAULT_SETTINGS:
                    self._data[key] = value
        except (json.JSONDecodeError, OSError):
            pass

    def save(self) -> None:
        self._path.write_text(
            json.dumps(self._data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        if key not in DEFAULT_SETTINGS:
            raise KeyError(f"未知设置项：{key}")
        self._data[key] = value
        self.save()