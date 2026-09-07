"""
工具基类与基础类型定义
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class ToolResult:
    """工具调用结果"""

    success: bool
    data: Any = None
    error: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_success(self) -> bool:
        return self.success

    @classmethod
    def ok(cls, data: Any = None, **kwargs: Any) -> "ToolResult":
        """成功结果"""
        return cls(success=True, data=data, **kwargs)

    @classmethod
    def fail(cls, error: str, **kwargs: Any) -> "ToolResult":
        """失败结果"""
        return cls(success=False, error=error, **kwargs)


class ToolBase(ABC):
    """
    所有工具的抽象基类

    子类需要实现：
    - name: 工具名称（Function Call 中使用）
    - description: 工具描述
    - execute: 实际执行逻辑
    """

    name: str = "base_tool"
    description: str = "基础工具"

    @abstractmethod
    def execute(self, **kwargs: Any) -> ToolResult:
        """执行工具逻辑"""
        ...

    def __call__(self, **kwargs: Any) -> ToolResult:
        """调用工具"""
        try:
            return self.execute(**kwargs)
        except Exception as e:
            return ToolResult.fail(error=f"{type(e).__name__}: {str(e)}")

    def get_function_spec(self) -> dict[str, Any]:
        """
        返回 Function Call 规格描述
        子类可重写以提供更详细的描述
        """
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        }
