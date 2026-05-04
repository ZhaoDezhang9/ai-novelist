import urllib.request, json, time, os

print("Test 1: Health")
resp = urllib.request.urlopen("http://localhost:8000/api/health")
print("Health:", json.loads(resp.read()))

print("\nTest 2: List stories")
resp = urllib.request.urlopen("http://localhost:8000/api/stories")
stories = json.loads(resp.read())
print(f"Stories: {len(stories)}")

print("\n=== Test 3: Create story (calling DeepSeek API) ===")
data = json.dumps({
    "title": "星辰陨落",
    "genre": "科幻",
    "style": "悬疑紧绷",
    "pov": "第三人称有限",
    "target_chapters": 10,
    "words_per_chapter": 2000,
    "target_audience": "科幻爱好者",
    "theme": "AI觉醒与人类命运"
}).encode()

req = urllib.request.Request(
    "http://localhost:8000/api/stories",
    data=data,
    headers={"Content-Type": "application/json"},
    method="POST",
)

start = time.time()
try:
    resp = urllib.request.urlopen(req, timeout=180)
    result = json.loads(resp.read())
    elapsed = time.time() - start
    story_id = result.get("id", "")
    wb = result.get("world_bible", {})

    print(f"Story created in {elapsed:.1f}s")
    print(f"  ID: {story_id}")
    print(f"  Title: {result.get('title', '')}")
    print(f"  Genre: {result.get('genre', '')}")
    print(f"  Style: {result.get('style', '')}")
    print(f"  Outline chapters: {result.get('total_chapters', 0)}")
    print(f"  Characters: {result.get('characters_count', 0)}")
    print(f"  World rules: {len(wb.get('rules', []))}")
    if wb.get("setting"):
        print(f"  Setting: {wb['setting'][:100]}...")
    if wb.get("rules"):
        for r in wb["rules"][:3]:
            print(f"    Rule: {r}")

    print(f"\n=== SUCCESS: Story fully created ===")
except Exception as e:
    elapsed = time.time() - start
    print(f"ERROR after {elapsed:.1f}s: {e}")
