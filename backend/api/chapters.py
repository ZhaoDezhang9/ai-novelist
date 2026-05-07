"""章节管理 API 路由"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from backend.core.orchestrator import NovelOrchestrator
from backend.memory import story_db
from backend.generation_status import generation_tracker

router = APIRouter()


@router.get("/generation-active")
async def get_all_active_generations():
    """查询所有正在生成的故事"""
    active = generation_tracker.get_all_active()
    return [
        {
            "story_id": s.story_id,
            "chapter_number": s.chapter_number,
            "status": s.status,
            "tokens_received": s.tokens_received,
            "updated_at": s.updated_at,
        }
        for s in active
    ]


@router.get("/{story_id}/generation-status")
async def get_generation_status(story_id: str):
    """查询故事当前生成状态"""
    status = generation_tracker.get(story_id)
    if not status:
        return {"status": "idle", "story_id": story_id}
    return {
        "story_id": status.story_id,
        "chapter_number": status.chapter_number,
        "status": status.status,
        "tokens_received": status.tokens_received,
        "content_preview": status.content_preview,
        "started_at": status.started_at,
        "updated_at": status.updated_at,
    }


@router.get("/{story_id}/list")
async def list_chapters(story_id: str):
    """列出故事的所有章节"""
    chapters = await story_db.load_all_chapters(story_id)
    return [
        {
            "chapter_number": ch.get("chapter_number"),
            "title": ch.get("title", ""),
            "word_count": ch.get("word_count", 0),
            "status": ch.get("status", "draft"),
            "alignment_score": ch.get("alignment_score", 0),
            "originality_score": ch.get("originality_score", 0),
            "rewrites_count": ch.get("rewrites_count", 0),
        }
        for ch in chapters
    ]


@router.get("/{story_id}/chapter/{chapter_number}")
async def get_chapter(story_id: str, chapter_number: int):
    """读取单个章节"""
    chapter = await story_db.load_chapter(story_id, chapter_number)
    if not chapter:
        raise HTTPException(status_code=404, detail="章节不存在")
    return {
        "chapter_number": chapter.get("chapter_number"),
        "title": chapter.get("title", ""),
        "content": chapter.get("content", ""),
        "word_count": chapter.get("word_count", 0),
        "status": chapter.get("status", "draft"),
        "check_results": chapter.get("check_results", []),
        "alignment_score": chapter.get("alignment_score", 0),
        "originality_score": chapter.get("originality_score", 0),
        "rewrites_count": chapter.get("rewrites_count", 0),
        "emotion_curve": chapter.get("emotion_curve", []),
    }


@router.post("/{story_id}/write-next")
async def write_next_chapter(story_id: str):
    """写下一章"""
    orchestrator = NovelOrchestrator()
    story = await orchestrator.load_story(story_id)
    if not story:
        raise HTTPException(status_code=404, detail="故事不存在")

    if story.current_chapter >= story.config.target_chapters:
        raise HTTPException(status_code=400, detail="所有章节已完成")

    chapter = await orchestrator.write_next_chapter(story)

    return {
        "chapter_number": chapter.chapter_number,
        "title": chapter.title,
        "content": chapter.content,
        "word_count": chapter.word_count,
        "status": chapter.status.value,
        "check_results": [
            {
                "layer": cr.layer,
                "passed": cr.passed,
                "issues_count": len(cr.issues),
                "scores": cr.scores,
            }
            for cr in chapter.check_results
        ],
        "rewrites_count": chapter.rewrites_count,
    }


@router.post("/{story_id}/write-all")
async def write_all_chapters(story_id: str, start_from: int = None):
    """写完全部章节（同步返回）"""
    orchestrator = NovelOrchestrator()
    story = await orchestrator.load_story(story_id)
    if not story:
        raise HTTPException(status_code=404, detail="故事不存在")

    if start_from is not None:
        if start_from < 1:
            raise HTTPException(status_code=400, detail="start_from 必须 >= 1")
        if start_from > story.config.target_chapters:
            raise HTTPException(status_code=400, detail="start_from 超出目标章节数")
        story.current_chapter = start_from - 1

    results = []
    async for chapter in orchestrator.write_all_chapters(story):
        results.append({
            "chapter_number": chapter.chapter_number,
            "title": chapter.title,
            "word_count": chapter.word_count,
            "status": chapter.status.value,
            "rewrites_count": chapter.rewrites_count,
        })

    return {"chapters_written": len(results), "chapters": results}


@router.get("/{story_id}/write-next-stream")
async def write_next_chapter_stream(story_id: str):
    """流式写下一章 (SSE)"""
    orchestrator = NovelOrchestrator()
    story = await orchestrator.load_story(story_id)
    if not story:
        raise HTTPException(status_code=404, detail="故事不存在")

    async def event_generator():
        import json
        async for event in orchestrator.write_chapter_stream(story):
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/{story_id}/chapter/{chapter_number}/rewrite")
async def rewrite_chapter(story_id: str, chapter_number: int):
    """单独改写某一章"""
    orchestrator = NovelOrchestrator()
    story = await orchestrator.load_story(story_id)
    if not story:
        raise HTTPException(status_code=404, detail="故事不存在")

    chapter_data = await story_db.load_chapter(story_id, chapter_number)
    if not chapter_data:
        raise HTTPException(status_code=404, detail="章节不存在")

    from backend.core.models import ChapterRecord

    chapter = ChapterRecord(
        story_id=story_id,
        chapter_number=chapter_number,
        content=chapter_data.get("content", ""),
        word_count=chapter_data.get("word_count", 0),
    )

    # 重新跑质检
    checks = await orchestrator.pipeline.run_checks_parallel(story, chapter)

    # 收集问题并改写
    issues = orchestrator._collect_issues(checks)
    if issues:
        context = await orchestrator.context_builder.build_master_prompt(
            story=story,
            hot_memory=await orchestrator.memory.get_hot(chapter_number),
            warm_memory=orchestrator.memory.get_warm(),
            cold_memory=orchestrator.memory.get_cold(),
        )
        chapter = await orchestrator.rewrite.rewrite_targeted(chapter, issues, context)
        await story_db.save_chapter(story_id, chapter_number, chapter.model_dump())

    return {
        "chapter_number": chapter.chapter_number,
        "content": chapter.content,
        "word_count": chapter.word_count,
        "issues_found": len(issues),
        "rewrites_count": chapter.rewrites_count,
    }
