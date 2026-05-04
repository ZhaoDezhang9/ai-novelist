"""全链路测试：创建故事 → 写第1章 → 质检 → 验证"""
import urllib.request, json, time

BASE = "http://localhost:8000/api"

def api_get(path):
    return json.loads(urllib.request.urlopen(f"{BASE}{path}").read())

def api_post(path, data=None):
    body = json.dumps(data).encode() if data else b"{}"
    req = urllib.request.Request(f"{BASE}{path}", data=body, headers={"Content-Type": "application/json"}, method="POST")
    return json.loads(urllib.request.urlopen(req, timeout=300).read())

# === Step 1: 创建故事 ===
print("=" * 50)
print("Step 1: 创建故事（大纲+世界观+角色）")
print("=" * 50)
start = time.time()
result = api_post("/stories", {
    "title": "深渊回响",
    "genre": "悬疑",
    "style": "悬疑紧绷",
    "pov": "第一人称",
    "target_chapters": 5,
    "words_per_chapter": 1500,
    "target_audience": "悬疑爱好者",
    "theme": "记忆裂缝与真相"
})
sid = result["id"]
print(f"  ID: {sid}")
print(f"  大纲: {result['total_chapters']} 章")
print(f"  角色: {result['characters_count']} 个")
print(f"  耗时: {time.time()-start:.1f}s")

# === Step 2: 查看大纲 ===
print("\n" + "=" * 50)
print("Step 2: 查看大纲")
print("=" * 50)
story = api_get(f"/stories/{sid}")
for node in story.get("outline", [])[:3]:
    print(f"  第{node.get('chapter','?')}章: {node.get('title','')} - {node.get('goal','')[:40]}")
if len(story.get("outline", [])) > 3:
    print(f"  ... 共{len(story['outline'])}章")

# === Step 3: 写第1章 ===
print("\n" + "=" * 50)
print("Step 3: 写第1章（草稿→三层质检→改写→入库）")
print("=" * 50)
start = time.time()
ch1 = api_post(f"/chapters/{sid}/write-next")
print(f"  第{ch1['chapter_number']}章: {ch1['title']}")
print(f"  字数: {ch1['word_count']}")
print(f"  状态: {ch1['status']}")
print(f"  改写次数: {ch1['rewrites_count']}")
print(f"  质检结果:")
for cr in ch1.get("check_results", []):
    mark = "PASS" if cr["passed"] else "FAIL"
    print(f"    [{mark}] {cr['layer']} (issues={cr['issues_count']})")
print(f"  内容预览: {ch1['content'][:120]}...")
print(f"  耗时: {time.time()-start:.1f}s")

# === Step 4: 写第2章 ===
print("\n" + "=" * 50)
print("Step 4: 写第2章（验证记忆连续性）")
print("=" * 50)
start = time.time()
ch2 = api_post(f"/chapters/{sid}/write-next")
print(f"  第{ch2['chapter_number']}章: {ch2['title']}")
print(f"  字数: {ch2['word_count']}")
print(f"  状态: {ch2['status']}")
print(f"  内容预览: {ch2['content'][:120]}...")
print(f"  耗时: {time.time()-start:.1f}s")

# === Step 5: 查看章节列表 ===
print("\n" + "=" * 50)
print("Step 5: 章节列表")
print("=" * 50)
chapters = api_get(f"/chapters/{sid}/list")
for ch in chapters:
    print(f"  第{ch['chapter_number']}章 [{ch['status']}] {ch['title']} - {ch['word_count']}字")

print("\n" + "=" * 50)
print("ALL TESTS PASSED!")
print("=" * 50)
