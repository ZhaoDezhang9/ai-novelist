"""AI Novelist - 全自动AI小说创作系统配置"""
from pydantic_settings import BaseSettings
from pathlib import Path
from typing import Optional


class Settings(BaseSettings):
    # --- 认证 ---
    api_key: str = ""
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    rate_limit: str = "30/minute"

    # --- LLM 配置 ---
    llm_api_key: str = ""
    llm_api_base: str = "https://api.openai.com/v1"
    llm_model: str = "gpt-4o"               # 创意写作模型（高质量）
    llm_fast_model: str = "gpt-4o-mini"     # 质量评估模型（中档）
    llm_cheap_model: str = "gpt-4o-mini"    # 规划类任务模型（便宜）
    llm_max_tokens: int = 8192
    llm_temperature: float = 0.85
    llm_top_p: float = 0.92

    # --- 记忆系统 ---
    hot_chapters: int = 2
    warm_summary_chapters: int = 5
    max_context_tokens: int = 64000

    # --- 质量门禁 ---
    ngram_overlap_threshold: float = 0.15
    template_similarity_threshold: float = 0.7
    vocab_diversity_threshold: float = 0.4
    twist_density_min: float = 0.00033
    alignment_score_min: float = 0.75
    quality_dimension_min: float = 5.0    # 任一维度低于此分则重写
    quality_overall_min: float = 6.0      # 总分低于此分则重写

    # --- 流水线 ---
    max_rewrite_rounds: int = 1     # 每章最多1轮改写（保证总LLM调用≤6次）
    rewrite_window_lines: int = 400

    # --- 存储 ---
    data_dir: Path = Path("data")
    stories_file: str = "stories.db"

    # --- 日志 ---
    log_level: str = "INFO"
    log_file: str = "logs/app.log"

    class Config:
        env_file = ".env"
        env_prefix = "NOVELIST_"


_settings: Optional[Settings] = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
