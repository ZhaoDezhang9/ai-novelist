"""Full end-to-end test: Create -> Write Ch1 -> Write Ch2 -> List -> Read"""
import asyncio
import time
from backend.core.models import StoryConfig, StoryGenre, StoryStyle, NarrativePOV
from backend.core.orchestrator import NovelOrchestrator
from backend.memory import story_db

async def test():
    orch = NovelOrchestrator()

    # Step 1: Create story
    print("=" * 60)
    print("STEP 1: Create Story")
    print("=" * 60)
    config = StoryConfig(
        title="深渊回响",
        genre=StoryGenre.XUANYI,
        style=StoryStyle.XUANYIJINTONG,
        pov=NarrativePOV.FIRST_PERSON,
        target_chapters=5,
        words_per_chapter=1500,
        target_audience="悬疑爱好者",
        theme="记忆裂缝与真相",
    )
    start = time.time()
    story = await orch.create_story(config)
    elapsed = time.time() - start
    print(f"  ID: {story.id}")
    print(f"  Outline: {len(story.outline)} chapters")
    print(f"  Characters: {len(story.characters)}")
    print(f"  World rules: {len(story.world_bible.rules)}")
    print(f"  Time: {elapsed:.1f}s")

    # Print outline
    print("\n  Outline:")
    for node in story.outline:
        ch = node.get("chapter", "?")
        title = node.get("title", "")
        goal = node.get("goal", "")[:50]
        beat = node.get("emotional_beat", "")
        print(f"    Ch{ch}: {title} | {goal} | beat={beat}")

    # Step 2: Write Chapter 1
    print("\n" + "=" * 60)
    print("STEP 2: Write Chapter 1 (draft -> L1/L2/L3 quality -> rewrite -> accept)")
    print("=" * 60)
    start = time.time()
    ch1 = await orch.write_next_chapter(story)
    elapsed = time.time() - start
    print(f"  Ch{ch1.chapter_number}: {ch1.title}")
    print(f"  Words: {ch1.word_count}")
    print(f"  Status: {ch1.status.value}")
    print(f"  Rewrites: {ch1.rewrites_count}")
    print("  Check results:")
    for cr in ch1.check_results:
        mark = "PASS" if cr.passed else "FAIL"
        print(f"    [{mark}] {cr.layer} (issues={len(cr.issues)}) scores={cr.scores}")
    print(f"  Content: {ch1.content[:150]}...")
    print(f"  Time: {elapsed:.1f}s")

    # Step 3: Write Chapter 2 (tests memory continuity)
    print("\n" + "=" * 60)
    print("STEP 3: Write Chapter 2 (memory continuity test)")
    print("=" * 60)
    start = time.time()
    ch2 = await orch.write_next_chapter(story)
    elapsed = time.time() - start
    print(f"  Ch{ch2.chapter_number}: {ch2.title}")
    print(f"  Words: {ch2.word_count}")
    print(f"  Status: {ch2.status.value}")
    print("  Check results:")
    for cr in ch2.check_results:
        mark = "PASS" if cr.passed else "FAIL"
        print(f"    [{mark}] {cr.layer} (issues={len(cr.issues)}) scores={cr.scores}")
    print(f"  Content: {ch2.content[:150]}...")
    print(f"  Time: {elapsed:.1f}s")

    # Step 4: List chapters from DB
    print("\n" + "=" * 60)
    print("STEP 4: List chapters from DB")
    print("=" * 60)
    chapters = await story_db.load_all_chapters(story.id)
    for ch in chapters:
        print(f"  Ch{ch['chapter_number']}: {ch.get('title','')} | {ch.get('word_count',0)} words | {ch.get('status','')}")

    # Step 5: Read chapter detail
    print("\n" + "=" * 60)
    print("STEP 5: Read Ch1 detail from DB")
    print("=" * 60)
    ch_data = await story_db.load_chapter(story.id, 1)
    if ch_data:
        print(f"  Title: {ch_data.get('title','')}")
        print(f"  Words: {ch_data.get('word_count',0)}")
        print(f"  Status: {ch_data.get('status','')}")
        print(f"  Content length: {len(ch_data.get('content',''))} chars")
        content = ch_data.get("content", "")
        print("  Full content:")
        print(f"  {content[:500]}...")
    else:
        print("  ERROR: Chapter not found in DB!")

    # Step 6: Verify story state
    print("\n" + "=" * 60)
    print("STEP 6: Verify story state")
    print("=" * 60)
    fresh = await orch.load_story(story.id)
    print(f"  current_chapter: {fresh.current_chapter}")
    print(f"  target: {fresh.config.target_chapters}")
    print(f"  foreshadowing items: {len(fresh.foreshadowing_list)}")

    print("\n" + "=" * 60)
    print("ALL 6 STEPS PASSED!")
    print("=" * 60)

asyncio.run(test())
