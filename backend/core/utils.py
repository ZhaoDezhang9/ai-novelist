"""共享工具函数"""
import re
import json
import logging

logger = logging.getLogger(__name__)


def extract_json(text: str) -> str:
    """从LLM返回文本中提取JSON（对象或数组）——返回最长的括号匹配结果"""
    text = text.strip()
    m = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', text, re.DOTALL)
    if m:
        text = m.group(1).strip()
    text = text.strip()
    # 尝试两种括号，返回最长的匹配——这样数组[{...}]返回数组，对象{"arr":[...]}返回对象
    best = ""
    for start, end in [("{", "}"), ("[", "]")]:
        idx = text.find(start)
        if idx != -1:
            depth = 0
            for i, ch in enumerate(text[idx:], idx):
                if ch == start:
                    depth += 1
                elif ch == end:
                    depth -= 1
                    if depth == 0:
                        candidate = text[idx:i+1]
                        if len(candidate) > len(best):
                            best = candidate
                        break
    return best or text


def repair_json(raw: str) -> str:
    """修复常见 LLM JSON 输出问题：尾部逗号、单引号、代码块包裹"""
    text = raw.strip()
    m = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', text, re.DOTALL)
    if m:
        text = m.group(1).strip()
    # 找到最外层 JSON，对象优先于数组
    for bracket in ('{', '['):
        start = text.find(bracket)
        if start != -1:
            depth = 0
            close = '}' if bracket == '{' else ']'
            for i, ch in enumerate(text[start:], start):
                if ch == bracket:
                    depth += 1
                elif ch == close:
                    depth -= 1
                    if depth == 0:
                        end = i + 1
                        break
            text = text[start:end]
            break
    text = re.sub(r',\s*([}\]])', r'\1', text)  # 尾部逗号
    text = re.sub(r"'", '"', text)               # 单引号 → 双引号
    return text


def parse_llm_json(raw: str) -> dict | list:
    """解析 LLM 返回的 JSON，三层回退：标准提取 → 修复 → 提取数组首元素"""
    try:
        return json.loads(extract_json(raw))
    except json.JSONDecodeError:
        pass
    try:
        return json.loads(repair_json(raw))
    except (json.JSONDecodeError, ValueError) as e:
        logger.warning(f"LLM JSON解析失败: {e}\nraw={raw[:300]}")
        raise
