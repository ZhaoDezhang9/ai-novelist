"""上下文构建器 - 组装最终写入LLM的提示词，集成语义搜索"""
import logging
import tiktoken
from backend.core.models import Story, HotMemory, WarmMemory, ColdMemory
from backend.core.config import get_settings
from backend.memory.vector_store import get_vector_store


logger = logging.getLogger(__name__)

# tiktoken编码器（懒加载）
_encoding = None


def _get_encoding():
    global _encoding
    if _encoding is None:
        try:
            _encoding = tiktoken.get_encoding("cl100k_base")
        except Exception:
            _encoding = tiktoken.get_encoding("o200k_base")
    return _encoding


class ContextBuilder:
    """将三级记忆组装为LLM可用的主提示词，语义搜索增强上下文检索"""

    def build_master_prompt(
        self,
        story: Story,
        hot_memory: HotMemory,
        warm_memory: WarmMemory,
        cold_memory: ColdMemory,
        semantic_context: dict | None = None,
    ) -> str:
        """构建完整的写作上下文（含语义搜索增强）"""
        cfg = story.config
        parts = []

        # === 创作身份 ===
        parts.append(
            f"你是一位{cfg.genre}类型的专业小说家，"
            f"写作风格为「{cfg.style}」，"
            f"用{cfg.pov}视角叙事。"
            f"目标读者：{cfg.target_audience}。"
            f"主题：{cfg.theme or '待定'}。"
        )

        # === 视角写作指导 ===
        pov_guide = self._get_pov_guide(cfg.pov)
        if pov_guide:
            parts.append(pov_guide)

        # === 世界观铁律（冷记忆 - 最重要，不可违反） ===
        wb = cold_memory.world_bible
        if wb.setting or wb.rules:
            rules_text = "【世界观铁律 - 永远不可违反】\n"
            if wb.setting:
                rules_text += f"世界观：{wb.setting}\n"
            if wb.rules:
                for i, rule in enumerate(wb.rules, 1):
                    rules_text += f"规则{i}：{rule}\n"
            if wb.factions:
                rules_text += f"势力：{', '.join(wb.factions)}\n"
            if wb.timeline:
                rules_text += "时间线：\n"
                for event, ch in wb.timeline.items():
                    rules_text += f"  - {event}（第{ch}章）\n"
            parts.append(rules_text)

        # === 语义搜索：相关世界规则 ===
        if semantic_context and semantic_context.get("relevant_rules"):
            rules = [r for r in semantic_context["relevant_rules"] if r.get("score", 0) > 0.7]
            if rules:
                sr_text = "【语义关联世界规则】\n"
                for r in rules[:3]:
                    sr_text += f"  • {r['rule']}\n"
                parts.append(sr_text)

        # === 角色卡（冷记忆） ===
        if cold_memory.character_cards:
            char_text = "【角色设定】\n"
            for c in cold_memory.character_cards:
                name = c.get("name", "未知")
                role = c.get("role", "")
                traits = c.get("traits", "")
                arc = c.get("arc", "")
                status = c.get("status", "")
                char_text += f"「{name}」{role}\n"
                if traits:
                    char_text += f"  性格：{traits}\n"
                if arc:
                    char_text += f"  弧光：{arc}\n"
                if status:
                    char_text += f"  当前状态：{status}\n"
            parts.append(char_text)

        # === 当前章大纲（热记忆） ===
        outline = hot_memory.current_outline
        if outline:
            parts.append(
                f"【本章写作要求 - 第{story.current_chapter + 1}章】\n"
                f"章节标题：{outline.get('title', '待定')}\n"
                f"核心目标：{outline.get('goal', '推进剧情')}\n"
                f"情节点：{', '.join(outline.get('plot_points', []))}\n"
                f"情绪基调：{outline.get('emotional_beat', '中性')}\n"
                f"关键角色：{', '.join(outline.get('key_characters', []))}\n"
                f"伏笔提示：{', '.join(outline.get('foreshadowing_seeds', []))}\n"
                f"转折提示：{outline.get('twist_note', '')}\n"
            )

        # === 语义搜索：相关历史章节 ===
        if semantic_context and semantic_context.get("relevant_chapters"):
            rel_chs = [c for c in semantic_context["relevant_chapters"] if c.get("score", 0) > 0.6]
            if rel_chs:
                rel_text = "【语义相关历史章节】\n"
                for c in rel_chs[:3]:
                    rel_text += f"  第{c.get('chapter', '?')}章（相关度{c.get('score', 0):.2f}）：{c.get('summary', '')}\n"
                parts.append(rel_text)

        # === 前文回顾（热记忆 + 温记忆） ===
        recent = hot_memory.recent_chapters
        summaries = warm_memory.recent_summaries
        if recent or summaries:
            recap = "【前文回顾】\n"
            if recent:
                for ch in recent:
                    recap += f"第{ch.get('number', '?')}章：{ch.get('summary', '')}\n"
            if summaries:
                for s in summaries:
                    recap += f"第{s.get('chapter', '?')}章：{s.get('summary', '')}\n"
            parts.append(recap)

        # === 角色当前状态（温记忆） ===
        char_states = warm_memory.character_states
        if char_states:
            state_text = "【角色当前状态】\n"
            for name, state in char_states.items():
                state_text += f"「{name}」→ {state.get('raw', '')}\n"
            parts.append(state_text)

        # === 待回收伏笔（温记忆） ===
        active_fs = warm_memory.active_foreshadowing
        if active_fs:
            fs_text = "【待回收伏笔 - 必须在合适时机回收】\n"
            for fs in active_fs:
                fs_text += f"伏笔（第{fs.get('planted_chapter', '?')}章）：{fs.get('description', '')}"
                if fs.get("min_payoff_chapter"):
                    fs_text += f" [最早第{fs['min_payoff_chapter']}章回收]"
                fs_text += "\n"
            parts.append(fs_text)

        # === 语义搜索：相关伏笔 ===
        if semantic_context and semantic_context.get("relevant_foreshadowing"):
            rel_fs = [f for f in semantic_context["relevant_foreshadowing"] if f.get("score", 0) > 0.6]
            if rel_fs:
                sfs_text = "【语义关联伏笔 - 可能需要回收】\n"
                for f in rel_fs[:3]:
                    sfs_text += f"  第{f.get('planted_chapter', '?')}章：{f.get('description', '')}\n"
                parts.append(sfs_text)

        # === 风格约束（冷记忆） ===
        sv = cold_memory.style_config
        style_text = (
            f"【风格约束】\n"
            f"  字数范围：{cfg.words_per_chapter}字左右\n"
            f"  平均句长：{sv.avg_sentence_length}字\n"
            f"  对话占比：{sv.dialogue_ratio * 100:.0f}%\n"
            f"  比喻密度：{sv.metaphor_density * 100:.1f}%（每百句）\n"
            f"  段落中位数：{sv.paragraph_length_median}句\n"
            f"  视角一致性：{'保持视角统一' if sv.perspective_consistency > 0.9 else '允许视角切换'}\n"
        )
        parts.append(style_text)

        # === 写作指令 ===
        parts.append(
            "【核心写作指令】\n"
            "1. 严格遵循世界观铁律，不可引入违反世界规则的设定\n"
            "2. 角色言行必须符合其性格和当前状态\n"
            "3. 保持与前文的时间和事件连续性\n"
            "4. 适当回收已有的伏笔（如有时机合适）\n"
            "5. 本章需要有一个出乎意料但合理的转折\n"
            "6. 确保情感节奏与大纲要求的情绪基调一致\n"
            "7. 避免陈词滥调，追求原创性表达\n"
            "8. 对话要符合人物性格，不自言自语\n"
            "9. 描写要具体、有画面感，避免抽象概述\n"
            "10. 结束时留有悬念或情感余韵\n"
        )

        # === 禁用模式 ===
        parts.append(
            "【禁止使用以下套路】\n"
            "• 禁止使用「突然」「忽然」开头连续两句\n"
            "• 禁止模板化桥段（退婚流、废柴觉醒、老爷爷传功等）\n"
            "• 禁止角色自言自语超过100字\n"
            "• 禁止连续三句以「他/她」开头\n"
            "• 禁止战斗场景中纯技能名堆砌\n"
            "• 禁止情感线进展过快（不符合角色性格）\n"
        )

        settings = get_settings()
        parts = self._truncate_context(parts, settings.max_context_tokens)

        return "\n\n".join(parts)

    async def build_semantic_context(self, story: Story, chapter_number: int) -> dict | None:
        """构建语义搜索上下文"""
        try:
            outline = story.outline[chapter_number - 1] if 0 <= chapter_number - 1 < len(story.outline) else {}
            query = f"{outline.get('goal', '')} {' '.join(outline.get('plot_points', []))} {' '.join(outline.get('key_characters', []))}"
            if not query.strip():
                query = f"第{chapter_number}章 {story.config.title}"
            vs = get_vector_store()
            return vs.search_relevant_context(story.id, query)
        except Exception as e:
            logger.warning(f"语义搜索失败: {e}")
            return None

    def _estimate_tokens(self, text: str) -> int:
        """使用 tiktoken 精确计算 token 数（替换启发式估算）"""
        try:
            enc = _get_encoding()
            return len(enc.encode(text))
        except Exception:
            # 回退到启发式估算
            chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
            other_chars = len(text) - chinese_chars
            return (chinese_chars // 2) + (other_chars // 4)

    def count_tokens(self, text: str) -> int:
        """公开的 token 计数方法（供其他模块使用）"""
        return self._estimate_tokens(text)

    def get_token_budget(self, chapter_content: str = "") -> dict:
        """返回当前章节的 token 预算使用情况"""
        settings = get_settings()
        used = self._estimate_tokens(chapter_content) if chapter_content else 0
        return {
            "max_context_tokens": settings.max_context_tokens,
            "used": used,
            "remaining": max(0, settings.max_context_tokens - used),
            "usage_pct": round(used / max(1, settings.max_context_tokens) * 100, 1),
        }

    def _truncate_context(self, parts: list[str], max_tokens: int) -> list[str]:
        total_tokens = sum(self._estimate_tokens(part) for part in parts)
        if total_tokens <= max_tokens:
            return parts

        logger.warning(f"上下文过长，开始截断: {total_tokens} > {max_tokens} tokens")

        for i, part in enumerate(parts):
            if "【前文回顾】" in part and "（全文见附件）" in part:
                continue
            elif "【前文回顾】" in part:
                lines = part.split('\n')
                if len(lines) > 3:
                    parts[i] = '\n'.join(lines[:3]) + "\n...（已截断较早章节）"
                    total_tokens = sum(self._estimate_tokens(p) for p in parts)
                    if total_tokens <= max_tokens:
                        return parts

        for i, part in enumerate(parts):
            if "【前文回顾】" in part:
                lines = part.split('\n')
                kept_lines = []
                chapter_count = 0
                for line in lines:
                    if line.startswith("第") and "章" in line:
                        chapter_count += 1
                        if chapter_count > 1:
                            continue
                    kept_lines.append(line)
                if len(kept_lines) < len(lines):
                    parts[i] = '\n'.join(kept_lines) + "\n...（已截断较早章节）"
                    total_tokens = sum(self._estimate_tokens(p) for p in parts)
                    if total_tokens <= max_tokens:
                        return parts

        for i, part in enumerate(parts):
            if "【角色当前状态】" in part:
                lines = part.split('\n')
                if len(lines) > 10:
                    parts[i] = '\n'.join(lines[:10]) + "\n...（已截断部分角色状态）"
                    total_tokens = sum(self._estimate_tokens(p) for p in parts)
                    if total_tokens <= max_tokens:
                        return parts

        logger.warning("上下文仍然过长，进行强制截断")
        truncated_parts = []
        remaining_tokens = max_tokens
        for part in parts:
            part_tokens = self._estimate_tokens(part)
            if part_tokens <= remaining_tokens:
                truncated_parts.append(part)
                remaining_tokens -= part_tokens
            else:
                chars_to_keep = int(len(part) * remaining_tokens / part_tokens)
                truncated_parts.append(part[:chars_to_keep] + "...（已截断）")
                break

        return truncated_parts

    def _get_pov_guide(self, pov) -> str:
        guides = {
            "第一人称": (
                "【视角规则 - 第一人称】\n"
                "1. 用「我」叙事，全程锁定主角视角\n"
                "2. 只能写主角感知到的事：看到的、听到的、想到的、感受到的\n"
                "3. 绝对禁止写主角不在场发生的事\n"
                "4. 绝对禁止写其他角色内心想法（只能通过表情、动作、语言推测）\n"
                "5. 信息受限是优势：利用视角盲区制造悬念和误解\n"
                "6. 心理描写要克制，用行为暗示而非直接剖白"
            ),
            "第三人称有限": (
                "【视角规则 - 第三人称有限】\n"
                "1. 用「他/她」叙事，聚焦于一个视点角色\n"
                "2. 只能写视点角色感知到的事，与第一人称的感知范围相同\n"
                "3. 禁止写视点角色不知道的信息或其他角色内心\n"
                "4. 叙述语言可以比第一人称更灵活，但信息边界不变\n"
                "5. 每个场景只有一个视点，场景切换时才能换视角"
            ),
            "第三人称全知": (
                "【视角规则 - 第三人称全知】\n"
                "1. 用「他/她」叙事，叙述者全知全觉\n"
                "2. 可以写任何角色的内心想法和行为，可以写多个角色同时发生的事\n"
                "3. 切换视角时要有明确过渡（场景分隔或段落转折），禁止在同一段内频繁跳视角\n"
                "4. 全知不等于乱知：不要一次性倾倒所有信息，该藏的悬念还是要藏\n"
                "5. 即使全知，每个场景仍应有主要聚焦角色，避免变成流水账"
            ),
        }
        return guides.get(str(pov), "")

    def build_user_prompt(self, story: Story, chapter_number: int, outline_node: dict) -> str:
        cfg = story.config
        return (
            f"请开始写第{chapter_number}章。\n\n"
            f"本章目标：{outline_node.get('goal', '推进剧情')}\n"
            f"情节点：{', '.join(outline_node.get('plot_points', []))}\n"
            f"情绪基调：{outline_node.get('emotional_beat', '中性')}\n"
            f"字数要求：{cfg.words_per_chapter}字左右\n\n"
            f"请直接写出章节正文，不要写标题、注释或摘要。"
            f"确保故事连贯，与前文自然衔接。"
        )

    def get_continuation_context(self, story: Story, chapter_number: int) -> str:
        cfg = story.config
        return (
            f"【续写上下文 - 第{chapter_number}章】\n"
            f"类型：{cfg.genre}\n"
            f"风格：{cfg.style}\n"
            f"视角：{cfg.pov}\n"
            f"字数：{cfg.words_per_chapter}字\n"
            f"保持与前文的人物性格、世界观设定完全一致。"
        )
