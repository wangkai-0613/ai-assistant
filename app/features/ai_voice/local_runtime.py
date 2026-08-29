"""本地 llama.cpp 模型的一键安装、启动和停止。"""

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import zipfile
from pathlib import Path

import httpx
from PySide6.QtCore import QObject, QThread, Signal

MODEL_FILENAME = "qwen2.5-7b-instruct-q3_k_m.gguf"
MODEL_SIZE = 3_808_391_072
MODEL_SHA256 = "a96b16179dc6cc9afdf0cf7a96a80c199cbd00b9be207c3465be21cb721cca5e"
MODEL_URL = (
    "https://www.modelscope.cn/models/qwen/Qwen2.5-7B-Instruct-GGUF/resolve/master/"
    + MODEL_FILENAME
)
LLAMA_RELEASE_API = "https://api.github.com/repos/ggml-org/llama.cpp/releases?per_page=5"
SERVER_PORT = 11435
SERVER_URL = f"http://127.0.0.1:{SERVER_PORT}"
BUILTIN_RUNTIME_ARCHIVE = (
    Path(__file__).resolve().parents[2] / "resources" / "llama-runtime-win-cpu-x64.zip"
)


def default_install_dir() -> Path:
    return Path.home() / ".xiao_assistant" / "local_ai"


class InstallWorker(QThread):
    progress = Signal(int)
    status = Signal(str)
    completed = Signal(bool, str)

    def __init__(self, install_dir: Path) -> None:
        super().__init__()
        self.install_dir = install_dir
        self._cancelled = False

    def cancel(self) -> None:
        self._cancelled = True

    def run(self) -> None:
        try:
            self.install_dir.mkdir(parents=True, exist_ok=True)
            self._install_runtime()
            self._download_model()
        except Exception as exc:  # noqa: BLE001 - error is reported to the UI
            self.completed.emit(False, str(exc))
            return
        if self._cancelled:
            self.completed.emit(False, "下载已取消，可稍后继续")
        else:
            self.progress.emit(100)
            self.completed.emit(True, "本地 AI 安装完成")

    def _install_runtime(self) -> None:
        if next(self.install_dir.rglob("llama-server.exe"), None) is not None:
            return
        runtime_dir = self.install_dir / "runtime"
        runtime_dir.mkdir(exist_ok=True)
        if BUILTIN_RUNTIME_ARCHIVE.is_file():
            self.status.emit("正在安装内置本地 AI 运行程序…")
            self._safe_extract(BUILTIN_RUNTIME_ARCHIVE, runtime_dir)
            self._validate_runtime(runtime_dir)
            return

        self.status.emit("未找到内置运行程序，正在从网络下载…")
        runtime_url = os.environ.get("LLAMA_RUNTIME_URL", "").strip()
        if not runtime_url:
            response = httpx.get(LLAMA_RELEASE_API, timeout=30, follow_redirects=True)
            response.raise_for_status()
            releases = response.json()
            runtime_url = next(
                (
                    item["browser_download_url"]
                    for release in releases
                    for item in release.get("assets", [])
                    if item.get("name", "").endswith("bin-win-cpu-x64.zip")
                ),
                "",
            )
        if not runtime_url:
            raise RuntimeError("没有找到适用于 Windows 的 llama.cpp 运行程序")

        archive = self.install_dir / "llama-runtime.zip.part"
        self._download(runtime_url, archive, progress_start=0, progress_span=3)
        if self._cancelled:
            return
        final_archive = archive.with_suffix("")
        archive.replace(final_archive)
        self._safe_extract(final_archive, runtime_dir)
        final_archive.unlink(missing_ok=True)
        self._validate_runtime(runtime_dir)

    @staticmethod
    def _validate_runtime(runtime_dir: Path) -> None:
        if next(runtime_dir.rglob("llama-server.exe"), None) is None:
            raise RuntimeError("运行程序压缩包中缺少 llama-server.exe")

    def _download_model(self) -> None:
        model_path = self.install_dir / MODEL_FILENAME
        if model_path.exists() and self._sha256(model_path) == MODEL_SHA256:
            self.progress.emit(100)
            return
        self.status.emit("正在从国内魔搭社区下载通义千问模型（约 3.8GB）…")
        part_path = model_path.with_suffix(model_path.suffix + ".part")
        if part_path.exists() and part_path.stat().st_size == MODEL_SIZE:
            if self._sha256(part_path) == MODEL_SHA256:
                part_path.replace(model_path)
                self.progress.emit(100)
                return
            part_path.unlink()
        self._download(
            MODEL_URL,
            part_path,
            progress_start=3,
            progress_span=94,
            expected_total=MODEL_SIZE,
        )
        if self._cancelled:
            return
        self.status.emit("正在校验模型完整性…")
        if self._sha256(part_path) != MODEL_SHA256:
            part_path.unlink(missing_ok=True)
            raise RuntimeError("模型校验失败，请重新下载")
        part_path.replace(model_path)

    def _download(
        self,
        url: str,
        destination: Path,
        progress_start: int,
        progress_span: int,
        expected_total: int | None = None,
    ) -> None:
        existing = destination.stat().st_size if destination.exists() else 0
        headers = {"Range": f"bytes={existing}-"} if existing else {}
        with httpx.stream(
            "GET", url, headers=headers, timeout=httpx.Timeout(30, read=120), follow_redirects=True
        ) as response:
            response.raise_for_status()
            if existing and response.status_code != 206:
                existing = 0
                destination.unlink(missing_ok=True)
            remaining = int(response.headers.get("content-length", "0") or 0)
            total = expected_total or (existing + remaining)
            mode = "ab" if existing else "wb"
            downloaded = existing
            with destination.open(mode) as output:
                for chunk in response.iter_bytes(1024 * 1024):
                    if self._cancelled:
                        return
                    output.write(chunk)
                    downloaded += len(chunk)
                    if total:
                        fraction = min(downloaded / total, 1.0)
                        self.progress.emit(progress_start + int(fraction * progress_span))

    @staticmethod
    def _sha256(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as source:
            for chunk in iter(lambda: source.read(4 * 1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    @staticmethod
    def _safe_extract(archive: Path, destination: Path) -> None:
        root = destination.resolve()
        with zipfile.ZipFile(archive) as zipped:
            for member in zipped.infolist():
                target = (destination / member.filename).resolve()
                if root not in target.parents and target != root:
                    raise RuntimeError("运行程序压缩包包含不安全路径")
            zipped.extractall(destination)


class LocalAIManager(QObject):
    progress = Signal(int)
    status_changed = Signal(str)
    install_finished = Signal(bool, str)

    def __init__(self, settings) -> None:
        super().__init__()
        configured = str(settings.get("local_ai_dir", "")).strip()
        self.install_dir = Path(configured) if configured else default_install_dir()
        self.settings = settings
        self._worker: InstallWorker | None = None
        self._process: subprocess.Popen | None = None
        self._log_handle = None

    @property
    def model_path(self) -> Path:
        return self.install_dir / MODEL_FILENAME

    @property
    def server_path(self) -> Path | None:
        return next(self.install_dir.rglob("llama-server.exe"), None)

    def is_installed(self) -> bool:
        return self.model_path.exists() and self.server_path is not None

    def is_running(self) -> bool:
        if self._process is not None and self._process.poll() is None:
            return True
        try:
            return httpx.get(
                f"{SERVER_URL}/health", timeout=0.5, trust_env=False
            ).status_code == 200
        except httpx.HTTPError:
            return False

    def set_install_dir(self, path: str) -> None:
        if not path.strip():
            raise ValueError("请选择保存位置")
        if self._worker is not None and self._worker.isRunning():
            raise RuntimeError("下载过程中不能更改保存位置")
        self.install_dir = Path(path).expanduser().resolve()
        self.settings.set("local_ai_dir", str(self.install_dir))

    def install(self) -> None:
        if self._worker is not None and self._worker.isRunning():
            return
        probe = self.install_dir
        while not probe.exists() and probe != probe.parent:
            probe = probe.parent
        usage = shutil.disk_usage(probe if probe.exists() else Path.home())
        if usage.free < 5 * 1024**3:
            self.install_finished.emit(False, "可用空间不足，需要至少 5GB")
            return
        self.settings.set("local_ai_dir", str(self.install_dir))
        self._worker = InstallWorker(self.install_dir)
        self._worker.progress.connect(self.progress)
        self._worker.status.connect(self.status_changed)
        self._worker.completed.connect(self._on_install_complete)
        self._worker.start()

    def cancel_install(self) -> None:
        if self._worker is not None:
            self._worker.cancel()

    def start(self) -> bool:
        if self.is_running():
            return True
        server = self.server_path
        if server is None or not self.model_path.exists():
            return False
        log_path = self.install_dir / "llama-server.log"
        self._log_handle = log_path.open("a", encoding="utf-8")
        flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        self._process = subprocess.Popen(
            [
                str(server),
                "-m",
                str(self.model_path),
                "--host",
                "127.0.0.1",
                "--port",
                str(SERVER_PORT),
                "-c",
                "4096",
                "-ngl",
                "0",
            ],
            cwd=server.parent,
            stdout=self._log_handle,
            stderr=subprocess.STDOUT,
            creationflags=flags,
        )
        self.status_changed.emit("本地 AI 正在启动…")
        return True

    def stop(self) -> None:
        if self._worker is not None and self._worker.isRunning():
            self._worker.cancel()
            self._worker.wait(3000)
        if self._process is not None and self._process.poll() is None:
            self._process.terminate()
            try:
                self._process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._process.kill()
        self._process = None
        if self._log_handle is not None:
            self._log_handle.close()
            self._log_handle = None

    def _on_install_complete(self, success: bool, message: str) -> None:
        if success:
            self.start()
        self.install_finished.emit(success, message)
