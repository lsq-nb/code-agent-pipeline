"""
代码规范索引器
从源代码仓库提取规范文档并建立索引
"""

import re
from pathlib import Path
from typing import Optional

from .retriever import CodeRetriever


class CodeIndexer:
    """
    代码规范索引器

    从项目中提取代码规范、文档、最佳实践，
    建立向量索引供 RAG 检索使用。
    """

    # 常见的规范文件模式
    SPEC_PATTERNS = [
        "*.md", "*.rst", "*.txt",
        "*.py", "*.js", "*.ts",
        "*.yaml", "*.yml", "*.json",
    ]

    # 需要排除的目录
    EXCLUDE_DIRS = {
        "node_modules", ".git", "__pycache__", "venv", ".venv",
        "env", ".cache", "build", "dist", ".tox", ".mypy_cache",
        ".pytest_cache", ".ruff_cache", "htmlcov",
    }

    def __init__(self, retriever: Optional[CodeRetriever] = None,
                 chunk_size: int = 512, chunk_overlap: int = 64):
        self.retriever = retriever or CodeRetriever()
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def index_directory(self, directory: str, source_type: str = "project") -> int:
        """
        索引整个目录

        参数:
            directory: 目标目录路径
            source_type: 来源类型（project/styleguide/api）

        返回:
            索引的文档数量
        """
        dir_path = Path(directory)
        count = 0

        for file_path in self._iter_files(dir_path):
            if file_path.suffix in {".py", ".js", ".ts"}:
                content = self._extract_comments_and_docs(file_path)
            else:
                content = file_path.read_text(encoding="utf-8", errors="ignore")

            if not content.strip():
                continue

            chunks = self._chunk_text(content)
            for i, chunk in enumerate(chunks):
                doc_id = f"{source_type}::{file_path.stem}::{i}"
                self.retriever.add_documents([{
                    "id": doc_id,
                    "text": chunk,
                    "metadata": {
                        "source": str(file_path),
                        "source_type": source_type,
                        "chunk_index": i,
                        "total_chunks": len(chunks),
                    },
                }])
                count += 1

        return count

    def index_repo(self, repo_path: str, source_type: str = "project") -> int:
        """索引 Git 仓库"""
        return self.index_directory(repo_path, source_type)

    def index_standard_documents(self, docs: list[dict]) -> int:
        """
        索引文档列表

        参数:
            docs: 文档列表，每项包含 text 和 metadata
        """
        count = 0
        for doc in docs:
            chunks = self._chunk_text(doc["text"])
            for i, chunk in enumerate(chunks):
                base_meta = doc.get("metadata", {})
                base_meta["chunk_index"] = i
                base_meta["total_chunks"] = len(chunks)
                self.retriever.add_documents([{
                    "id": f"doc::{count}",
                    "text": chunk,
                    "metadata": base_meta,
                }])
                count += 1
        return count

    def _iter_files(self, directory: Path) -> Path:
        """递归遍历文件，跳过排除目录"""
        for path in sorted(directory.rglob("*")):
            if path.is_file():
                # 检查路径中是否有需要排除的目录
                rel_parts = path.relative_to(directory).parts
                if any(part in self.EXCLUDE_DIRS for part in rel_parts):
                    continue
                yield path

    def _extract_comments_and_docs(self, file_path: Path) -> str:
        """从代码文件中提取注释和文档字符串"""
        content = file_path.read_text(encoding="utf-8", errors="ignore")
        lines = content.splitlines()
        extracted = []

        in_docstring = False
        docstring_delimiter = None

        for line in lines:
            stripped = line.strip()

            # 检测文档字符串开始
            if not in_docstring:
                found_docstring = False
                for delim in ('"""', "'''"):
                    if stripped.startswith(delim):
                        in_docstring = True
                        docstring_delimiter = delim
                        # 检查是否单行闭合
                        rest = stripped[3:]
                        if delim in rest:
                            extracted.append(rest.split(delim)[0].strip())
                            in_docstring = False
                        found_docstring = True
                        break
                # 单行注释
                if not found_docstring and stripped.startswith("#"):
                    extracted.append(stripped[1:].strip())
            else:
                # 文档字符串结束
                if docstring_delimiter and docstring_delimiter in stripped:
                    extracted.append(stripped.split(docstring_delimiter)[0].strip())
                    in_docstring = False
                else:
                    extracted.append(stripped)

        return "\n".join(extracted)

    def _chunk_text(self, text: str) -> list[str]:
        """将文本分割为重叠的块。按段落分割，超长段落按行/字符切分。"""
        paragraphs = re.split(r"\n\s*\n", text)
        chunks = []
        current = ""

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            # 超长段落：先按行分割
            if len(para) > self.chunk_size:
                for line in para.split("\n"):
                    line = line.strip()
                    if not line:
                        continue
                    # 如果单行仍然超长，按字符切分
                    if len(line) > self.chunk_size:
                        if current:
                            chunks.append(current.strip())
                            os_start = max(0, len(current) - self.chunk_overlap)
                            current = current[os_start:]
                        # 字符级切分
                        for i in range(0, len(line), self.chunk_size - self.chunk_overlap):
                            chunk = line[i:i + self.chunk_size]
                            if chunk.strip():
                                chunks.append(chunk.strip())
                        current = ""
                    elif len(current) + len(line) + 2 > self.chunk_size and current:
                        chunks.append(current.strip())
                        os_start = max(0, len(current) - self.chunk_overlap)
                        current = current[os_start:] + "\n" + line
                    else:
                        current += "\n" + line
                continue

            # 正常段落：检查是否需要切分
            if len(current) + len(para) + 2 > self.chunk_size and current:
                chunks.append(current.strip())
                os_start = max(0, len(current) - self.chunk_overlap)
                current = current[os_start:] + "\n\n" + para
            else:
                current += "\n\n" + para

        if current.strip():
            chunks.append(current.strip())

        return [c for c in chunks if len(c) > 10]
