"""1号模块：语音播报。

Windows 下调用系统自带 SAPI 引擎朗读，不引入新依赖；
其他平台或播报失败时静默降级，绝不影响提醒主流程。
"""

from __future__ import annotations

import os
import subprocess

_MAX_LENGTH = 200


def speak(text: str) -> bool:
    """后台朗读文本，返回是否成功启动播报。失败不抛异常。"""
    text = (text or "").strip()[:_MAX_LENGTH]
    if not text or os.name != "nt":
        return False
    escaped = text.replace('"', '`"')
    script = (
        "Add-Type -AssemblyName System.Speech; "
        f'(New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak("{escaped}")'
    )
    try:
        subprocess.Popen(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        return True
    except OSError:
        return False
