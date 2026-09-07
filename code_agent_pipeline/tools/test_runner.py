"""
测试执行工具
用于运行单元测试和集成测试
"""

import subprocess
from pathlib import Path
from typing import Any, Optional

from .base import ToolBase, ToolResult


class TestRunnerTool(ToolBase):
    """测试执行工具"""

    name = "test_runner"
    description = (
        "测试执行工具：运行 pytest 测试套件，支持按路径/标记/模式筛选，"
        "生成覆盖率报告，返回测试结果摘要。"
    )

    def execute(self, action: str, path: str = ".", **kwargs: Any) -> ToolResult:
        """
        执行测试操作

        支持的 action:
        - run: 运行测试
        - coverage: 生成覆盖率报告
        - list: 列出可用测试
        """
        action_map = {
            "run": self._run,
            "coverage": self._coverage,
            "list": self._list,
        }

        handler = action_map.get(action)
        if not handler:
            return ToolResult.fail(f"未知的测试操作: {action}")

        target = Path(path)
        try:
            result = handler(target, **kwargs)
            return ToolResult.ok(data=result)
        except Exception as e:
            return ToolResult.fail(error=f"测试执行失败: {str(e)}")

    def _run(self, path: Path, mark: Optional[str] = None,
             pattern: Optional[str] = None) -> dict:
        """运行测试"""
        cmd = ["pytest", str(path), "-v", "--tb=short"]

        if mark:
            cmd.extend(["-m", mark])
        if pattern:
            cmd.extend(["-k", pattern])

        result = subprocess.run(cmd, capture_output=True, text=True)

        # 解析结果
        passed = result.stdout.count(" PASSED")
        failed = result.stdout.count(" FAILED")
        skipped = result.stdout.count(" SKIPPED")

        return {
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "command": " ".join(cmd),
            "output": result.stdout,
            "error": result.stderr,
            "success": failed == 0,
        }

    def _coverage(self, path: Path) -> dict:
        """生成覆盖率报告"""
        cmd = [
            "pytest", str(path),
            "--cov=.",
            "--cov-report=term-missing",
            "--cov-report=html:htmlcov",
            "-v",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return {
            "output": result.stdout,
            "error": result.stderr,
            "report_path": "htmlcov/index.html",
        }

    def _list(self, path: Path) -> list[str]:
        """列出可用测试"""
        cmd = ["pytest", str(path), "--collect-only", "--quiet"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        tests = []
        for line in result.stdout.splitlines():
            if line.strip().startswith("test_") or "/test_" in line:
                tests.append(line.strip())
        return tests[:100]
