"""AI Novelist - 全自动AI小说创作系统

全流程闭环：大纲→逐章写作→多层防御质控→记忆上下文→伏笔管理
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from backend.core.config import get_settings
from backend.memory.story_db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动：初始化数据库
    settings = get_settings()
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    await init_db()
    yield
    # 关闭：清理资源
    pass


app = FastAPI(
    title="AI Novelist",
    description="全自动AI小说创作系统 - 闭环流水线",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# API 路由
from backend.api.stories import router as stories_router
from backend.api.chapters import router as chapters_router
from backend.api.settings import router as settings_router

app.include_router(stories_router, prefix="/api/stories", tags=["Stories"])
app.include_router(chapters_router, prefix="/api/chapters", tags=["Chapters"])
app.include_router(settings_router, prefix="/api/settings", tags=["Settings"])


@app.get("/api/health")
async def health():
    return {"status": "ok", "system": "AI Novelist"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
