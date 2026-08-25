from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.core.events import AppEvents


@dataclass(slots=True)
class AppContext:
    events: AppEvents
    services: dict[str, Any] = field(default_factory=dict)

    def register_service(self, name: str, service: Any) -> None:
        if name in self.services:
            raise ValueError(f"服务已注册：{name}")
        self.services[name] = service

    def get_service(self, name: str) -> Any:
        try:
            return self.services[name]
        except KeyError as exc:
            raise LookupError(f"服务尚未注册：{name}") from exc

