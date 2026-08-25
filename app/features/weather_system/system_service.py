"""3号模块：系统状态服务。

使用 psutil 读取内存、磁盘（和可选 CPU）状态，返回公共 SystemSummary。
"""

from __future__ import annotations

import psutil

from app.core.contracts import SystemSummary


class SystemService:
    def snapshot(self, with_cpu: bool = False) -> SystemSummary:
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage(psutil.disk_partitions()[0].mountpoint)
        cpu = psutil.cpu_percent(interval=0.1) if with_cpu else None
        return SystemSummary(
            memory_percent=memory.percent,
            disk_percent=disk.percent,
            cpu_percent=cpu,
        )