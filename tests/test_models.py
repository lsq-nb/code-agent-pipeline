from multi_agent_pipeline import MultiAgentPipeline
from multi_agent_pipeline.models import PipelineState, PipelineStage, TaskStatus

state = PipelineState(
    requirement="开发一个用户认证系统",
    project_context="Python FastAPI 项目",
    constraints=["支持 JWT 认证", "密码加密存储"],
    task_id="test_001",
    status=TaskStatus.RUNNING,
)

assert state.current_stage == PipelineStage.ANALYZE
assert state.task_id == "test_001"
assert len(state.agent_messages) == 0

state.add_message("test_agent", "Hello")
assert len(state.agent_messages) == 1
assert state.agent_messages[0]["agent"] == "test_agent"

state.update_timestamp()
assert state.updated_at > state.created_at

print("✓ PipelineState 基础功能测试通过")
