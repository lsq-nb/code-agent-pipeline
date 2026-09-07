"""
文件操作工具
用于读写、搜索、创建项目文件
"""

import json
import re
from pathlib import Path
from typing import Optional

from .base import ToolBase, ToolResult


class FileTool(ToolBase):
    """文件操作工具"""

    name = "file_tool"
    description = (
        "文件操作工具：读取文件内容、写入文件、搜索文件内容、"
        "列出目录结构、获取文件统计信息等。用于代码生成和管理。"
    )

    def __init__(self, root: Optional[Path] = None):
        self.root = root or Path.cwd()

    def execute(self, action: str, **kwargs: Any) -> ToolResult:
        """
        执行文件操作

        支持的 action:
        - read: 读取文件，参数 path
        - write: 写入文件，参数 path, content, append
        - search: 搜索文件内容，参数 pattern, path, exclude
        - list: 列出目录，参数 path, recursive
        - stats: 获取文件统计，参数 path
        - create_dir: 创建目录，参数 path
        """
        action_map = {
            "read": self._read,
            "write": self._write,
            "search": self._search,
            "list": self._list,
            "stats": self._stats,
            "create_dir": self._create_dir,
        }

        handler = action_map.get(action)
        if not handler:
            return ToolResult.fail(f"未知的文件操作: {action}")

        try:
            result = handler(**kwargs)
            return ToolResult.ok(data=result)
        except Exception as e:
            return ToolResult.fail(error=f"文件操作失败: {str(e)}")

    def _read(self, path: str) -> dict:
        """读取文件内容"""
        full_path = self._resolve(path)
        if not full_path.exists():
            return ToolResult.fail(error=f"文件不存在: {path}").data
        content = full_path.read_text(encoding="utf-8")
        lines = content.splitlines()
        return {
            "path": str(full_path),
            "content": content,
            "lines": len(lines),
            "size_bytes": full_path.stat().st_size,
        }

    def _write(self, path: str, content: str, append: bool = False) -> dict:
        """写入文件内容"""
        full_path = self._resolve(path)
        full_path.parent.mkdir(parents=True, exist_ok=True)
        mode = "a" if append else "w"
        full_path.write_text(content, encoding="utf-8", mode=mode)
        return {
            "path": str(full_path),
            "bytes_written": len(content.encode("utf-8")),
            "append": append,
        }

    def _search(self, pattern: str, path: Optional[str] = None,
                exclude: Optional[list[str]] = None) -> list[dict]:
        """在文件中搜索文本"""
        search_root = self._resolve(path) if path else self.root
        exclude_exts = set(exclude or [])
        matches = []
        for fp in search_root.rglob("*"):
            if fp.suffix in exclude_exts:
                continue
            if not fp.is_file():
                continue
            try:
                content = fp.read_text(encoding="utf-8", errors="ignore")
                if re.search(pattern, content):
                    matches.append({
                        "path": str(fp.relative_to(self.root)),
                        "line": content.count('\n', 0, content.find(pattern)) + 1,
                    })
            except (UnicodeDecodeError, PermissionError):
                continue
        return matches[:50]  # 限制结果数量

    def _list(self, path: Optional[str] = None, recursive: bool = False) -> list[str]:
        """列出目录内容"""
        target = self._resolve(path) if path else self.root
        if recursive:
            return [str(p.relative_to(self.root)) for p in target.rglob("*") if p.is_file()]
        return [str(p.relative_to(self.root)) for p in target.iterdir() if p.is_file()]

    def _stats(self, path: str) -> dict:
        """获取文件或目录统计信息"""
        full_path = self._resolve(path)
        if full_path.is_file():
            content = full_path.read_text(encoding="utf-8", errors="ignore")
            lines = content.splitlines()
            return {
                "type": "file",
                "path": str(full_path),
                "lines": len(lines),
                "characters": len(content),
                "words": len(content.split()),
                "size_bytes": full_path.stat().st_size,
            }
        elif full_path.is_dir():
            files = list(full_path.rglob("*"))
            py_files = [f for f in files if f.suffix == ".py"]
            return {
                "type": "directory",
                "path": str(full_path),
                "total_files": len([f for f in files if f.is_file()]),
                "python_files": len(py_files),
                "total_dirs": len([f for f in files if f.is_dir()]),
            }
        return {"error": "路径不存在"}

    def _create_dir(self, path: str) -> dict:
        """创建目录"""
        full_path = self._resolve(path)
        full_path.mkdir(parents=True, exist_ok=True)
        return {"path": str(full_path), "created": True}

    def _resolve(self, path: str) -> Path:
        """解析相对路径为绝对路径"""
        p = Path(path)
        if p.is_absolute():
            return p
        return self.root / p
