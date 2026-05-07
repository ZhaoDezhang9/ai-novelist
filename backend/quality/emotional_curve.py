"""情感节奏分析器 - 程序化情感曲线控制"""
import json
import re
import math
from collections import Counter
from backend.core.models import ChapterRecord, EmotionSample, CheckResult
from backend.core.llm_client import fast_llm
from backend.core.utils import extract_json
from backend.generation.prompt_templates import EMOTIONAL_CURVE_PROMPT


class EmotionalCurveAnalyzer:
    def __init__(self):
        pass

    async def analyze(self, chapter: ChapterRecord) -> list[EmotionSample]:
        """分析章节情感曲线"""
        content = chapter.content
        if not content.strip():
            return []

        rule_samples = self._rule_based_analyze(content)

        if len(content) > 500:
            try:
                llm_samples = await self._llm_analyze(content)
                return llm_samples if llm_samples else rule_samples
            except Exception:
                return rule_samples

        return rule_samples

    def _rule_based_analyze(self, content: str) -> list[EmotionSample]:
        """基于规则的快速情感采样"""
        tension_words = {"他死死": 5, "捏紧了": 5, "咬牙": 4, "杀气": 5, "危险": 4, "对峙": 4, "逼迫": 4, "悬": 3}
        relaxation_words = {"轻笑": 4, "安逸": 4, "惬意": 5, "阳光": 3, "暖": 3, "平静": 3, "安然": 4, "轻轻": 2}
        sadness_words = {"泪": 4, "哭泣": 5, "离": 3, "死": 5, "别": 3, "伤": 4, "痛": 4, "失去": 5, "回忆": 3}
        pleasure_words = {"笑": 3, "喜": 4, "甜": 3, "幸福": 5, "胜": 3, "突破": 4, "牛": 2, "爽": 4, "得意": 3}

        samples = []
        chunk_size = 500
        total_chars = len(re.findall(r'[\u4e00-\u9fff]', content))

        for i in range(0, max(1, total_chars), chunk_size):
            chunk = content[i:i+chunk_size]
            tension = self._score_chunk(chunk, tension_words)
            relaxation = self._score_chunk(chunk, relaxation_words)
            sadness = self._score_chunk(chunk, sadness_words)
            pleasure = self._score_chunk(chunk, pleasure_words)

            norm_factor = max(1, len(chunk))
            samples.append(EmotionSample(
                chapter=0,
                position_pct=min(1.0, i / max(1, total_chars)),
                tension=min(10, tension / norm_factor * 50),
                relaxation=min(10, relaxation / norm_factor * 50),
                sadness=min(10, sadness / norm_factor * 50),
                pleasure=min(10, pleasure / norm_factor * 50),
            ))

        return samples

    @staticmethod
    def _score_chunk(text: str, weight_map: dict) -> float:
        score = 0.0
        for word, weight in weight_map.items():
            score += text.count(word) * weight
        return score

    async def _llm_analyze(self, content: str) -> list[EmotionSample]:
        """LLM情感采样"""
        system = EMOTIONAL_CURVE_PROMPT
        user = f"请分析以下章节的情感曲线：\n\n{content[:4000]}"
        try:
            raw = await fast_llm.chat(system, user, temperature=0.2, max_tokens=1500)
            data = json.loads(extract_json(raw))
            samples = []
            for s in data.get("samples", []):
                samples.append(EmotionSample(
                    chapter=0,
                    position_pct=s.get("position_pct", 0.5),
                    tension=s.get("tension", 5),
                    relaxation=s.get("relaxation", 5),
                    sadness=s.get("sadness", 5),
                    pleasure=s.get("pleasure", 5),
                ))
            return samples
        except Exception:
            return []

    async def check_against_expected(self, chapter: ChapterRecord, expected_beat: str) -> CheckResult:
        """检查情感曲线是否匹配预期 - 0-10评分"""
        samples = await self.analyze(chapter)
        if not samples:
            return CheckResult(passed=True, layer="emotion", issues=[], scores={"emotion_match": 10.0})

        avg_tension = sum(s.tension for s in samples) / len(samples)
        avg_pleasure = sum(s.pleasure for s in samples) / len(samples)
        avg_sadness = sum(s.sadness for s in samples) / len(samples)

        from backend.generation.prompt_templates import EMOTIONAL_BEAT_TEMPLATES
        expected = EMOTIONAL_BEAT_TEMPLATES.get(expected_beat)

        if not expected:
            return CheckResult(passed=True, layer="emotion", issues=[], scores={"emotion_match": 10.0})

        tension_diff = abs(avg_tension - expected["tension"])
        sadness_diff = abs(avg_sadness - expected["sadness"])
        pleasure_diff = abs(avg_pleasure - expected["pleasure"])
        total_diff = (tension_diff + sadness_diff + pleasure_diff) / 3

        score = max(0, 10.0 - total_diff)
        passed = score >= 5

        issues = []
        if not passed:
            issues.append({
                "type": "emotion_mismatch",
                "severity": "medium",
                "description": f"本章情感曲线与预期「{expected_beat}」不匹配（偏差= {total_diff:.1f}）",
                "detail": f"预期 tension={expected['tension']} 实际≈{avg_tension:.1f}, 预期 pleasure={expected['pleasure']} 实际≈{avg_pleasure:.1f}",
            })

        return CheckResult(passed=passed, layer="emotion", issues=issues, scores={"emotion_match": score})
