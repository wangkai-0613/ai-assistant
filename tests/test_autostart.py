import sys
from unittest.mock import MagicMock, patch

import pytest

from app.features.weather_system.autostart import AutoStartService


@pytest.fixture
def fake_winreg():
    mock = MagicMock()
    with patch.dict(sys.modules, {"winreg": mock}):
        yield mock


@patch("app.features.weather_system.autostart.sys.platform", "win32")
def test_command_contains_python_and_main() -> None:
    command = AutoStartService._command()
    assert "main.py" in command
    assert command.startswith('"')


@patch("app.features.weather_system.autostart.sys.platform", "win32")
def test_is_enabled_reads_registry(fake_winreg) -> None:
    fake_winreg.OpenKey.return_value = MagicMock()
    service = AutoStartService()

    assert service.is_enabled() is True


@patch("app.features.weather_system.autostart.sys.platform", "win32")
def test_is_enabled_false_when_key_missing(fake_winreg) -> None:
    fake_winreg.OpenKey.side_effect = OSError()
    service = AutoStartService()

    assert service.is_enabled() is False


@patch("app.features.weather_system.autostart.sys.platform", "win32")
def test_set_enabled_writes_value(fake_winreg) -> None:
    fake_winreg.CreateKey.return_value = MagicMock()
    service = AutoStartService()

    service.set_enabled(True)
    fake_winreg.SetValueEx.assert_called_once()


@patch("app.features.weather_system.autostart.sys.platform", "win32")
def test_set_disabled_deletes_value(fake_winreg) -> None:
    fake_winreg.CreateKey.return_value = MagicMock()
    service = AutoStartService()

    service.set_enabled(False)
    fake_winreg.DeleteValue.assert_called_once()


@patch("app.features.weather_system.autostart.sys.platform", "linux")
def test_non_windows_returns_false() -> None:
    service = AutoStartService()
    assert service.is_enabled() is False