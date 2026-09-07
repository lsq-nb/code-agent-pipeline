"""
Git 操作工具
集成 gitpython 实现仓库克隆、分支管理、提交等操作
"""

import subprocess
from pathlib import Path
from typing import Any, Optional

from git import Repo, GitCommandError

from .base import ToolBase, ToolResult


class GitTool(ToolBase):
    """Git 版本控制工具"""

    name = "git_tool"
    description = (
        "执行 Git 操作：克隆仓库、创建分支、查看状态、创建提交、获取日志等。"
        "用于与代码仓库交互，获取历史代码和规范文档。"
    )

    def __init__(self, workdir: Optional[Path] = None):
        self.workdir = workdir or Path.cwd()

    def execute(self, action: str, **kwargs: Any) -> ToolResult:
        """
        执行 Git 操作

        支持的 action:
        - clone: 克隆仓库，参数 repo_url, target_dir
        - status: 查看仓库状态
        - branch_create: 创建分支，参数 branch_name
        - branch_list: 列出所有分支
        - commit: 提交更改，参数 message, files
        - log: 获取提交历史，参数 limit
        - diff: 获取差异
        - fetch: 拉取远程更新
        - pull: 拉取并合并
        - blame: 获取文件改动历史
        """
        action_map = {
            "clone": self._clone,
            "status": self._status,
            "branch_create": self._branch_create,
            "branch_list": self._branch_list,
            "commit": self._commit,
            "log": self._log,
            "diff": self._diff,
            "fetch": self._fetch,
            "pull": self._pull,
            "blame": self._blame,
        }

        handler = action_map.get(action)
        if not handler:
            return ToolResult.fail(f"未知的 Git 操作: {action}")

        try:
            result = handler(**kwargs)
            return ToolResult.ok(data=result)
        except Exception as e:
            return ToolResult.fail(error=f"Git 操作失败: {str(e)}")

    def _get_repo(self, path: Optional[Path] = None) -> Repo:
        """获取或打开 Git 仓库"""
        target = path or self.workdir
        if target.exists() and (target / ".git").exists():
            return Repo(target)
        raise FileNotFoundError(f"不是 Git 仓库: {target}")

    def _clone(self, repo_url: str, target_dir: Optional[str] = None) -> dict:
        """克隆仓库"""
        target = Path(target_dir) if target_dir else self.workdir / Path(repo_url).stem
        target.mkdir(parents=True, exist_ok=True)
        Repo.clone_from(repo_url, target)
        return {
            "path": str(target),
            "url": repo_url,
            "message": f"成功克隆仓库到 {target}",
        }

    def _status(self) -> dict:
        """查看仓库状态"""
        repo = self._get_repo()
        return {
            "is_clean": repo.is_dirty() is False,
            "branch": repo.active_branch.name if repo.active_branch else "detached",
            "files_changed": len(repo.git.diff("--name-only").splitlines())
            if repo.is_dirty()
            else 0,
        }

    def _branch_create(self, branch_name: str) -> dict:
        """创建分支"""
        repo = self._get_repo()
        repo.git.checkout("-b", branch_name)
        return {"branch": branch_name, "message": f"已创建分支: {branch_name}"}

    def _branch_list(self) -> list[str]:
        """列出分支"""
        repo = self._get_repo()
        return [ref.name for ref in repo.refs]

    def _commit(self, message: str, files: Optional[list[str]] = None) -> dict:
        """创建提交"""
        repo = self._get_repo()
        if files:
            for f in files:
                repo.git.add(f)
        else:
            repo.git.add(".")
        repo.git.commit("-m", message)
        return {"message": f"已提交: {message}"}

    def _log(self, limit: int = 10) -> list[dict]:
        """获取提交历史"""
        repo = self._get_repo()
        commits = list(repo.iter_commits(max_count=limit))
        return [
            {
                "sha": c.hexsha[:8],
                "message": c.message.strip(),
                "author": c.author.name,
                "date": c.authored_datetime.isoformat(),
            }
            for c in commits
        ]

    def _diff(self, target: Optional[str] = None) -> str:
        """获取差异"""
        repo = self._get_repo()
        if target:
            return repo.git.diff(target)
        return repo.git.diff()

    def _fetch(self) -> dict:
        """拉取远程更新"""
        repo = self._get_repo()
        repo.remote().fetch()
        return {"message": "已拉取远程更新"}

    def _pull(self) -> dict:
        """拉取并合并"""
        repo = self._get_repo()
        repo.remote().pull()
        return {"message": "已拉取并合并远程更改"}

    def _blame(self, file_path: str) -> list[dict]:
        """获取文件改动历史"""
        repo = self._get_repo()
        lines = repo.git.blame("--porcelain", file_path).splitlines()
        result = []
        current_sha = None
        for line in lines:
            if line.startswith(" ") or not line:
                continue
            parts = line.split()
            if parts[0] != current_sha:
                current_sha = parts[0]
                result.append({"sha": current_sha[:8]})
            elif result and "buffer" not in line:
                result[-1]["line"] = line.strip()
        return result[:20]  # 限制返回行数

    def clone_repo(self, repo_url: str, target_dir: Optional[str] = None) -> Path:
        """便捷方法：克隆仓库到指定目录"""
        result = self._clone(repo_url=repo_url, target_dir=target_dir)
        return Path(result["path"])
