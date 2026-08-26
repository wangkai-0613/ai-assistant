"""不依赖任何 AI 后端的离线任务解析兜底方案。

当本地模型（Ollama）和云端 OpenRouter 都不可用时，仍然需要保证
demo.py 中“明天下午三点提醒我交报告”这类请求可以被解析成 TaskDraft，
因此这里用规则/正则实现一个简化版中文时间解析器。
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta

from app.core.contracts import TaskDraft

_CN_NUM = {
    "零": 0, "一": 1, "二": 2, "两": 2, "三": 3, "四": 4,
    "五": 5, "六": 6, "七": 7, "八": 8, "九": 9, "十": 10,
}

_DAY_OFFSETS = {
    "大后天": 3,
    "后天": 2,
    "明天": 1,
    "明日": 1,
    "今天": 0,
    "今日": 0,
}

_TIME_PATTERN = re.compile(
    r"(?P<period>凌晨|早上|早晨|上午|中午|下午|晚上|傍晚)?"
    r"(?P<hour>[0-9]{1,2}|[一二两三四五六七八九十]{1,3})"
    r"[点:：]"
    r"(?P<minute>[0-9]{1,2}|半|一刻|三刻)?"
)

_TRIGGER_WORDS = (
    "提醒我", "提醒", "记得", "别忘了", "帮我添加", "添加任务", "新建任务", "安排",
)

_STRIP_WORDS = _TRIGGER_WORDS + ("，", ",", "。", "!", "！")


def _cn_to_int(raw: str) -> int | None:
    if raw.isdigit():
        return int(raw)
    if raw == "十":
        return 10
    if len(raw) == 2 and raw[0] == "十":
        digit = _CN_NUM.get(raw[1])
        return 10 + digit if digit is not None else None
    if len(raw) == 2 and raw[1] == "十":
        digit = _CN_NUM.get(raw[0])
        return digit * 10 if digit is not None else None
    if len(raw) == 3 and raw[1] == "十":
        tens = _CN_NUM.get(raw[0])
        ones = _CN_NUM.get(raw[2])
        if tens is not None and ones is not None:
            return tens * 10 + ones
    return _CN_NUM.get(raw)


def _parse_time_part(text: str, base_date: datetime) -> datetime | None:
    match = _TIME_PATTERN.search(text)
    if not match:
        return None

    hour = _cn_to_int(match.group("hour"))
    if hour is None:
        return None

    period = match.group("period")
    if period in ("下午", "晚上", "傍晚") and hour < 12:
        hour += 12
    elif period in ("凌晨", "早上", "早晨", "上午") and hour == 12:
        hour = 0

    minute_raw = match.group("minute")
    if minute_raw is None:
        minute = 0
    elif minute_raw == "半":
        minute = 30
    elif minute_raw == "一刻":
        minute = 15
    elif minute_raw == "三刻":
        minute = 45
    else:
        minute = int(minute_raw)

    hour = max(0, min(hour, 23))
    minute = max(0, min(minute, 59))
    return base_date.replace(hour=hour, minute=minute, second=0, microsecond=0)


def _extract_title(text: str, matched_day_token: str | None) -> str:
    cleaned = text
    if matched_day_token:
        cleaned = cleaned.replace(matched_day_token, "")
    cleaned = _TIME_PATTERN.sub("", cleaned)
    for word in _STRIP_WORDS:
        cleaned = cleaned.replace(word, "")
    cleaned = cleaned.strip()
    return cleaned or "未命名任务"


def looks_like_task_request(text: str) -> bool:
    """粗略判断这句话是否像是在请求创建提醒/任务。"""
    return any(word in text for word in _TRIGGER_WORDS)


def fallback_parse_task(text: str, now: datetime) -> TaskDraft | None:
    """离线规则解析。解析失败返回 None，调用方应转为普通聊天处理。"""
    matched_day_token = None
    day_offset = 0
    for token, offset in _DAY_OFFSETS.items():
        if token in text:
            matched_day_token = token
            day_offset = offset
            break

    base_date = now + timedelta(days=day_offset)
    due_at = _parse_time_part(text, base_date)
    if due_at is None:
        return None

    if due_at <= now and matched_day_token is None:
        due_at += timedelta(days=1)

    title = _extract_title(text, matched_day_token)
    return TaskDraft(title=title, due_at=due_at, category="任务", confidence=0.5)
