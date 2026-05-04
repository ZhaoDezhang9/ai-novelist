"""共享工具函数"""
import re


def extract_json(text: str) -> str:
    """从LLM返回文本中提取JSON（对象或数组）"""
    text = text.strip()
    m = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', text, re.DOTALL)
    if m:
        text = m.group(1).strip()
    text = text.strip()
    for start, end in [("[", "]"), ("{", "}")]:
        idx = text.find(start)
        if idx != -1:
            depth = 0
            for i, ch in enumerate(text[idx:], idx):
                if ch == start:
                    depth += 1
                elif ch == end:
                    depth -= 1
                    if depth == 0:
                        return text[idx:i+1]
    return text
