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

        # listen() 通常在 QThread/普通后台线程里执行，该线程没有默认的 COM
        # 单元套间，必须先 CoInitialize 才能创建/使用下面这些 COM 对象，
        # 否则每次都会报“尚未调用 CoInitialize”。
        pythoncom.CoInitialize()
        try:
            # 用进程内识别器（SpInprocRecognizer），不用共享识别器
            # （SpSharedRecognizer）：共享识别器的音频输入由系统统一管理，
            # 只有跑过 Windows “语音识别”设置向导才会有默认麦克风绑定，
            # 而且程序无法自己指定音频输入（尝试赋值会报 SAPI 错误
            # 0x8004505F/SPERR_NOT_SUPPORTED_FOR_SHARED_RECOGNIZER）——
            # 这台机器从未跑过向导时，共享识别器完全收不到任何声音，
            # 麦克风本身正常也无济于事。进程内识别器由本进程私有，
            # 允许显式绑定默认多媒体输入设备。
            recognizer = win32com.client.Dispatch("SAPI.SpInprocRecognizer")
            recognizer.AudioInputStream = win32com.client.Dispatch("SAPI.SpMMAudioIn")
            context = recognizer.CreateRecoContext()
            grammar = context.CreateGrammar()
            grammar.DictationSetState(1)
            win32com.client.WithEvents(context, _RecoEventSink)

            deadline = time.time() + max_seconds
            while time.time() < deadline and not should_stop():
                pythoncom.PumpWaitingMessages()
                time.sleep(0.05)

            # 用户刚说完就点“停止”时，SAPI 可能还没有把最后一句的静音
            # 断点识别完；停止前多泵一会儿消息循环，给最后一句收尾的机会。
            grace_deadline = time.time() + 1.5
            while time.time() < grace_deadline:
                pythoncom.PumpWaitingMessages()
                time.sleep(0.05)

            grammar.DictationSetState(0)
        except Exception as exc:
            raise VoiceInputUnavailable(f"本地语音识别不可用：{exc}") from exc
        finally:
            pythoncom.CoUninitialize()

        return "".join(phrases).strip()
