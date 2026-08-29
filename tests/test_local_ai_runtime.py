import zipfile
from pathlib import Path

import pytest

from app.features.ai_voice.ai_client import ChatMessage, LlamaCppBackend
from app.features.ai_voice.local_runtime import (
    MODEL_FILENAME,
    InstallWorker,
    LocalAIManager,
)


class _Settings:
    def __init__(self, path: Path) -> None:
        self.data = {"local_ai_dir": str(path)}

    def get(self, key, default=None):
        return self.data.get(key, default)

    def set(self, key, value) -> None:
        self.data[key] = value


def test_manager_detects_installed_files(tmp_path) -> None:
    (tmp_path / MODEL_FILENAME).write_bytes(b"model")
    runtime = tmp_path / "runtime"
    runtime.mkdir()
    (runtime / "llama-server.exe").write_bytes(b"server")

    manager = LocalAIManager(_Settings(tmp_path))

    assert manager.is_installed() is True
    assert manager.model_path == tmp_path / MODEL_FILENAME
    assert manager.server_path == runtime / "llama-server.exe"


def test_manager_rejects_empty_install_path(tmp_path) -> None:
    manager = LocalAIManager(_Settings(tmp_path))
    with pytest.raises(ValueError, match="请选择保存位置"):
        manager.set_install_dir("  ")


def test_safe_extract_rejects_parent_path(tmp_path) -> None:
    archive = tmp_path / "bad.zip"
    with zipfile.ZipFile(archive, "w") as zipped:
        zipped.writestr("../outside.txt", "bad")

    with pytest.raises(RuntimeError, match="不安全路径"):
        InstallWorker._safe_extract(archive, tmp_path / "runtime")


def test_install_runtime_prefers_builtin_archive(tmp_path, monkeypatch) -> None:
    archive = tmp_path / "builtin.zip"
    with zipfile.ZipFile(archive, "w") as zipped:
        zipped.writestr("llama-server.exe", "server")
    monkeypatch.setattr(
        "app.features.ai_voice.local_runtime.BUILTIN_RUNTIME_ARCHIVE", archive
    )

    def fail_get(*args, **kwargs):
        raise AssertionError("内置运行时存在时不应访问网络")

    monkeypatch.setattr("app.features.ai_voice.local_runtime.httpx.get", fail_get)
    worker = InstallWorker(tmp_path / "install")
    worker.install_dir.mkdir()

    worker._install_runtime()

    assert (worker.install_dir / "runtime" / "llama-server.exe").is_file()


def test_health_check_ignores_system_proxy(tmp_path, monkeypatch) -> None:
    captured = {}

    class _Response:
        status_code = 200

    def fake_get(url, **kwargs):
        captured["url"] = url
        captured.update(kwargs)
        return _Response()

    monkeypatch.setattr("app.features.ai_voice.local_runtime.httpx.get", fake_get)

    assert LocalAIManager(_Settings(tmp_path)).is_running() is True
    assert captured["trust_env"] is False

def test_llamacpp_backend_uses_openai_compatible_endpoint(monkeypatch) -> None:
    captured = {}

    class _Response:
        def raise_for_status(self) -> None:
            return None

        def json(self):
            return {"choices": [{"message": {"content": "hello"}}]}

    def fake_post(url, **kwargs):
        captured["url"] = url
        captured.update(kwargs)
        return _Response()

    monkeypatch.setattr("app.features.ai_voice.ai_client.httpx.post", fake_post)
    backend = LlamaCppBackend("http://127.0.0.1:11435")

    result = backend.chat([ChatMessage(role="user", content="你好")], timeout=20)

    assert result == "hello"
    assert captured["url"] == "http://127.0.0.1:11435/v1/chat/completions"
    assert captured["trust_env"] is False