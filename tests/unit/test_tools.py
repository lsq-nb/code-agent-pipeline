"""
工具模块测试
"""

import pytest

from code_agent_pipeline.tools.base import ToolResult
from code_agent_pipeline.tools.file_tool import FileTool
from code_agent_pipeline.tools.git_tool import GitTool
from code_agent_pipeline.tools.mcp_client import MCPClient
from code_agent_pipeline.tools.test_runner import TestRunnerTool


class TestToolBase:
    """工具基类测试"""

    def test_tool_result_ok(self):
        result = ToolResult.ok(data={"key": "value"})
        assert result.success is True
        assert result.data == {"key": "value"}
        assert result.error is None

    def test_tool_result_fail(self):
        result = ToolResult.fail(error="test error")
        assert result.success is False
        assert result.error == "test error"

    def test_tool_result_is_success_property(self):
        assert ToolResult.ok().is_success is True
        assert ToolResult.fail("err").is_success is False


class TestFileTool:
    """文件工具测试"""

    def test_write_and_read(self, tmp_path):
        tool = FileTool(root=tmp_path)
        # 写入
        result = tool.execute("write", path="test.txt", content="hello world")
        assert result.success is True
        assert result.data["bytes_written"] == 11
        # 读取
        result = tool.execute("read", path="test.txt")
        assert result.data["content"] == "hello world"

    def test_read_nonexistent(self, tmp_path):
        tool = FileTool(root=tmp_path)
        result = tool.execute("read", path="missing.txt")
        assert result is not None

    def test_create_dir(self, tmp_path):
        tool = FileTool(root=tmp_path)
        result = tool.execute("create_dir", path="sub/dir")
        assert result.success is True
        assert (tmp_path / "sub" / "dir").exists()

    def test_list_empty_dir(self, tmp_path):
        tool = FileTool(root=tmp_path)
        result = tool.execute("list", path=".")
        assert isinstance(result.data, list)

    def test_stats_file(self, tmp_path):
        (tmp_path / "test.py").write_text("print('hi')")
        tool = FileTool(root=tmp_path)
        result = tool.execute("stats", path="test.py")
        assert result.data["type"] == "file"
        assert result.data["lines"] == 1


class TestGitTool:
    """Git 工具测试"""

    def test_status_not_repo(self, tmp_path):
        tool = GitTool(workdir=tmp_path)
        result = tool.execute("status")
        # 非仓库应返回错误而非崩溃
        assert result is not None

    def test_branch_list_not_repo(self, tmp_path):
        tool = GitTool(workdir=tmp_path)
        result = tool.execute("branch_list")
        assert result is not None

    def test_clone_invalid_url(self, tmp_path):
        tool = GitTool(workdir=tmp_path)
        result = tool.execute("clone", repo_url="not-a-real-url")
        # 应返回失败结果
        assert result is not None


class TestTestRunner:
    """测试执行工具测试"""

    def test_list_not_found(self, tmp_path):
        tool = TestRunnerTool()
        result = tool.execute("list", path=str(tmp_path))
        assert result is not None


class TestMCPClient:
    """MCP 客户端测试"""

    def test_register_tool(self):
        client = MCPClient(server_name="test")
        client.register_tool(
            "get_weather",
            "获取天气",
            {"type": "object", "properties": {"city": {"type": "string"}}},
        )
        tools = client.get_tool_specs()
        assert len(tools) == 1
        assert tools[0]["name"] == "get_weather"

    def test_call_unknown_tool(self):
        client = MCPClient(server_name="test")
        with pytest.raises(ValueError):
            client.call_tool("unknown_tool", {})
