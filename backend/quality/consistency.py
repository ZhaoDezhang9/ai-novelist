"""一致性检查器 - L1/L2/L3 三层防幻觉检测"""
import json
from backend.core.models import Story, ChapterRecord, CheckResult
from backend.core.llm_client import fast_llm
from backend.core.utils import extract_json
from backend.generation.prompt_templates import (
    CONSISTENCY_CHECK_L1, CONSISTENCY_CHECK_L2, CONSISTENCY_CHECK_L3,
)


class ConsistencyChecker:
    def __init__(self):
        pass

    async def check_l1_self(self, chapter: ChapterRecord) -> CheckResult:
        """L1: 章节自身一致性（时间、空间、角色、道具）"""
        user = f"请检查以下章节的自身一致性：\n\n{chapter.content[:6000]}"
        try:
            raw = await fast_llm.chat(CONSISTENCY_CHECK_L1, user, temperature=0.2, max_tokens=1000)
            data = json.loads(extract_json(raw))
            return CheckResult(
                passed=data.get("passed", True),
                layer="L1",
                issues=data.get("issues", []),
                scores={"self_consistency": 1.0 if data.get("passed") else 0.5},
            )
        except Exception as e:
            return CheckResult(passed=False, layer="L1", issues=[{
                "type": "check_error", "severity": "high",
                "description": f"L1检查异常: {e}",
            }])

    async def check_l2_cross(self, story: Story, chapter: ChapterRecord, hot_memory) -> CheckResult:
        """L2: 跨章一致性（与前文比对）"""
        # 构建上下文
        prev_chapters = hot_memory.recent_chapters if hot_memory else []
        prev_text = "\n".join([
            f"第{ch.get('number', '?')}章：{ch.get('content', '')[:500]}"
            for ch in prev_chapters
        ])

        context = f"【角色设定】\n{json.dumps(story.characters[:3], ensure_ascii=False)}\n\n【前文】\n{prev_text}"
        system = CONSISTENCY_CHECK_L2.format(context=context)
        user = f"请检查以下章节与前文的一致性：\n\n{chapter.content[:5000]}"

        try:
            raw = await fast_llm.chat(system, user, temperature=0.2, max_tokens=1000)
            data = json.loads(extract_json(raw))
            return CheckResult(
                passed=data.get("passed", True),
                layer="L2",
                issues=data.get("issues", []),
                scores={"cross_consistency": 1.0 if data.get("passed") else 0.5},
            )
        except Exception as e:
            return CheckResult(passed=False, layer="L2", issues=[{
                "type": "check_error", "severity": "high",
                "description": f"L2检查异常: {e}",
            }])

    async def check_l3_world_rules(self, story: Story, chapter: ChapterRecord) -> CheckResult:
        """L3: 世界观铁律合规检查"""
        rules = story.world_bible.rules
        if not rules:
            return CheckResult(passed=True, layer="L3", issues=[], scores={"world_compliance": 1.0})

        world_rules = "\n".join(f"- {r}" for r in rules)
        system = CONSISTENCY_CHECK_L3.format(world_rules=world_rules)
        user = f"请检查以下章节是否违反世界观规则：\n\n{chapter.content[:6000]}"

        try:
            raw = await fast_llm.chat(system, user, temperature=0.2, max_tokens=1000)
            data = json.loads(extract_json(raw))
            return CheckResult(
                passed=data.get("passed", True),
                layer="L3",
                issues=data.get("violations", data.get("issues", [])),
                scores={"world_compliance": 1.0 if data.get("passed") else 0.3},
            )
        except Exception as e:
            return CheckResult(passed=False, layer="L3", issues=[{
                "type": "check_error", "severity": "high",
                "description": f"L3检查异常: {e}",
            }])

    async def run_all(self, story: Story, chapter: ChapterRecord, hot_memory=None) -> list[CheckResult]:
        """运行全部三层检查"""
        l1 = await self.check_l1_self(chapter)
        l2 = await self.check_l2_cross(story, chapter, hot_memory)
        l3 = await self.check_l3_world_rules(story, chapter)
        return [l1, l2, l3]


