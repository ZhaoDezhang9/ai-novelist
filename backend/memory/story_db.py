"""故事状态持久化 - SQLite (aiosqlite) + WAL + migration"""
import json
import hashlib
import aiosqlite
from pathlib import Path
from contextlib import asynccontextmanager
from backend.core.config import get_settings

DB_PATH: Path = get_settings().data_dir / get_settings().stories_file

MIGRATIONS = [
    (1, """
        CREATE TABLE IF NOT EXISTS schema_versions (
            version INTEGER PRIMARY KEY,
            applied_at TEXT NOT NULL
        );
    """),
    (2, """
        CREATE INDEX IF NOT EXISTS idx_stories_updated_at ON stories(updated_at);
        CREATE INDEX IF NOT EXISTS idx_chapters_updated_at ON chapters(updated_at);
    """),
    (3, """
        CREATE TABLE IF NOT EXISTS memory_cache (
            story_id TEXT NOT NULL,
            cache_key TEXT NOT NULL,
            data TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            PRIMARY KEY (story_id, cache_key)
        );
    """),
    (4, """
        CREATE TABLE IF NOT EXISTS llm_cache (
            story_id TEXT NOT NULL,
            operation TEXT NOT NULL,
            content_hash TEXT NOT NULL,
            response TEXT NOT NULL,
            created_at TEXT NOT NULL,
            PRIMARY KEY (story_id, operation, content_hash)
        );
    """),
    (5, """
        CREATE INDEX IF NOT EXISTS idx_chapters_story_num ON chapters(story_id, chapter_number);
    """),
    (6, """
        -- 删除重复章节，保留每个(story_id, chapter_number)最新的那条
        DELETE FROM chapters WHERE rowid NOT IN (
            SELECT MAX(rowid) FROM chapters GROUP BY story_id, chapter_number
        );
        -- 添加唯一约束
        CREATE UNIQUE INDEX IF NOT EXISTS idx_chapters_story_chapter_unique
            ON chapters(story_id, chapter_number);
    """),
]


@asynccontextmanager
async def get_db():
    db = await aiosqlite.connect(str(DB_PATH))
    db.row_factory = aiosqlite.Row
    try:
        yield db
    finally:
        await db.close()


async def init_db():
    """初始化数据库表 + 执行迁移"""
    async with get_db() as db:
        await db.execute("PRAGMA journal_mode=WAL")
        await db.execute("PRAGMA synchronous=NORMAL")
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

    current_version = await _get_schema_version()
    for version, sql in MIGRATIONS:
        if version > current_version:
            async with get_db() as db:
                await db.executescript(sql)
                await db.execute(
                    "INSERT OR REPLACE INTO schema_versions (version, applied_at) VALUES (?, datetime('now'))",
                    (version,),
                )
                await db.commit()


async def _get_schema_version() -> int:
    try:
        async with get_db() as db:
            async with db.execute("SELECT MAX(version) FROM schema_versions") as cursor:
                row = await cursor.fetchone()
                return row[0] if row and row[0] is not None else 0
    except Exception:
        return 0


# --- Story CRUD ---

async def save_story(story_id: str, data: dict):
    from datetime import datetime
    now = datetime.now().isoformat()
    async with get_db() as db:
        await db.execute(
            """INSERT INTO stories (id, data, created_at, updated_at) VALUES (?, ?, ?, ?)
               ON CONFLICT(id) DO UPDATE SET data=excluded.data, updated_at=excluded.updated_at""",
            (story_id, json.dumps(data, ensure_ascii=False), now, now),
        )
        await db.commit()


async def load_story(story_id: str) -> dict | None:
    async with get_db() as db:
        async with db.execute("SELECT data FROM stories WHERE id=?", (story_id,)) as cursor:
            row = await cursor.fetchone()
            return json.loads(row[0]) if row else None


async def list_stories() -> list[dict]:
    async with get_db() as db:
        async with db.execute(
            "SELECT id, data FROM stories ORDER BY updated_at DESC"
        ) as cursor:
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
        await db.execute("DELETE FROM memory_cache WHERE story_id=?", (story_id,))
        await db.execute("DELETE FROM llm_cache WHERE story_id=?", (story_id,))
        await db.commit()


# --- Chapter CRUD ---

async def save_chapter(story_id: str, chapter_number: int, data: dict):
    from datetime import datetime
    now = datetime.now().isoformat()
    chapter_id = data.get("id", f"{story_id}_ch{chapter_number}")
    async with get_db() as db:
        await db.execute(
            """INSERT INTO chapters (id, story_id, chapter_number, data, content, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(story_id, chapter_number) DO UPDATE SET
                   id=excluded.id,
                   data=excluded.data,
                   content=excluded.content,
                   updated_at=excluded.updated_at""",
            (chapter_id, story_id, chapter_number,
             json.dumps(data, ensure_ascii=False), data.get("content", ""), now, now),
        )
        await db.commit()


async def load_chapter(story_id: str, chapter_number: int) -> dict | None:
    async with get_db() as db:
        async with db.execute(
            "SELECT data, content FROM chapters WHERE story_id=? AND chapter_number=? ORDER BY updated_at DESC LIMIT 1",
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
            "INSERT INTO outlines (story_id, data) VALUES (?, ?) ON CONFLICT(story_id) DO UPDATE SET data=excluded.data",
            (story_id, json.dumps(data, ensure_ascii=False)),
        )
        await db.commit()


async def load_outline(story_id: str) -> list[dict] | None:
    async with get_db() as db:
        async with db.execute(
            "SELECT data FROM outlines WHERE story_id=?", (story_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return json.loads(row[0]) if row else None


# --- World Bible CRUD ---

async def save_world_bible(story_id: str, data: dict):
    async with get_db() as db:
        await db.execute(
            "INSERT INTO world_bible (story_id, data) VALUES (?, ?) ON CONFLICT(story_id) DO UPDATE SET data=excluded.data",
            (story_id, json.dumps(data, ensure_ascii=False)),
        )
        await db.commit()


async def load_world_bible(story_id: str) -> dict | None:
    async with get_db() as db:
        async with db.execute(
            "SELECT data FROM world_bible WHERE story_id=?", (story_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return json.loads(row[0]) if row else None


# --- Memory Cache (持久化) ---

async def save_memory_cache(story_id: str, cache_key: str, data: dict):
    from datetime import datetime
    now = datetime.now().isoformat()
    async with get_db() as db:
        await db.execute(
            """INSERT INTO memory_cache (story_id, cache_key, data, updated_at) VALUES (?, ?, ?, ?)
               ON CONFLICT(story_id, cache_key) DO UPDATE SET data=excluded.data, updated_at=excluded.updated_at""",
            (story_id, cache_key, json.dumps(data, ensure_ascii=False), now),
        )
        await db.commit()


async def load_memory_cache(story_id: str, cache_key: str) -> dict | None:
    async with get_db() as db:
        async with db.execute(
            "SELECT data FROM memory_cache WHERE story_id=? AND cache_key=?",
            (story_id, cache_key),
        ) as cursor:
            row = await cursor.fetchone()
            return json.loads(row[0]) if row else None


async def load_all_memory_cache(story_id: str) -> dict:
    """加载故事的所有memory缓存"""
    async with get_db() as db:
        async with db.execute(
            "SELECT cache_key, data FROM memory_cache WHERE story_id=?",
            (story_id,),
        ) as cursor:
            rows = await cursor.fetchall()
            return {row[0]: json.loads(row[1]) for row in rows}


# --- LLM Cache ---

def _content_hash(operation: str, story_id: str, content: str) -> str:
    return hashlib.md5(f"{operation}:{story_id}:{content[:500]}".encode()).hexdigest()


async def load_llm_cache(story_id: str, operation: str, content: str) -> str | None:
    h = _content_hash(operation, story_id, content)
    async with get_db() as db:
        async with db.execute(
            "SELECT response FROM llm_cache WHERE story_id=? AND operation=? AND content_hash=?",
            (story_id, operation, h),
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None


async def save_llm_cache(story_id: str, operation: str, content: str, response: str):
    from datetime import datetime
    h = _content_hash(operation, story_id, content)
    async with get_db() as db:
        await db.execute(
            "INSERT OR IGNORE INTO llm_cache (story_id, operation, content_hash, response, created_at) VALUES (?, ?, ?, ?, ?)",
            (story_id, operation, h, response, datetime.now().isoformat()),
        )
        await db.commit()
