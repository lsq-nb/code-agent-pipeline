"""
工具模块包
"""

from .base import ToolBase, ToolResult
from .file_tool import FileTool
from .code_formatter import CodeFormatterTool
from .test_runner import TestRunnerTool
from .mcp_client import MCPClient

# GitTool 依赖 gitpython，懒加载以避免未安装时报错
_GitTool = None


def __getattr__(name: str):
    global _GitTool
    if name == "GitTool":
        try:
            from .git_tool import GitTool as _GT  # noqa: PLC0415
            _GitTool = _GT
            return _GT
        except ImportError as e:
            raise ImportError(
                "GitTool requires gitpython: pip install gitpython"
            ) from e
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "ToolBase",
    "ToolResult",
    "GitTool",
    "FileTool",
    "CodeFormatterTool",
    "TestRunnerTool",
    "MCPClient",
]
