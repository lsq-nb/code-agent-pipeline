"""
流水线路由
处理流水线执行的 HTTP 请求
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..models import PipelineState, RequirementInput, PipelineResponse, PipelineStage
from ..graph import compile_pipeline

router = APIRouter()

# 运行时状态存储（生产环境应使用数据库）
_active_tasks: dict[str, PipelineState] = {}
compiled_graph = None


class PipelineRequest(BaseModel):
    """流水线执行请求"""
    requirement: str
    project_context: str = ""
    constraints: list[str] = []
    extra_instructions: str = ""


@router.post("/run", response_model=PipelineResponse)
async def run_pipeline(req: PipelineRequest):
    """
    执行完整流水线

    提交一个开发需求，系统将自动完成：
    需求分析 → 架构设计 → 代码生成 → 代码审查 → 文档生成 → 测试

    返回:
        PipelineResponse: 执行结果
    """
    global compiled_graph
    if compiled_graph is None:
        compiled_graph = compile_pipeline()

    # 创建任务状态
    task_id = f"task_{len(_active_tasks) + 1:04d}"
    state = PipelineState(
        requirement=req.requirement,
        project_context=req.project_context,
        constraints=req.constraints,
        task_id=task_id,
        status=TaskStatus.RUNNING,
    )
    _active_tasks[task_id] = state

    try:
        # 运行流水线
        result = compiled_graph.invoke(state)
        final_state = PipelineState(**result)
        final_state.status = TaskStatus.COMPLETED
        _active_tasks[task_id] = final_state

        return PipelineResponse(
            success=True,
            task_id=task_id,
            stage=final_state.current_stage.value,
            status=final_state.status.value,
            message="流水线执行完成",
            result=final_state.to_dict(),
        )
    except Exception as e:
        state.status = TaskStatus.FAILED
        state.add_error(str(e))
        _active_tasks[task_id] = state
        raise HTTPException(status_code=500, detail=f"流水线执行失败: {str(e)}")


@router.get("/status/{task_id}")
async def get_task_status(task_id: str):
    """查询任务执行状态"""
    state = _active_tasks.get(task_id)
    if not state:
        raise HTTPException(status_code=404, detail="任务不存在")
    return {
        "task_id": task_id,
        "status": state.status.value,
        "stage": state.current_stage.value,
        "iteration_count": state.iteration_count,
        "errors": state.errors,
        "message_count": len(state.agent_messages),
    }


@router.get("/stages")
async def get_available_stages():
    """获取可用阶段列表"""
    return {
        "stages": [s.value for s in PipelineStage],
        "default_order": [
            PipelineStage.ANALYZE.value,
            PipelineStage.DESIGN.value,
            PipelineStage.CODE.value,
            PipelineStage.REVIEW.value,
            PipelineStage.DOCUMENT.value,
            PipelineStage.TEST.value,
        ],
    }
