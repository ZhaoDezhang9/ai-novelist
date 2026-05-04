"""故事管理 API 路由"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.core.models import Story, StoryConfig, StoryGenre, StoryStyle, NarrativePOV
from backend.core.orchestrator import NovelOrchestrator
from backend.core.llm_client import fast_llm
from backend.core.utils import extract_json
from backend.memory import story_db
import json

router = APIRouter()


class GenerateMetaRequest(BaseModel):
    idea: str
    genre: str = "玄幻"


class CreateStoryRequest(BaseModel):
    title: str
    genre: str
    style: str
    pov: str = "第三人称有限"
    target_chapters: int = 20
    words_per_chapter: int = 3000
    target_audience: str = "大众读者"
    theme: str = ""


class StoryListItem(BaseModel):
    id: str
    title: str
    genre: str
    style: str
    current_chapter: int
    target_chapters: int
    status: str
    created_at: str


@router.post("/generate-meta")
async def generate_meta(req: GenerateMetaRequest):
    """从灵感自动生成标题和简介"""
    prompt = (
        f"用户想写一部{req.genre}类型的小说，灵感是：\n{req.idea}\n\n"
        f"请为这部小说生成：\n"
        f"1. 一个有吸引力的标题（6-15字，要有悬念或冲突感）\n"
        f"2. 一段简介（50-100字，说清核心冲突和看点）\n\n"
        f"输出JSON：{{\"title\": \"...\", \"theme\": \"...\"}}"
    )
    try:
        raw = await fast_llm.chat(
            "你是一位资深小说编辑，擅长提炼故事核心卖点。只输出JSON。",
            prompt, temperature=0.8, max_tokens=500,
        )
        data = json.loads(extract_json(raw))
        return {"title": data.get("title", ""), "theme": data.get("theme", "")}
    except Exception:
        # 回退：从灵感中截取
        title = req.idea.strip()[:12] + ("" if len(req.idea) <= 12 else "...")
        return {"title": title, "theme": req.idea.strip()[:100]}


@router.post("")
async def create_story(req: CreateStoryRequest):
    """创建新故事"""
    orchestrator = NovelOrchestrator()
    config = StoryConfig(
        title=req.title,
        genre=StoryGenre(req.genre),
        style=StoryStyle(req.style),
        pov=NarrativePOV(req.pov),
        target_chapters=req.target_chapters,
        words_per_chapter=req.words_per_chapter,
        target_audience=req.target_audience,
        theme=req.theme,
    )
    story = await orchestrator.create_story(config)
    return {
        "id": story.id,
        "title": story.config.title,
        "genre": story.config.genre.value,
        "style": story.config.style.value,
        "total_chapters": len(story.outline),
        "world_bible": story.world_bible.model_dump(),
        "characters_count": len(story.characters),
    }


@router.get("")
async def list_stories():
    """列出所有故事"""
    stories = await story_db.list_stories()
    result = []
    for s in stories:
        config = s.get("config", {})
        if isinstance(config, dict):
            result.append(StoryListItem(
                id=s["id"],
                title=config.get("title", "未命名"),
                genre=config.get("genre", "未知"),
                style=config.get("style", "默认"),
                current_chapter=s.get("current_chapter", 0),
                target_chapters=config.get("target_chapters", 50),
                status=s.get("status", "draft"),
                created_at=s.get("created_at", ""),
            ))
    return result


@router.get("/{story_id}")
async def get_story(story_id: str):
    """获取故事详情"""
    orchestrator = NovelOrchestrator()
    story = await orchestrator.load_story(story_id)
    if not story:
        raise HTTPException(status_code=404, detail="故事不存在")
    return {
        "id": story.id,
        "config": story.config.model_dump(),
        "outline": story.outline,
        "world_bible": story.world_bible.model_dump(),
        "characters": story.characters,
        "foreshadowing_list": story.foreshadowing_list,
        "current_chapter": story.current_chapter,
    }


@router.delete("/{story_id}")
async def delete_story(story_id: str):
    """删除故事"""
    await story_db.delete_story(story_id)
    return {"status": "deleted"}
