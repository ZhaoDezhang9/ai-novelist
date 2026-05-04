"""风格量化器 - 将风格参数化为可测量的向量"""
import re
from backend.core.models import StyleVector
from backend.generation.prompt_templates import STYLE_VECTORS


class StyleQuantifier:
    def __init__(self):
        self.presets = STYLE_VECTORS

    def get_preset(self, style_name: str) -> StyleVector:
        """获取预设风格向量"""
        preset = self.presets.get(style_name)
        if preset:
            return StyleVector(**preset)
        return StyleVector()

    def from_text(self, text: str) -> StyleVector:
        """从文本中提取风格向量"""
        if not text.strip():
            return StyleVector()

        # 句长
        sentences = re.split(r'[。！？…\n]', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        lengths = [len(re.findall(r'[\u4e00-\u9fff]', s)) for s in sentences]
        avg_sentence_length = sum(lengths) / max(1, len(lengths))

        # 对话占比
        dialogue_chars = len(re.findall(r'["""][^""""]+["""]', text)) + len(re.findall(r'「[^」]+」', text))
        total_chars = max(1, len(re.findall(r'[\u4e00-\u9fff]', text)))
        dialogue_ratio = min(1.0, dialogue_chars / total_chars)

        # 比喻密度
        metaphor_indicators = ["像", "如", "仿佛", "宛如", "如同", "好比", "犹如", "像是"]
        metaphor_count = sum(text.count(w) for w in metaphor_indicators)
        sentence_count = max(1, len(sentences))
        metaphor_density = min(0.3, metaphor_count / sentence_count)

        # 副词密度
        adverb_indicators = re.findall(r'[\u4e00-\u9fff]{1,2}地', text)
        adverb_ratio = min(0.2, len(adverb_indicators) / max(1, sentence_count))

        # 段落中位数
        paragraphs = [p for p in text.split("\n") if p.strip()]
        para_sentence_counts = []
        for para in paragraphs:
            sents = re.split(r'[。！？…]', para)
            para_sentence_counts.append(len([s for s in sents if s.strip()]))
        sorted_counts = sorted(para_sentence_counts)
        median_idx = len(sorted_counts) // 2
        paragraph_length_median = sorted_counts[median_idx] if sorted_counts else 4

        return StyleVector(
            avg_sentence_length=round(avg_sentence_length, 1),
            dialogue_ratio=round(dialogue_ratio, 2),
            metaphor_density=round(metaphor_density, 3),
            adverb_ratio=round(adverb_ratio, 2),
            paragraph_length_median=paragraph_length_median,
        )

    def compare(self, target: StyleVector, actual: StyleVector) -> float:
        """比较两个风格向量的相似度 (0.0-1.0)"""
        diffs = [
            abs(target.avg_sentence_length - actual.avg_sentence_length) / max(1, target.avg_sentence_length),
            abs(target.dialogue_ratio - actual.dialogue_ratio) / max(0.01, target.dialogue_ratio),
            abs(target.metaphor_density - actual.metaphor_density) / max(0.001, target.metaphor_density),
            abs(target.adverb_ratio - actual.adverb_ratio) / max(0.001, target.adverb_ratio),
            abs(target.paragraph_length_median - actual.paragraph_length_median) / max(1, target.paragraph_length_median),
        ]
        avg_diff = sum(diffs) / len(diffs)
        return max(0, 1.0 - avg_diff)

    def style_feedback(self, target: StyleVector, actual: StyleVector) -> dict:
        """生成风格偏差反馈"""
        feedback = {}
        if actual.avg_sentence_length < target.avg_sentence_length * 0.7:
            feedback["sentence_length"] = "句长偏短，建议增加修饰语和复合句"
        elif actual.avg_sentence_length > target.avg_sentence_length * 1.3:
            feedback["sentence_length"] = "句长偏长，建议拆分长句"

        if actual.dialogue_ratio < target.dialogue_ratio * 0.5:
            feedback["dialogue"] = "对话偏少，建议增加角色互动"
        elif actual.dialogue_ratio > target.dialogue_ratio * 1.5:
            feedback["dialogue"] = "对话偏多，建议增加叙述和描写"

        if actual.adverb_ratio > target.adverb_ratio * 1.5:
            feedback["adverb"] = "副词使用过多（XX地），建议用动作描写替代"

        return feedback
