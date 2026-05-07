"""Supplementary tests: settings, story detail, chapters, error cases, delete"""
import urllib.request, json, sys

BASE = "http://localhost:8000/api"
PASS = 0
FAIL = 0

def ok(msg):
    global PASS
    PASS += 1
    print(f"  PASS: {msg}")

def fail(msg):
    global FAIL
    FAIL += 1
    print(f"  FAIL: {msg}")

def api_get(path, timeout=10):
    return json.loads(urllib.request.urlopen(f"{BASE}{path}", timeout=timeout).read())

def api_post(path, data=None, timeout=30):
    body = json.dumps(data).encode() if data else b"{}"
    req = urllib.request.Request(f"{BASE}{path}", data=body, headers={"Content-Type": "application/json"}, method="POST")
    return json.loads(urllib.request.urlopen(req, timeout=timeout).read())

def api_delete(path, timeout=10):
    req = urllib.request.Request(f"{BASE}{path}", method="DELETE")
    return json.loads(urllib.request.urlopen(req, timeout=timeout).read())

# Use an existing story with chapters for read tests
SID = "9ba6dbf356f5"

print("=" * 50)
print("T1: GET /api/settings")
print("=" * 50)
try:
    s = api_get("/settings")
    assert "llm_model" in s, "missing llm_model"
    assert "max_rewrite_rounds" in s, "missing max_rewrite_rounds"
    assert s["llm_api_key"].startswith("*"), "api_key not masked"
    ok(f"model={s['llm_model']}, rewrite_rounds={s['max_rewrite_rounds']}, key masked")
except Exception as e:
    fail(str(e))

print("\n" + "=" * 50)
print("T2: GET /api/stories/{id} - story detail")
print("=" * 50)
try:
    story = api_get(f"/stories/{SID}")
    assert "config" in story, "missing config"
    assert "outline" in story, "missing outline"
    assert "characters" in story, "missing characters"
    assert "world_bible" in story, "missing world_bible"
    assert len(story["outline"]) == 5, f"expected 5 outline chapters, got {len(story['outline'])}"
    ok(f"title={story['config']['title']}, outline={len(story['outline'])}ch, chars={len(story['characters'])}")
except Exception as e:
    fail(str(e))

print("\n" + "=" * 50)
print("T3: GET /api/stories/{id} - 404 for non-existent")
print("=" * 50)
try:
    req = urllib.request.Request(f"{BASE}/stories/nonexistent-id")
    resp = urllib.request.urlopen(req, timeout=10)
    fail("should have returned 404")
except urllib.error.HTTPError as e:
    assert e.code == 404, f"expected 404, got {e.code}"
    ok(f"404 returned correctly")
except Exception as e:
    fail(str(e))

print("\n" + "=" * 50)
print("T4: GET /api/chapters/{sid}/list")
print("=" * 50)
try:
    chapters = api_get(f"/chapters/{SID}/list")
    assert isinstance(chapters, list), "not a list"
    assert len(chapters) >= 2, f"expected >=2 chapters, got {len(chapters)}"
    for ch in chapters:
        assert "chapter_number" in ch
        assert "word_count" in ch
        assert "status" in ch
    ok(f"{len(chapters)} chapters: " + ", ".join(f"Ch{c['chapter_number']}({c['word_count']}w)" for c in chapters))
except Exception as e:
    fail(str(e))

print("\n" + "=" * 50)
print("T5: GET /api/chapters/{sid}/chapter/1 - chapter detail")
print("=" * 50)
try:
    ch = api_get(f"/chapters/{SID}/chapter/1")
    assert "content" in ch, "missing content"
    assert "title" in ch, "missing title"
    assert ch["chapter_number"] == 1
    assert len(ch["content"]) > 100, f"content too short: {len(ch['content'])} chars"
    ok(f"Ch1: {ch['title']}, {ch['word_count']} words, {len(ch['content'])} chars")
except Exception as e:
    fail(str(e))

print("\n" + "=" * 50)
print("T6: GET /api/chapters/{sid}/chapter/999 - 404")
print("=" * 50)
try:
    req = urllib.request.Request(f"{BASE}/chapters/{SID}/chapter/999")
    resp = urllib.request.urlopen(req, timeout=10)
    fail("should have returned 404")
except urllib.error.HTTPError as e:
    assert e.code == 404, f"expected 404, got {e.code}"
    ok("404 returned correctly")

print("\n" + "=" * 50)
print("T7: POST /api/stories/generate-meta")
print("=" * 50)
try:
    result = api_post("/stories/generate-meta", {
        "idea": "一个程序员穿越到魔法世界，发现代码可以操控魔法",
        "genre": "玄幻"
    })
    assert "title" in result, "missing title"
    assert "theme" in result, "missing theme"
    ok(f"title={result['title']}, theme={result.get('theme','')[:50]}...")
except Exception as e:
    fail(str(e))

print("\n" + "=" * 50)
print("T8: GET /api/chapters/generation-active")
print("=" * 50)
try:
    active = api_get("/chapters/generation-active")
    assert isinstance(active, list), "not a list"
    ok(f"{len(active)} active generations")
except Exception as e:
    fail(str(e))

print("\n" + "=" * 50)
print("T9: DELETE /api/stories/{id}")
print("=" * 50)
test_id = "0ee033f7a8af"
try:
    result = api_delete(f"/stories/{test_id}")
    assert result.get("status") == "deleted", f"expected deleted, got {result}"
    # Verify it's gone
    try:
        api_get(f"/stories/{test_id}")
        fail("story should not exist after delete")
    except urllib.error.HTTPError as e:
        assert e.code == 404, f"expected 404 after delete, got {e.code}"
        ok("story deleted and confirmed gone")
except Exception as e:
    fail(str(e))

print("\n" + "=" * 50)
print("T10: POST /api/stories with invalid genre")
print("=" * 50)
try:
    req = urllib.request.Request(
        f"{BASE}/stories",
        data=json.dumps({"title": "test", "genre": "invalid_genre", "style": "悬疑紧绷", "target_chapters": 5}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    resp = urllib.request.urlopen(req, timeout=10)
    fail("should have returned 400")
except urllib.error.HTTPError as e:
    error_body = json.loads(e.read())
    ok(f"400 returned: {error_body.get('detail','')[:80]}")

print("\n" + "=" * 50)
print(f"RESULTS: {PASS} passed, {FAIL} failed, {PASS+FAIL} total")
print("=" * 50)

sys.exit(0 if FAIL == 0 else 1)
