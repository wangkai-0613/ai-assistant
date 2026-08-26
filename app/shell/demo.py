"""4号模块独立演示：程序外壳、导航、托盘与桌宠。

用法：
    python -m app.shell.demo

演示内容：
    - 主窗口、左侧导航和页面容器
    - 首页卡片布局与小猫展示
    - 占位页（功能模块未完成时）
    - 系统托盘：关闭隐藏、右键菜单、双击恢复
    - 桌宠小猫：鼠标悬停弹出功能菜单，可拖拽，点击功能跳转页面
"""

import sys

from PySide6.QtWidgets import QApplication

from app.core.app_context import AppContext
from app.core.events import AppEvents
from app.shell.floating_entry import DesktopPet
from app.shell.main_window import MainWindow


def main() -> int:
    app = QApplication.instance() or QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    window = MainWindow(AppContext(events=AppEvents()))

    pet = DesktopPet()
    pet.move(100, 100)

    def on_navigate(index: int):
        window._navigate_to(index)
        window.showNormal()
        window.activateWindow()
        window.raise_()

    pet.popup.navigate.connect(on_navigate)

    window.statusBar().showMessage("就绪 — 关闭窗口将隐藏到系统托盘，桌宠小猫在桌面等你")

    window.show()
    pet.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())