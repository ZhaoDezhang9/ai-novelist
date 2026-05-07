"""向量数据库集成 - ChromaDB 嵌入式模式，语义搜索替代字串匹配"""
import logging
import json
from pathlib import Path
from typing import Optional

import chromadb
from chromadb.config import Settings as ChromaSettings

from backend.core.config import get_settings

logger = logging.getLogger(__name__)

COLLECTION_CHAPTERS = "chapter_summaries"
COLLECTION_CHAR_STATES = "character_states"
COLLECTION_WORLD_RULES = "world_rules"
COLLECTION_FORESHADOWING = "foreshadowing"


class VectorStore:
    """ChromaDB 向量存储，嵌入式无需外部服务"""

    def __init__(self, persist_dir: Optional[Path] = None):
        if persist_dir is None:
            persist_dir = get_settings().data_dir / "chroma"
        persist_dir.mkdir(parents=True, exist_ok=True)
        self._client = chromadb.PersistentClient(
            path=str(persist_dir),
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self._collections: dict[str, chromadb.Collection] = {}

    def _get_collection(self, name: str) -> chromadb.Collection:
        if name not in self._collections:
            self._collections[name] = self._client.get_or_create_collection(
                name=name,
                metadata={"hnsw:space": "cosine"},
            )
        return self._collections[name]

    # --- Indexing ---

    def index_chapter(self, story_id: str, chapter_number: int, summary: str, title: str = ""):
        if not summary.strip():
            return
        coll = self._get_collection(COLLECTION_CHAPTERS)
        doc_id = f"{story_id}_ch{chapter_number}"
        coll.upsert(
            documents=[summary],
            metadatas=[{"story_id": story_id, "chapter_number": chapter_number, "title": title}],
            ids=[doc_id],
        )

    def index_character_states(self, story_id: str, states: dict):
        if not states:
            return
        coll = self._get_collection(COLLECTION_CHAR_STATES)
        for name, state in states.items():
            doc_id = f"{story_id}_{name}"
            text = f"{name}: {json.dumps(state, ensure_ascii=False)}"
            coll.upsert(
                documents=[text],
                metadatas=[{"story_id": story_id, "character": name}],
                ids=[doc_id],
            )

    def index_world_rules(self, story_id: str, rules: list[str]):
        if not rules:
            return
        coll = self._get_collection(COLLECTION_WORLD_RULES)
        ids = []
        docs = []
        metas = []
        for i, rule in enumerate(rules):
            ids.append(f"{story_id}_rule{i}")
            docs.append(rule)
            metas.append({"story_id": story_id, "rule_index": i})
        coll.upsert(documents=docs, metadatas=metas, ids=ids)

    def index_foreshadowing(self, story_id: str, items: list[dict]):
        if not items:
            return
        coll = self._get_collection(COLLECTION_FORESHADOWING)
        ids = []
        docs = []
        metas = []
        for item in items:
            fs_id = item.get("id", "")
            if not fs_id:
                continue
            ids.append(fs_id)
            docs.append(item.get("description", ""))
            metas.append({
                "story_id": story_id,
                "planted_chapter": item.get("planted_chapter", 0),
                "status": item.get("status", "unresolved"),
            })
        if ids:
            coll.upsert(documents=docs, metadatas=metas, ids=ids)

    # --- Search ---

    def search(self, story_id: str, query: str, collections: list[str],
               n_results: int = 5) -> dict[str, list[dict]]:
        """语义搜索，返回各collection的匹配结果"""
        results = {}
        where = {"story_id": story_id}
        for name in collections:
            coll = self._get_collection(name)
            try:
                r = coll.query(query_texts=[query], n_results=n_results, where=where)
                items = []
                if r["ids"] and r["ids"][0]:
                    for i, doc_id in enumerate(r["ids"][0]):
                        item = {"id": doc_id, "document": r["documents"][0][i] if r["documents"] else ""}
                        if r["metadatas"] and r["metadatas"][0]:
                            item["metadata"] = r["metadatas"][0][i] or {}
                        if r["distances"] and r["distances"][0]:
                            item["distance"] = r["distances"][0][i]
                        items.append(item)
                results[name] = items
            except Exception as e:
                logger.warning(f"Vector search failed for {name}: {e}")
                results[name] = []
        return results

    def search_all(self, story_id: str, query: str, n_results: int = 3) -> dict:
        """搜索所有collection"""
        return self.search(story_id, query, [
            COLLECTION_CHAPTERS, COLLECTION_CHAR_STATES,
            COLLECTION_WORLD_RULES, COLLECTION_FORESHADOWING,
        ], n_results)

    def search_relevant_context(self, story_id: str, query: str, n_results: int = 5) -> dict:
        """搜索与当前章相关的所有上下文"""
        results = self.search_all(story_id, query, n_results)
        context = {
            "relevant_chapters": [],
            "relevant_characters": [],
            "relevant_rules": [],
            "relevant_foreshadowing": [],
        }
        for item in results.get(COLLECTION_CHAPTERS, []):
            meta = item.get("metadata", {})
            context["relevant_chapters"].append({
                "chapter": meta.get("chapter_number"),
                "summary": item.get("document", ""),
                "score": 1.0 - item.get("distance", 0),
            })
        for item in results.get(COLLECTION_CHAR_STATES, []):
            context["relevant_characters"].append({
                "name": item.get("metadata", {}).get("character"),
                "state": item.get("document", ""),
                "score": 1.0 - item.get("distance", 0),
            })
        for item in results.get(COLLECTION_WORLD_RULES, []):
            context["relevant_rules"].append({
                "rule": item.get("document", ""),
                "score": 1.0 - item.get("distance", 0),
            })
        for item in results.get(COLLECTION_FORESHADOWING, []):
            meta = item.get("metadata", {})
            context["relevant_foreshadowing"].append({
                "id": item.get("id"),
                "description": item.get("document", ""),
                "planted_chapter": meta.get("planted_chapter"),
                "status": meta.get("status"),
                "score": 1.0 - item.get("distance", 0),
            })
        return context

    # --- Cleanup ---

    def delete_story(self, story_id: str):
        for name in [COLLECTION_CHAPTERS, COLLECTION_CHAR_STATES,
                      COLLECTION_WORLD_RULES, COLLECTION_FORESHADOWING]:
            coll = self._get_collection(name)
            try:
                results = coll.get(where={"story_id": story_id})
                if results["ids"]:
                    coll.delete(ids=results["ids"])
            except Exception as e:
                logger.warning(f"Failed to delete vector data for {name}: {e}")


_vector_store: Optional[VectorStore] = None


def get_vector_store() -> VectorStore:
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store
