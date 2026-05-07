"""Pydantic validators — 防注入 + 输入清理"""
import re

INJECTION_PATTERN = re.compile(r"[<>{}();`'\"\\]|--|/\*|\*/|script|onerror|onload", re.IGNORECASE)
MAX_TEXT_LENGTH = 5000


def validate_no_injection(v: str) -> str:
    if INJECTION_PATTERN.search(v):
        raise ValueError("输入包含非法字符或模式")
    return v.strip()


def validate_length(v: str) -> str:
    if len(v) > MAX_TEXT_LENGTH:
        raise ValueError(f"输入长度不能超过 {MAX_TEXT_LENGTH} 字符")
    return v
