"""原创性检测器 - 句式重复/情节模板/词汇多样性/转折密度"""
import json
import re
from collections import Counter
from backend.core.models import CheckResult
from backend.core.llm_client import fast_llm
from backend.core.config import get_settings
from backend.core.utils import extract_json
from backend.generation.prompt_templates import ORIGINALITY_CHECK_PROMPT


class OriginalityChecker:
    def __init__(self):
        self.settings = get_settings()

    async def check(self, content: str, genre: str = "玄幻") -> CheckResult:
        """综合原创性检测"""
        scores = {}
        issues = []

        ngram_score, ngram_issues = self._check_sentence_repetition(content)
        scores["ngram_repetition"] = ngram_score
        issues.extend(ngram_issues)

        vocab_score, vocab_issues = self._check_vocab_diversity(content)
        scores["vocab_diversity"] = vocab_score
        issues.extend(vocab_issues)

        twist_score, twist_issues = self._check_twist_density(content)
        scores["twist_density"] = twist_score
        issues.extend(twist_issues)

        template_score, template_issues = await self._check_template_patterns(content, genre)
        scores["template_avoidance"] = template_score
        issues.extend(template_issues)

        # 将 0-1 分数映射到 0-10
        overall_01 = sum(scores.values()) / max(1, len(scores))
        overall = overall_01 * 10
        passed = overall >= 7 and len(issues) < 5
        return CheckResult(
            passed=passed,
            layer="originality",
            issues=issues,
            scores={k: v * 10 for k, v in scores.items()},
        )

    def _check_sentence_repetition(self, content: str) -> tuple[float, list[dict]]:
        """n-gram句式重复检测"""
        sentences = re.split(r'[。！？…\n]', content)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 5]

        if len(sentences) < 10:
            return 1.0, []

        trigrams = []
        for s in sentences:
            words = list(s)
            for i in range(len(words) - 2):
                trigrams.append(tuple(words[i:i+3]))

        if len(trigrams) < 10:
            return 1.0, []

        counter = Counter(trigrams)
        repeat_count = sum(1 for c in counter.values() if c > 2)
        overlap_rate = repeat_count / max(1, len(trigrams))

        score = max(0, 1.0 - overlap_rate / self.settings.ngram_overlap_threshold)
        issues = []
        if overlap_rate > self.settings.ngram_overlap_threshold:
            issues.append({
                "type": "sentence_repetition",
                "severity": "medium",
                "description": f"句式重复率 {overlap_rate:.1%} 超过阈值 {self.settings.ngram_overlap_threshold:.1%}",
                "suggestion": "变化句式结构，混合长短句，避免重复的3字组合",
            })
        return score, issues

    def _check_vocab_diversity(self, content: str) -> tuple[float, list[dict]]:
        """TTR词汇多样性检测"""
        words = re.findall(r'[\u4e00-\u9fff]{2,}', content)
        if len(words) < 20:
            return 1.0, []

        unique = len(set(words))
        total = len(words)
        ttr = unique / total if total > 0 else 0

        score = min(1.0, ttr / self.settings.vocab_diversity_threshold)
        issues = []
        if ttr < self.settings.vocab_diversity_threshold:
            counter = Counter(words)
            top_repeat = counter.most_common(5)
            issues.append({
                "type": "low_vocab_diversity",
                "severity": "medium",
                "description": f"词汇多样性 TTR={ttr:.2f} 低于阈值 {self.settings.vocab_diversity_threshold}",
                "top_repeated_words": [w for w, _ in top_repeat if _ > 2],
                "suggestion": "增加同义词替换，丰富词汇库",
            })
        return score, issues

    def _check_twist_density(self, content: str) -> tuple[float, list[dict]]:
        """转折密度检测"""
        twist_indicators = [
            "然而", "但是", "可是", "不过", "突然", "忽然",
            "没想到", "竟然是", "原来", "其实", "反而", "不料",
            "竟然", "居然", "发现", "惊醒", "恍然大悟",
            "不，", "等等，", "但",
        ]
        count = sum(content.count(w) for w in twist_indicators)
        words = len(re.findall(r'[\u4e00-\u9fff]', content))
        density = count / max(1, words)

        score = min(1.0, density / self.settings.twist_density_min)
        issues = []
        if density < self.settings.twist_density_min:
            issues.append({
                "type": "low_twist_density",
                "severity": "low",
                "description": f"转折密度 {density:.5f} 低于最低要求 {self.settings.twist_density_min:.5f}",
                "suggestion": "增加意外事件或信息揭示，提升阅读节奏",
            })
        return score, issues

    async def _check_template_patterns(self, content: str, genre: str) -> tuple[float, list[dict]]:
        """使用LLM检测情节模板化"""
        system = ORIGINALITY_CHECK_PROMPT.format(genre=genre)
        user = f"请检查以下章节是否落入模板化写作：\n\n{content[:4000]}"

        try:
            raw = await fast_llm.chat(system, user, temperature=0.2, max_tokens=1000)
            data = json.loads(extract_json(raw))
            score = data.get("overall_score", 0.7)
            issues = data.get("issues", [])
            suggestions = data.get("rewrite_suggestions", [])
            if suggestions:
                issues.extend([{"type": "rewrite_suggestion", "severity": "low", "description": s, "suggestion": s} for s in suggestions[:3]])
            return score, issues
        except Exception:
            return 0.8, []
