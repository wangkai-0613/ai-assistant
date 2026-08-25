"""语音输入（第二优先级）：基于 Windows 自带 SAPI 的本地语音识别。

不联网、不下载模型，天然符合“AI 优先本地部署”的取向。未安装 pywin32
或非 Windows 环境时 `available` 为 False，调用方应据此禁用麦克风按钮，
而不是让识别失败导致程序崩溃。
"""

from __future__ import annotations

import time
from collections.abc import Callable


class VoiceInputUnavailable(Exception):
    """语音识别不可用或识别过程中出现异常。"""


class VoiceRecognizer:
    def __init__(self) -> None:
        self._available = self._check_available()

    @staticmethod
    def _check_available() -> bool:
        try:
            import pythoncom  # noqa: F401
            import win32com.client  # noqa: F401
        except ImportError:
            return False
        return True

    @property
    def available(self) -> bool:
        return self._available

    def listen(self, should_stop: Callable[[], bool], max_seconds: float = 30.0) -> str:
        """持续监听直到 `should_stop()` 返回 True 或超过 `max_seconds`。

        返回识别到的文字（可能为空字符串）。任何底层异常都转换成
        `VoiceInputUnavailable`，调用方无需关心 COM/SAPI 细节。
        """
        if not self._available:
            raise VoiceInputUnavailable(
                "未安装 pywin32，无法使用本地语音识别（pip install pywin32）"
            )

        import pythoncom
        import win32com.client

        phrases: list[str] = []

        class _RecoEventSink:
            def OnRecognition(self, _stream_number, _stream_position, _recognition_type, result):
                try:
                    reco_result = win32com.client.Dispatch(result)
                    phrase = reco_result.PhraseInfo.GetText()
                    if phrase:
                        phrases.append(phrase)
                except Exception:  # noqa: BLE001, S110 - COM 回调，任何异常都不能向上抛出
                    pass

        try:
            recognizer = win32com.client.Dispatch("SAPI.SpSharedRecognizer")
            context = recognizer.CreateRecoContext()
            grammar = context.CreateGrammar()
            grammar.DictationSetState(1)
            win32com.client.WithEvents(context, _RecoEventSink)

            deadline = time.time() + max_seconds
            while time.time() < deadline and not should_stop():
                pythoncom.PumpWaitingMessages()
                time.sleep(0.05)

            grammar.DictationSetState(0)
        except Exception as exc:
            raise VoiceInputUnavailable(f"本地语音识别不可用：{exc}") from exc

        return "".join(phrases).strip()
