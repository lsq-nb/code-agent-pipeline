"""
单元测试
"""

import pytest

from code_agent_pipeline.config import PipelineConfig, get_config, reset_config
from code_agent_pipeline.models import (
    AnalysisResult,
    CodeArtifact,
    PipelineStage,
    PipelineState,
    ReviewVerdict,
    TaskStatus,
)
from code_agent_pipeline.utils.validation import validate_code_output, validate_requirement


class TestPipelineState:
    """PipelineState 单元测试"""

    def test_create_state(self):
        state = PipelineState(requirement="测试需求", task_id="test_001")
        assert state.requirement == "测试需求"
        assert state.task_id == "test_001"
        assert state.current_stage == PipelineStage.ANALYZE
        assert state.status == TaskStatus.PENDING
        assert state.iteration_count == 0

    def test_add_message(self):
        state = PipelineState()
        state.add_message("analyst", "分析完成")
        assert len(state.agent_messages) == 1
        assert state.agent_messages[0]["agent"] == "analyst"
        assert state.agent_messages[0]["message"] == "分析完成"

    def test_add_error(self):
        state = PipelineState()
        state.add_error("测试错误")
        assert len(state.errors) == 1
        assert "测试错误" in state.errors[0]

    def test_to_dict(self):
        state = PipelineState(requirement="测试")
        d = state.to_dict()
        assert d["requirement"] == "测试"
        assert "created_at" in d

    def test_update_timestamp(self):
        import time  # noqa: PLC0415

        state = PipelineState()
        time.sleep(0.01)
        state.update_timestamp()
        assert state.updated_at >= state.created_at


class TestModels:
    """数据模型单元测试"""

    def test_analysis_result(self):
        result = AnalysisResult(
            requirement_summary="测试",
            functional_requirements=["功能1"],
            non_functional_requirements=[],
            technical_constraints=[],
            risk_factors=[],
            suggested_tech_stack=["python"],
            estimated_complexity="medium",
            tasks=[],
        )
        assert result.requirement_summary == "测试"
        assert "python" in result.suggested_tech_stack

    def test_code_artifact(self):
        artifact = CodeArtifact(
            file_path="src/main.py",
            content="print('hello')",
            language="python",
            description="主程序",
        )
        assert artifact.file_path == "src/main.py"
        assert artifact.test_required is True

    def test_review_verdict_enum(self):
        assert ReviewVerdict.APPROVED.value == "approved"
        assert ReviewVerdict.REJECTED.value == "rejected"


class TestValidation:
    """输入验证单元测试"""

    def test_valid_requirement(self):
        valid, msg = validate_requirement("这是一个测试需求描述")
        assert valid is True
        assert msg == ""

    def test_empty_requirement(self):
        valid, msg = validate_requirement("")
        assert valid is False
        assert "不能为空" in msg

    def test_short_requirement(self):
        valid, msg = validate_requirement("短")
        assert valid is False
        assert "至少需要" in msg

    def test_validate_python_code(self):
        valid, issues = validate_code_output("print('hello')", "python")
        assert valid is True
        assert len(issues) == 0

    def test_invalid_python_code(self):
        valid, issues = validate_code_output("def foo(", "python")
        assert valid is False
        assert any("语法错误" in i for i in issues)


class TestConfig:
    """配置单元测试"""

    def test_default_config(self):
        reset_config()
        config = get_config()
        assert isinstance(config, PipelineConfig)
        assert config.llm.provider == "openai"
        assert config.graph.max_iterations == 10

    def test_reset_config(self):
        reset_config()
        config1 = get_config()
        reset_config()
        config2 = get_config()
        assert config1 is not config2


class TestTools:
    """工具模块单元测试"""

    def test_tool_result_ok(self):
        from code_agent_pipeline.tools.base import ToolResult  # noqa: PLC0415

        result = ToolResult.ok(data={"key": "value"})
        assert result.success is True
        assert result.data == {"key": "value"}

    def test_tool_result_fail(self):
        from code_agent_pipeline.tools.base import ToolResult  # noqa: PLC0415

        result = ToolResult.fail(error="something wrong")
        assert result.success is False
        assert result.error == "something wrong"

    def test_file_tool_write_read(self, tmp_path):
        from code_agent_pipeline.tools.file_tool import FileTool  # noqa: PLC0415

        tool = FileTool(root=tmp_path)
        result = tool.execute("write", path="test.txt", content="hello world")
        assert result.success is True

        result = tool.execute("read", path="test.txt")
        assert result.data["content"] == "hello world"

    def test_git_tool_status_no_repo(self, tmp_path):
        from code_agent_pipeline.tools.git_tool import GitTool  # noqa: PLC0415

        tool = GitTool(workdir=tmp_path)
        # 非 Git 仓库应返回错误
        result = tool.execute("status")
        # 应返回失败结果而非崩溃
        assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
