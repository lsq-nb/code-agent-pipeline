"""
API 服务层 - FastAPI 应用
提供 RESTful 接口，暴露流水线功能
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ..config import get_config
from .routers import health_router, pipeline_router, task_router

app = FastAPI(
    title="代码研发辅助多智能体流水线",
    description="基于 LangGraph+CrewAI 的全流程代码研发辅助系统",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(health_router, prefix="/api/health", tags=["健康检查"])
app.include_router(pipeline_router, prefix="/api/pipeline", tags=["流水线"])
app.include_router(task_router, prefix="/api/tasks", tags=["任务管理"])


@app.on_event("startup")
async def startup_event():
    """服务启动时的初始化"""
    config = get_config()
    print("[Pipeline] 服务启动，配置加载完成")
    print(f"[Pipeline] LLM: {config.llm.provider}/{config.llm.model}")
    print(f"[Pipeline] 端口: {config.port}")


@app.on_event("shutdown")
async def shutdown_event():
    """服务关闭时的清理"""
    print("[Pipeline] 服务关闭")


def serve():
    """启动服务入口点"""
    import uvicorn  # noqa: PLC0415 (局部导入)

    config = get_config()
    uvicorn.run(
        "code_agent_pipeline.api.main:app",
        host=config.host,
        port=config.port,
        reload=config.debug,
    )
