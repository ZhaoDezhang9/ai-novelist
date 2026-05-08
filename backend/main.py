"""AI Novelist - 全自动AI小说创作系统

全流程闭环：大纲→逐章写作→多层防御质控→记忆上下文→伏笔管理
"""
import os
from uuid import uuid4
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from backend.core.config import get_settings
from backend.core.auth import verify_api_key
from backend.core.logging import setup_logging, get_logger, correlation_id_var
from backend.memory.story_db import init_db
from backend.api.stories import router as stories_router
from backend.api.chapters import router as chapters_router
from backend.api.settings import router as settings_router
from backend.api.export import router as export_router

setup_logging()
log = get_logger(component="main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    await init_db()
    log.info("app_startup", data_dir=str(settings.data_dir))
    yield
    log.info("app_shutdown")


app = FastAPI(
    title="AI Novelist",
    description="全自动AI小说创作系统 - 闭环流水线",
    version="1.1.0",
    lifespan=lifespan,
)

# Rate limiting
limiter = Limiter(key_func=get_remote_address, default_limits=[get_settings().rate_limit])
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]

# CORS from env
settings = get_settings()
origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)


# Correlation ID middleware
@app.middleware("http")
async def add_correlation_id(request: Request, call_next):
    cid = request.headers.get("X-Correlation-ID", str(uuid4()))
    correlation_id_var.set(cid)
    log.info("request_start", method=request.method, path=request.url.path)
    response = await call_next(request)
    response.headers["X-Correlation-ID"] = cid
    log.info("request_end", status_code=response.status_code)
    return response


# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    import traceback
    log.error("unhandled_exception", path=request.url.path, error=str(exc), traceback=traceback.format_exc())
    from fastapi.responses import JSONResponse
    return JSONResponse(status_code=500, content={"detail": f"服务器错误: {exc}"})


# API 路由 (with auth)
app.include_router(stories_router, prefix="/api/stories", tags=["Stories"], dependencies=[Depends(verify_api_key)])
app.include_router(chapters_router, prefix="/api/chapters", tags=["Chapters"], dependencies=[Depends(verify_api_key)])
app.include_router(settings_router, prefix="/api/settings", tags=["Settings"], dependencies=[Depends(verify_api_key)])
app.include_router(export_router, prefix="/api/stories", tags=["Stories"], dependencies=[Depends(verify_api_key)])

@app.get("/api/health")
async def health():
    """深度健康检查 — DB + LLM API 可达性"""
    import time
    from backend.memory import story_db

    result = {
        "status": "ok",
        "system": "AI Novelist",
        "checks": {},
    }

    # DB check
    start = time.monotonic()
    try:
        await story_db.list_stories()
        result["checks"]["database"] = {"status": "ok", "latency_ms": round((time.monotonic() - start) * 1000, 2)}
    except Exception as e:
        result["checks"]["database"] = {"status": "error", "detail": str(e)}
        result["status"] = "degraded"

    # LLM API check
    start = time.monotonic()
    try:
        from backend.core.llm_client import LLMClient
        client = LLMClient(tier="assessment")
        await client.chat("健康检查", "回复 OK", temperature=0, max_tokens=10)
        result["checks"]["llm_api"] = {"status": "ok", "latency_ms": round((time.monotonic() - start) * 1000, 2)}
    except Exception as e:
        result["checks"]["llm_api"] = {"status": "error", "detail": str(e)}
        result["status"] = "degraded"

    return result


# 前端静态文件（必须在所有路由之后）
dist_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
if os.path.isdir(dist_path):
    app.mount("/", StaticFiles(directory=dist_path, html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
