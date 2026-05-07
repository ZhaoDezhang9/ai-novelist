"""增量改写引擎 - 精准定位问题段落，单次调用批量改写"""
import re
from backend.core.models import ChapterRecord
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
        """针对具体问题的增量改写（单次LLM调用批量修复所有问题）"""
        if not issues:
            return chapter

        sorted_issues = sorted(issues, key=lambda x: {
            "critical": 4, "high": 3, "medium": 2, "low": 1,
        }.get(x.get("severity", "low"), 1), reverse=True)
        top_issues = sorted_issues[:3]

        issues_text = "\n".join(
            f"{i+1}. [{issue.get('severity', 'medium')}] {issue.get('type', '')}: {issue.get('description', '')}"
            + (f" 建议：{issue.get('fix_suggestion', '')}" if issue.get('fix_suggestion') else "")
            for i, issue in enumerate(top_issues)
        )

        prompt = (
            f"【批量改写任务】\n"
            f"以下章节存在多个问题，请一次性修复所有问题，输出完整改写后的章节。\n\n"
            f"【问题列表】\n{issues_text}\n\n"
            f"【原文】\n{chapter.content}\n\n"
            f"【上下文约束】\n{context[:1500]}\n\n"
            f"【改写要求】\n"
            f"1. 修复上述所有问题\n"
            f"2. 不改变情节走向和角色设定\n"
            f"3. 保持原文风格和精彩表达\n"
            f"4. 修改后的文字要自然融入\n"
            f"5. 直接输出完整改写后的章节全文，不要解释"
        )

        try:
            rewritten = await fast_llm.chat(
                "你是一位精准的小说编辑。修复章节中的所有问题，保持情节不变。直接输出完整的改写后全文。",
                prompt,
                temperature=0.5,
                max_tokens=len(chapter.content) * 2,
            )
            if rewritten.strip() and len(rewritten.strip()) > len(chapter.content) * 0.3:
                chapter.content = rewritten.strip()
                chapter.word_count = self._count_words(rewritten.strip())
        except Exception:
            pass

        return chapter

    @staticmethod
    def _count_words(text: str) -> int:
        chinese = len(re.findall(r'[\u4e00-\u9fff\u3400-\u4dbf]', text))
        english = len(re.findall(r'[a-zA-Z]+', text))
        return chinese + english
