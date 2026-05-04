"""章节写作引擎 - 流式写章节 + 字数控制"""
import asyncio
import logging
from typing import AsyncGenerator, Optional
from datetime import datetime

from backend.core.models import Story, ChapterRecord, ChapterStatus
from backend.core.llm_client import main_llm
from backend.generation.prompt_templates import chapter_writing_user


logger = logging.getLogger(__name__)


class ChapterWriter:
    def __init__(self):
        pass

    async def write_draft(
        self,
        story,
        chapter_number: int,
        context: str,
        temperature: Optional[float] = None,
    ) -> ChapterRecord:
        """写一章完整草稿"""
        outline_node = story.outline[chapter_number - 1] if chapter_number - 1 < len(story.outline) else {}
        user_prompt = chapter_writing_user(story, chapter_number, outline_node)

        content = await main_llm.chat(
            system_prompt=context,
            user_prompt=user_prompt,
            temperature=temperature or 0.88,
            max_tokens=story.config.words_per_chapter * 3,
        )

        title = self._generate_chapter_title(content[:500])
        word_count = self._count_words(content)

        return ChapterRecord(
            story_id=story.id,
            chapter_number=chapter_number,
            title=title,
            content=content,
            word_count=word_count,
            status=ChapterStatus.DRAFT,
            created_at=datetime.now().isoformat(),
        )

    async def write_draft_stream(
        self,
        story,
        chapter_number: int,
        context: str,
        temperature: Optional[float] = None,
    ) -> AsyncGenerator[dict, None]:
        """流式写章节"""
        outline_node = story.outline[chapter_number - 1] if chapter_number - 1 < len(story.outline) else {}
        user_prompt = chapter_writing_user(story, chapter_number, outline_node)

        content_chunks = []
        async for chunk in main_llm.chat_stream(
            system_prompt=context,
            user_prompt=user_prompt,
            temperature=temperature or 0.88,
            max_tokens=story.config.words_per_chapter * 3,
        ):
            content_chunks.append(chunk)
            yield {"type": "token", "data": chunk}

        content = "".join(content_chunks)
        title = self._generate_chapter_title(content[:500])
        word_count = self._count_words(content)

        yield {
            "type": "complete",
            "chapter": ChapterRecord(
                story_id=story.id,
                chapter_number=chapter_number,
                title=title,
                content=content,
                word_count=word_count,
                status=ChapterStatus.DRAFT,
                created_at=datetime.now().isoformat(),
            ).model_dump(),
        }

    def _generate_chapter_title(self, text: str) -> str:
        """从文本开头生成章节标题"""
        import re
        # 清理空格和换行
        first_line = text.strip().split("\n")[0]
        first_line = re.sub(r'^[第第]\d+[章節]', '', first_line).strip()
        # 取前12字
        title = first_line[:12].strip("，。！？…,;.!? \t")
        return title or "无题"

    @staticmethod
    def _count_words(text: str) -> int:
        """统计中文字数（汉字 + 英文单词）"""
        import re
        # 中文字符
        chinese = len(re.findall(r'[\u4e00-\u9fff\u3400-\u4dbf]', text))
        # 英文单词
        english = len(re.findall(r'[a-zA-Z]+', text))
        # 数字
        digits = len(re.findall(r'\d+', text))
        return chinese + english + digits
