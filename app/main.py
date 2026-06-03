"""FastAPI 应用入口

主应用程序，配置路由、中间件、静态文件等
"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from loguru import logger

from app.api import chat, file, health, interview
from app.config import config
from app.core.chroma_client import chroma_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    logger.info("=" * 60)
    logger.info(f"🚀 {config.app_name} v{config.app_version} 启动中...")
    logger.info(f"📝 环境: {'开发' if config.debug else '生产'}")
    logger.info(f"🌐 监听地址: http://{config.host}:{config.port}")
    logger.info(f"📚 API 文档: http://{config.host}:{config.port}/docs")

    # 初始化 ChromaDB
    logger.info("🔌 正在初始化 ChromaDB...")
    chroma_manager.connect()
    logger.info("✅ ChromaDB 初始化成功")

    logger.info("=" * 60)

    yield

    # 关闭时执行
    logger.info("🔌 正在关闭 ChromaDB 连接...")
    chroma_manager.close()
    logger.info(f"👋 {config.app_name} 关闭")


# 创建 FastAPI 应用
app = FastAPI(
    title=config.app_name,
    version=config.app_version,
    description="通用技术面试智能辅导系统 - RAG + LangGraph",
    lifespan=lifespan,
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(health.router, tags=["健康检查"])
app.include_router(chat.router, prefix="/api", tags=["面试问答"])
app.include_router(file.router, prefix="/api", tags=["知识库管理"])
app.include_router(interview.router, prefix="/api/interview", tags=["面试备考"])

# 挂载静态文件
static_dir = "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/")
async def root():
    """返回首页"""
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {
        "message": f"Welcome to {config.app_name} API",
        "version": config.app_version,
        "docs": "/docs",
    }


@app.get("/interview")
async def interview_page():
    """返回面试备考页面"""
    interview_path = os.path.join(static_dir, "interview.html")
    if os.path.exists(interview_path):
        return FileResponse(interview_path)
    return {"message": "面试页面不存在"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=config.host,
        port=config.port,
        reload=config.debug,
        log_level="info",
    )
