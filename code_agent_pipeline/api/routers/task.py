"""
任务管理路由
处理任务的创建、查询、历史管理等
"""

from fastapi import APIRouter

from ...models import TaskHistoryItem, TaskStatus

router = APIRouter()


@router.get("/history")
async def get_task_history(limit: int = 20):
    """获取历史任务列表"""
    # 实际应从数据库查询
    return {
        "tasks": [],
        "total": 0,
        "limit": limit,
    }


@router.delete("/task/{task_id}")
async def cancel_task(task_id: str):
    """取消任务"""
    return {"task_id": task_id, "status": "cancelled"}


@router.get("/stats")
async def get_task_stats():
    """获取任务统计信息"""
    return {
        "total_tasks": 0,
        "completed": 0,
        "failed": 0,
        "running": 0,
    }
