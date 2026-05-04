"""AI Novelist - 全自动AI小说创作系统配置"""
from pydantic_settings import BaseSettings
from pathlib import Path
from typing import Optional


class Settings(BaseSettings):
    # --- LLM 配置 ---
    llm_api_key: str = ""
    llm_api_base: str = "https://api.openai.com/v1"
    llm_model: str = "gpt-4o"
    llm_fast_model: str = "gpt-4o-mini"  # 轻量模型，用于快筛检查
    llm_max_tokens: int = 8192
    llm_temperature: float = 0.85
    llm_top_p: float = 0.92

    # --- 记忆系统 ---
    hot_chapters: int = 2          # 热记忆保留最近N章全文
    warm_summary_chapters: int = 5 # 温记忆保留最近N章摘要
    max_context_tokens: int = 64000

    # --- 质量门禁 ---
    ngram_overlap_threshold: float = 0.15    # 句式重复触发阈值
    template_similarity_threshold: float = 0.7  # 模板化触发阈值
    vocab_diversity_threshold: float = 0.4   # TTR最低阈值
    twist_density_min: float = 0.00033       # 每3000字至少1次转折
    alignment_score_min: float = 0.75        # 大纲对齐最低分

    # --- 流水线 ---
    max_rewrite_rounds: int = 3
    rewrite_window_lines: int = 400  # 改写窗口(字)

    # --- 存储 ---
    data_dir: Path = Path("data")
    stories_file: str = "stories.db"

    class Config:
        env_file = ".env"
        env_prefix = "NOVELIST_"


_settings: Optional[Settings] = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
