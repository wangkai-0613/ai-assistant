"""3号模块：开机自启服务。

Windows 下通过 HKCU Run 注册表实现开机自启，无需管理员权限。
非 Windows 平台返回 False 且操作静默无效。
"""

from __future__ import annotations

import sys
from pathlib import Path

_APP_NAME = "XiaoAssist"
_RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"


def _is_windows() -> bool:
    return sys.platform == "win32"


class AutoStartService:
    def is_enabled(self) -> bool:
        if not _is_windows():
            return False
        try:
            import winreg

            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _RUN_KEY) as key:
                winreg.QueryValueEx(key, _APP_NAME)
                return True
        except OSError:
            return False

    def set_enabled(self, enabled: bool) -> None:
        if not _is_windows():
            return
        import winreg

        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, _RUN_KEY) as key:
            if enabled:
                winreg.SetValueEx(key, _APP_NAME, 0, winreg.REG_SZ, self._command())
            else:
                try:
                    winreg.DeleteValue(key, _APP_NAME)
                except FileNotFoundError:
                    pass

    @staticmethod
    def _command() -> str:
        python_exe = Path(sys.executable)
        pythonw = python_exe.with_name("pythonw.exe")
        launcher = pythonw if pythonw.exists() else python_exe
        main = Path(__file__).resolve().parents[3] / "main.py"
        return f'"{launcher}" "{main}"'