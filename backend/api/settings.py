"""设置管理 API 路由"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from pathlib import Path

from backend.core.config import get_settings

router = APIRouter()


class SettingsResponse(BaseModel):
    llm_api_key: str
    llm_api_base: str
    llm_model: str
    llm_fast_model: str
    llm_temperature: float
    llm_top_p: float
    llm_max_tokens: int
    max_rewrite_rounds: int
    alignment_score_min: float
    ngram_overlap_threshold: float
    template_similarity_threshold: float
    vocab_diversity_threshold: float
    twist_density_min: float
    rewrite_window_lines: int
    hot_chapters: int
    warm_summary_chapters: int
    max_context_tokens: int


class SettingsUpdateRequest(BaseModel):
    llm_api_key: Optional[str] = None
    llm_api_base: Optional[str] = None
    llm_model: Optional[str] = None
    llm_fast_model: Optional[str] = None
    llm_temperature: Optional[float] = None
    llm_top_p: Optional[float] = None
    llm_max_tokens: Optional[int] = None
    max_rewrite_rounds: Optional[int] = None
    alignment_score_min: Optional[float] = None
    ngram_overlap_threshold: Optional[float] = None
    template_similarity_threshold: Optional[float] = None
    vocab_diversity_threshold: Optional[float] = None
    twist_density_min: Optional[float] = None
    rewrite_window_lines: Optional[int] = None
    hot_chapters: Optional[int] = None
    warm_summary_chapters: Optional[int] = None
    max_context_tokens: Optional[int] = None


def mask_api_key(key: str) -> str:
    """掩码 API 密钥，只显示最后 4 位"""
    if not key or len(key) <= 4:
        return "****"
    return "*" * (len(key) - 4) + key[-4:]


def update_env_file(updates: dict):
    """更新 .env 文件，保留注释和格式"""
    env_path = Path(".env")
    if not env_path.exists():
        lines = []
    else:
        with open(env_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

    # 构建字段名到 env 键的映射
    field_to_env = {
        "llm_api_key": "NOVELIST_LLM_API_KEY",
        "llm_api_base": "NOVELIST_LLM_API_BASE",
        "llm_model": "NOVELIST_LLM_MODEL",
        "llm_fast_model": "NOVELIST_LLM_FAST_MODEL",
        "llm_temperature": "NOVELIST_LLM_TEMPERATURE",
        "llm_top_p": "NOVELIST_LLM_TOP_P",
        "llm_max_tokens": "NOVELIST_LLM_MAX_TOKENS",
        "max_rewrite_rounds": "NOVELIST_MAX_REWRITE_ROUNDS",
        "alignment_score_min": "NOVELIST_ALIGNMENT_SCORE_MIN",
        "ngram_overlap_threshold": "NOVELIST_NGRAM_OVERLAP_THRESHOLD",
        "template_similarity_threshold": "NOVELIST_TEMPLATE_SIMILARITY_THRESHOLD",
        "vocab_diversity_threshold": "NOVELIST_VOCAB_DIVERSITY_THRESHOLD",
        "twist_density_min": "NOVELIST_TWIST_DENSITY_MIN",
        "rewrite_window_lines": "NOVELIST_REWRITE_WINDOW_LINES",
        "hot_chapters": "NOVELIST_HOT_CHAPTERS",
        "warm_summary_chapters": "NOVELIST_WARM_SUMMARY_CHAPTERS",
        "max_context_tokens": "NOVELIST_MAX_CONTEXT_TOKENS",
    }

    updated_keys = set()

    # 更新已存在的行
    for i, line in enumerate(lines):
        line = line.rstrip("\n")
        if not line or line.startswith("#"):
            continue

        if "=" in line:
            key = line.split("=", 1)[0].strip()
            for field, env_key in field_to_env.items():
                if key == env_key and field in updates:
                    lines[i] = f"{env_key}={updates[field]}\n"
                    updated_keys.add(env_key)
                    break

    # 添加不存在的键
    for field, env_key in field_to_env.items():
        if field in updates and env_key not in updated_keys:
            lines.append(f"{env_key}={updates[field]}\n")

    # 写回文件
    with open(env_path, "w", encoding="utf-8") as f:
        f.writelines(lines)


@router.get("", response_model=SettingsResponse)
async def get_settings_endpoint():
    """获取当前设置（API 密钥已掩码）"""
    settings = get_settings()
    return SettingsResponse(
        llm_api_key=mask_api_key(settings.llm_api_key),
        llm_api_base=settings.llm_api_base,
        llm_model=settings.llm_model,
        llm_fast_model=settings.llm_fast_model,
        llm_temperature=settings.llm_temperature,
        llm_top_p=settings.llm_top_p,
        llm_max_tokens=settings.llm_max_tokens,
        max_rewrite_rounds=settings.max_rewrite_rounds,
        alignment_score_min=settings.alignment_score_min,
        ngram_overlap_threshold=settings.ngram_overlap_threshold,
        template_similarity_threshold=settings.template_similarity_threshold,
        vocab_diversity_threshold=settings.vocab_diversity_threshold,
        twist_density_min=settings.twist_density_min,
        rewrite_window_lines=settings.rewrite_window_lines,
        hot_chapters=settings.hot_chapters,
        warm_summary_chapters=settings.warm_summary_chapters,
        max_context_tokens=settings.max_context_tokens,
    )


@router.put("", response_model=SettingsResponse)
async def update_settings_endpoint(req: SettingsUpdateRequest):
    """更新设置（支持部分更新）"""
    settings = get_settings()
    updates = req.model_dump(exclude_none=True)

    # 更新 settings 单例
    for field, value in updates.items():
        setattr(settings, field, value)

    # 持久化到 .env 文件
    update_env_file(updates)

    return SettingsResponse(
        llm_api_key=mask_api_key(settings.llm_api_key),
        llm_api_base=settings.llm_api_base,
        llm_model=settings.llm_model,
        llm_fast_model=settings.llm_fast_model,
        llm_temperature=settings.llm_temperature,
        llm_top_p=settings.llm_top_p,
        llm_max_tokens=settings.llm_max_tokens,
        max_rewrite_rounds=settings.max_rewrite_rounds,
        alignment_score_min=settings.alignment_score_min,
        ngram_overlap_threshold=settings.ngram_overlap_threshold,
        template_similarity_threshold=settings.template_similarity_threshold,
        vocab_diversity_threshold=settings.vocab_diversity_threshold,
        twist_density_min=settings.twist_density_min,
        rewrite_window_lines=settings.rewrite_window_lines,
        hot_chapters=settings.hot_chapters,
        warm_summary_chapters=settings.warm_summary_chapters,
        max_context_tokens=settings.max_context_tokens,
    )
