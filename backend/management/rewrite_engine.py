"""增量改写引擎 - 精准定位问题段落，最小窗口改写"""
import re
from backend.core.models import Story, ChapterRecord, CheckResult
from backend.core.llm_client import fast_llm
from backend.core.config import get_settings


class RewriteEngine:
    def __init__(self):
        self.settings = get_settings()

    async def rewrite_targeted(
        self,
        chapter: ChapterRecord,
        issues: list[dict],
        context: str,
    ) -> ChapterRecord:
        """针对具体问题的增量改写"""
        if not issues:
            return chapter

        content = chapter.content
        fixed = content

        # 按严重程度排序
        sorted_issues = sorted(issues, key=lambda x: {
            "critical": 4, "high": 3, "medium": 2, "low": 1,
        }.get(x.get("severity", "low"), 1), reverse=True)

        for issue in sorted_issues[:3]:  # 最多改3个问题
            severity = issue.get("severity", "medium")
            desc = issue.get("description", "")
            suggestion = issue.get("suggestion", "")
            layer = issue.get("layer", "unknown")
            location = issue.get("location", "")

            # 定位改写窗口
            window = self._locate_rewrite_window(content, location)

            # 构造精准改写提示
            rewrite_prompt = self._build_rewrite_prompt(
                window=window,
                issue=desc,
                suggestion=suggestion,
                layer=layer,
                context=context,
            )

            # 改写窗口内容
            try:
                rewritten = await fast_llm.chat(
                    "你是一位精准的小说编辑。只改写需要修改的段落，保持其他内容完全不变。",
                    rewrite_prompt,
                    temperature=0.5,
                    max_tokens=len(window) * 3,
                )

                # 替换窗口内容
                if window in fixed:
                    fixed = fixed.replace(window, rewritten.strip())
                else:
                    # 模糊匹配替换
                    fixed = self._fuzzy_replace(fixed, window, rewritten.strip())

            except Exception:
                continue

        chapter.content = fixed
        chapter.word_count = self._count_words(fixed)
        return chapter

    def _locate_rewrite_window(self, content: str, location: str) -> str:
        """根据问题位置定位改写窗口"""
        window_size = self.settings.rewrite_window_lines

        # 按段落分割，找到问题区域
        paragraphs = content.split("\n\n")

        # 尝试数字定位（"第3段落" → 取索引2）
        numbers = re.findall(r'\d+', location)
        if numbers:
            idx = int(numbers[0]) - 1
            if 0 <= idx < len(paragraphs):
                # 取前后扩展的窗口
                start = max(0, idx - 1)
                end = min(len(paragraphs), idx + 2)
                return "\n\n".join(paragraphs[start:end])

        # 取中间偏后的内容（多数问题在冲突区）
        mid = len(content) // 2
        chars_per_line = 50
        start = max(0, mid - window_size * chars_per_line)
        end = min(len(content), mid + window_size * chars_per_line)
        return content[start:end]

    def _build_rewrite_prompt(
        self,
        window: str,
        issue: str,
        suggestion: str,
        layer: str,
        context: str,
    ) -> str:
        """构造精准改写提示"""
        return (
            f"【改写任务】\n"
            f"问题层级：{layer}\n"
            f"问题描述：{issue}\n"
            + (f"修改建议：{suggestion}\n" if suggestion else "")
            + f"\n"
            f"【原文段（仅这段需要修改）】\n"
            f"{window}\n\n"
            f"【上下文约束】\n"
            f"{context[:1000]}\n\n"
            f"【改写要求】\n"
            f"1. 只修改存在问题的段落，不改变情节走向\n"
            f"2. 保持原文的角色设定、世界观和风格\n"
            f"3. 修改后的文字要自然融入原文\n"
            f"4. 保留原文的精彩表达，只修问题部分\n"
            f"5. 直接输出修改后的完整段落，不要解释\n"
        )

    def _fuzzy_replace(self, text: str, old: str, new: str) -> str:
        """模糊匹配替换（处理微小差异）"""
        if old in text:
            return text.replace(old, new)

        # 尝试匹配第一句和最后一句
        old_lines = old.strip().split("\n")
        if not old_lines:
            return text

        first_line = old_lines[0].strip()[:30]
        last_line = old_lines[-1].strip()[:30]

        # 找包含首句和末句的区间
        idx_first = text.find(first_line)
        idx_last = text.rfind(last_line)

        if idx_first != -1 and idx_last != -1 and idx_last > idx_first:
            return text[:idx_first] + new.strip() + text[idx_last + len(last_line):]

        return text

    @staticmethod
    def _count_words(text: str) -> int:
        chinese = len(re.findall(r'[\u4e00-\u9fff\u3400-\u4dbf]', text))
        english = len(re.findall(r'[a-zA-Z]+', text))
        return chinese + english
