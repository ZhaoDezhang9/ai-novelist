import urllib.request, json, time, os
import pytest

BASE = os.environ.get("API_BASE", "http://localhost:8000")

def _check_server():
    try:
        urllib.request.urlopen(f"{BASE}/api/health", timeout=5)
        return True
    except Exception:
        return False

server_available = _check_server()
skip_if_down = pytest.mark.skipif(not server_available, reason="Server not running")


def test_health():
    resp = urllib.request.urlopen(f"{BASE}/api/health")
    data = json.loads(resp.read())
    assert resp.status == 200
    print("Health:", data)


def test_list_stories():
    resp = urllib.request.urlopen(f"{BASE}/api/stories")
    stories = json.loads(resp.read())
    assert resp.status == 200
    assert isinstance(stories, list)
    print(f"Stories: {len(stories)}")


@skip_if_down
def test_create_story():
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
        f"{BASE}/api/stories",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    start = time.time()
    try:
        resp = urllib.request.urlopen(req, timeout=600)
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

        assert resp.status == 200
        print("\n=== SUCCESS: Story fully created ===")
    except Exception as e:
        elapsed = time.time() - start
        pytest.fail(f"Create story failed after {elapsed:.1f}s: {e}")
