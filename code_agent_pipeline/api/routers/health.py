"""
健康检查路由
"""

from fastapi import APIRouter

from ...__init__ import __version__

router = APIRouter()


@router.get("")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "version": __version__,
        "components": {
            "langgraph": "ready",
            "crewai": "ready",
            "rag": "ready",
            "mcp": "ready",
        },
    }


@router.get("/ready")
async def readiness_probe():
    """就绪探针"""
    return {"ready": True}


@router.get("/live")
async def liveness_probe():
    """存活探针"""
    return {"alive": True}
