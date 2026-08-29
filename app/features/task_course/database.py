"""1号模块：SQLite 数据库访问。

任务与课表共用同一个本地数据库文件，默认位于
用户主目录下 .xiao_assistant/assistant.db（不入库）。
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

_SCHEMA = """
CREATE TABLE IF NOT EXISTS tasks (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    due_at TEXT NOT NULL,
    completed INTEGER NOT NULL DEFAULT 0,
    category TEXT NOT NULL DEFAULT '任务'
);

CREATE TABLE IF NOT EXISTS courses (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    weekday INTEGER NOT NULL,
    start_time TEXT NOT NULL,
    end_time TEXT NOT NULL DEFAULT '',
    room TEXT NOT NULL DEFAULT '',
    course_date TEXT
);
"""


def default_db_path() -> Path:
    """默认数据库路径，所在目录不存在时自动创建。"""
    path = Path.home() / ".xiao_assistant"
    path.mkdir(parents=True, exist_ok=True)
    return path / "assistant.db"


def connect(path: Path | None = None) -> sqlite3.Connection:
    """打开连接并保证表结构存在。"""
    conn = sqlite3.connect(path or default_db_path())
    conn.row_factory = sqlite3.Row
    conn.executescript(_SCHEMA)
    columns = {row["name"] for row in conn.execute("PRAGMA table_info(courses)")}
    if "course_date" not in columns:
        conn.execute("ALTER TABLE courses ADD COLUMN course_date TEXT")
        conn.commit()
    return conn
