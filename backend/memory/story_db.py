"""故事状态持久化 - SQLite (aiosqlite)"""
import json
import aiosqlite
from pathlib import Path
from contextlib import asynccontextmanager
from backend.core.config import get_settings

DB_PATH: Path = get_settings().data_dir / get_settings().stories_file


@asynccontextmanager
async def get_db():
    """数据库连接上下文管理器"""
    db = await aiosqlite.connect(str(DB_PATH))
    db.row_factory = aiosqlite.Row
    try:
        yield db
    finally:
        await db.close()


async def init_db():
    """初始化数据库表"""
    async with get_db() as db:
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS stories (
                id TEXT PRIMARY KEY,
                data TEXT NOT NULL,
                created_at TEXT,
                updated_at TEXT
            );
            CREATE TABLE IF NOT EXISTS chapters (
                id TEXT PRIMARY KEY,
                story_id TEXT NOT NULL,
                chapter_number INTEGER NOT NULL,
                data TEXT NOT NULL,
                content TEXT DEFAULT '',
                created_at TEXT,
                updated_at TEXT,
                FOREIGN KEY (story_id) REFERENCES stories(id)
            );
            CREATE INDEX IF NOT EXISTS idx_chapters_story 
                ON chapters(story_id, chapter_number);
            CREATE TABLE IF NOT EXISTS outlines (
                story_id TEXT PRIMARY KEY,
                data TEXT NOT NULL,
                FOREIGN KEY (story_id) REFERENCES stories(id)
            );
            CREATE TABLE IF NOT EXISTS world_bible (
                story_id TEXT PRIMARY KEY,
                data TEXT NOT NULL,
                FOREIGN KEY (story_id) REFERENCES stories(id)
            );
        """)
        await db.commit()


# --- Story CRUD ---

async def save_story(story_id: str, data: dict):
    from datetime import datetime
    now = datetime.now().isoformat()
    async with get_db() as db:
        await db.execute(
            "INSERT OR REPLACE INTO stories (id, data, created_at, updated_at) VALUES (?, ?, COALESCE((SELECT created_at FROM stories WHERE id=?), ?), ?)",
            (story_id, json.dumps(data, ensure_ascii=False), story_id, now, now),
        )
        await db.commit()


async def load_story(story_id: str) -> dict | None:
    async with get_db() as db:
        async with db.execute("SELECT data FROM stories WHERE id=?", (story_id,)) as cursor:
            row = await cursor.fetchone()
            return json.loads(row[0]) if row else None


async def list_stories() -> list[dict]:
    async with get_db() as db:
        async with db.execute("SELECT id, data FROM stories ORDER BY updated_at DESC") as cursor:
            rows = await cursor.fetchall()
            results = []
            for row in rows:
                item = json.loads(row[1])
                item["id"] = row[0]
                results.append(item)
            return results


async def delete_story(story_id: str):
    async with get_db() as db:
        await db.execute("DELETE FROM stories WHERE id=?", (story_id,))
        await db.execute("DELETE FROM chapters WHERE story_id=?", (story_id,))
        await db.execute("DELETE FROM outlines WHERE story_id=?", (story_id,))
        await db.execute("DELETE FROM world_bible WHERE story_id=?", (story_id,))
        await db.commit()


# --- Chapter CRUD ---

async def save_chapter(story_id: str, chapter_number: int, data: dict):
    from datetime import datetime
    now = datetime.now().isoformat()
    chapter_id = data.get("id", f"{story_id}_ch{chapter_number}")
    async with get_db() as db:
        await db.execute(
            "INSERT OR REPLACE INTO chapters (id, story_id, chapter_number, data, content, created_at, updated_at) VALUES (?, ?, ?, ?, ?, COALESCE((SELECT created_at FROM chapters WHERE id=?), ?), ?)",
            (
                chapter_id, story_id, chapter_number,
                json.dumps(data, ensure_ascii=False),
                data.get("content", ""),
                chapter_id, now, now,
            ),
        )
        await db.commit()


async def load_chapter(story_id: str, chapter_number: int) -> dict | None:
    async with get_db() as db:
        async with db.execute(
            "SELECT data, content FROM chapters WHERE story_id=? AND chapter_number=?",
            (story_id, chapter_number),
        ) as cursor:
            row = await cursor.fetchone()
            if not row:
                return None
            data = json.loads(row[0])
            data["content"] = row[1]
            return data


async def load_all_chapters(story_id: str) -> list[dict]:
    async with get_db() as db:
        async with db.execute(
            "SELECT data, content FROM chapters WHERE story_id=? ORDER BY chapter_number",
            (story_id,),
        ) as cursor:
            rows = await cursor.fetchall()
            results = []
            for row in rows:
                data = json.loads(row[0])
                data["content"] = row[1]
                results.append(data)
            return results


# --- Outline CRUD ---

async def save_outline(story_id: str, data: list[dict]):
    async with get_db() as db:
        await db.execute(
            "INSERT OR REPLACE INTO outlines (story_id, data) VALUES (?, ?)",
            (story_id, json.dumps(data, ensure_ascii=False)),
        )
        await db.commit()


async def load_outline(story_id: str) -> list[dict] | None:
    async with get_db() as db:
        async with db.execute("SELECT data FROM outlines WHERE story_id=?", (story_id,)) as cursor:
            row = await cursor.fetchone()
            return json.loads(row[0]) if row else None


# --- World Bible CRUD ---

async def save_world_bible(story_id: str, data: dict):
    async with get_db() as db:
        await db.execute(
            "INSERT OR REPLACE INTO world_bible (story_id, data) VALUES (?, ?)",
            (story_id, json.dumps(data, ensure_ascii=False)),
        )
        await db.commit()


async def load_world_bible(story_id: str) -> dict | None:
    async with get_db() as db:
        async with db.execute("SELECT data FROM world_bible WHERE story_id=?", (story_id,)) as cursor:
            row = await cursor.fetchone()
            return json.loads(row[0]) if row else None
