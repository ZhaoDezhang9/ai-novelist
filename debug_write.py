"""Debug write_next_chapter - get full traceback"""
import asyncio, traceback, json
from backend.core.models import Story
from backend.core.orchestrator import NovelOrchestrator
from backend.memory import story_db

async def test():
    stories = await story_db.list_stories()
    if not stories:
        print("No stories found")
        return
    sid = stories[-1]["id"]
    print(f"Loading story {sid}...")
    
    orch = NovelOrchestrator()
    story = await orch.load_story(sid)
    if not story:
        print("Story not found")
        return
    print(f"Story: {story.config.title}, outline: {len(story.outline)} ch, current: {story.current_chapter}")
    print(f"Outline sample: {json.dumps(story.outline[0], ensure_ascii=False)[:200] if story.outline else 'EMPTY'}")
    
    print("\nCalling write_next_chapter...")
    try:
        ch = await orch.write_next_chapter(story)
        print(f"SUCCESS: Chapter {ch.chapter_number}, {ch.word_count} words, status={ch.status}")
        print(f"Content preview: {ch.content[:200]}")
    except Exception as e:
        print(f"FAILED: {type(e).__name__}: {e}")
        traceback.print_exc()

asyncio.run(test())
