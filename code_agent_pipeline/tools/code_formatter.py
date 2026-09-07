"""
代码格式化与质量检查工具
集成 black、ruff、mypy 等工具
"""

import re
import subprocess
from pathlib import Path
from typing import Any, Optional

from .base import ToolBase, ToolResult


class CodeFormatterTool(ToolBase):
    """代码格式化与质量检查工具"""

    name = "code_formatter"
    description = (
        "代码格式化与质量检查工具：格式化 Python 代码（black）、"
        "运行 linter（ruff）、类型检查（mypy）、代码复杂度分析等。"
    )

    def execute(self, action: str, path: str = ".", **kwargs: Any) -> ToolResult:
        """
        执行代码格式化或检查操作

        支持的 action:
        - format: 格式化代码（使用 black）
        - lint: 运行 linter（使用 ruff）
        - typecheck: 运行类型检查（使用 mypy）
        - complexity: 分析代码复杂度
        - fix: 自动修复可修复的问题
        """
        action_map = {
            "format": self._format,
            "lint": self._lint,
            "typecheck": self._typecheck,
            "complexity": self._complexity,
            "fix": self._fix,
        }

        handler = action_map.get(action)
        if not handler:
            return ToolResult.fail(f"未知的格式化操作: {action}")

        target = Path(path)
        try:
            result = handler(target)
            return ToolResult.ok(data=result)
        except subprocess.CalledProcessError as e:
            return ToolResult.ok(data={
                "stdout": e.stdout,
                "stderr": e.stderr,
                "returncode": e.returncode,
            })
        except Exception as e:
            return ToolResult.fail(error=f"格式化操作失败: {str(e)}")

    def _format(self, path: Path) -> dict:
        """使用 black 格式化代码"""
        result = subprocess.run(
            ["black", "--check", "--diff", str(path)],
            capture_output=True,
            text=True,
        )
        return {
            "formatted": result.returncode == 0,
            "diff": result.stdout if result.stdout else "无变化",
            "stderr": result.stderr,
        }

    def _lint(self, path: Path, select: Optional[list[str]] = None) -> dict:
        """使用 ruff 检查代码"""
        args = ["ruff", "check", str(path)]
        if select:
            args.extend(["--select", ",".join(select)])
        result = subprocess.run(args, capture_output=True, text=True)
        issues = []
        for line in result.stdout.splitlines():
            if match := _parse_ruff_line(line):
                issues.append(match)
        return {
            "issues": issues,
            "count": len(issues),
            "raw_output": result.stdout,
        }

    def _typecheck(self, path: Path) -> dict:
        """使用 mypy 进行类型检查"""
        result = subprocess.run(
            ["mypy", str(path)],
            capture_output=True,
            text=True,
        )
        errors = [line for line in result.stdout.splitlines() if "error" in line.lower()]
        return {
            "errors": errors,
            "error_count": len(errors),
            "output": result.stdout,
        }

    def _complexity(self, path: Path) -> dict:
        """分析代码复杂度"""
        result = subprocess.run(
            ["radon", "cc", "-s", str(path)],
            capture_output=True,
            text=True,
        )
        return {
            "output": result.stdout,
            "returncode": result.returncode,
        }

    def _fix(self, path: Path) -> dict:
        """自动修复问题"""
        results = {}
        # 尝试 ruff 自动修复
        ruff_result = subprocess.run(
            ["ruff", "check", "--fix", str(path)],
            capture_output=True,
            text=True,
        )
        results["ruff_fix"] = ruff_result.returncode == 0
        # 尝试 black 格式化
        black_result = subprocess.run(
            ["black", str(path)],
            capture_output=True,
            text=True,
        )
        results["black_format"] = black_result.returncode == 0
        return results


def _parse_ruff_line(line: str) -> Optional[dict]:
    """解析 ruff 输出行"""
    match = re.match(r"^(.+):(\d+):(\d+):\s([A-Z]\d+\s+.+)$", line)
    if match:
        return {
            "file": match.group(1),
            "line": int(match.group(2)),
            "column": int(match.group(3)),
            "code": match.group(4).split()[0],
            "message": " ".join(match.group(4).split()[1:]),
        }
    return None


import re
