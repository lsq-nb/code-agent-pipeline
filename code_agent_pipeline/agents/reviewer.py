"""
代码审查员智能体
负责代码质量审查、安全扫描、性能分析
"""

from typing import Optional

from crewai import Agent

from ..rag.retriever import CodeRetriever


class Reviewer:
    """
    代码审查员智能体

    职责：
    - 代码质量审查（可读性、可维护性）
    - 安全漏洞扫描
    - 性能问题分析
    - 代码规范合规检查
    - 给出改进建议
    """

    ROLE_TEMPLATE = """\
你是资深代码审查员和技术负责人，拥有严格的代码质量标准。
你的任务是全面审查代码，确保质量、安全和性能达标。

## 审查维度
1. **代码质量**：可读性、可维护性、DRY 原则
2. **安全性**：注入攻击、数据泄露、权限控制
3. **性能**：算法效率、资源消耗、缓存策略
4. **规范性**：编码规范、命名约定、注释质量
5. **测试覆盖**：边界条件、异常处理、错误恢复

## 严重级别定义
- **CRITICAL**: 必须修复，可能导致安全漏洞或系统崩溃
- **MAJOR**: 重要问题，影响代码质量或可维护性
- **MINOR**: 建议改进，提升代码质量
- **STYLE**: 样式建议，不影响功能

## 输出格式
严格按照以下 JSON 结构输出：
```json
{{
  "verdict": "approved|changes_requested|rejected|comment_only",
  "quality_score": 8.5,
  "quality_level": "excellent|good|needs_improvement|poor",
  "issues": [
    {{"severity": "critical|major|minor|style", "file": "path", "line": 42, "message": "问题描述"}}
  ],
  "suggestions": ["改进建议1", "改进建议2"],
  "security_findings": ["安全问题1"],
  "performance_findings": ["性能问题1"]
}}
```

## 待审查代码
{code_content}

## 项目上下文
{project_context}

## 代码规范参考
{rag_context}

请开始审查，输出 JSON 格式结果。
"""

    def __init__(self, llm=None, rag_retriever: Optional[CodeRetriever] = None):
        self.llm = llm
        self.rag_retriever = rag_retriever

        self.agent = Agent(
            role="代码审查员",
            goal="全面审查代码质量，发现安全漏洞和性能问题",
            backstory="""\
资深代码审查员和技术负责人，以严格的代码质量标准著称。
擅长发现代码中的安全隐患、性能瓶颈和设计缺陷，
能够提供具体可操作的改进建议。""",
            llm=llm,
            verbose=True,
            allow_delegation=False,
        )

    def review(self, code_content: str, project_context: str = "",
               file_path: str = "") -> dict:
        """
        审查代码

        参数:
            code_content: 代码内容
            project_context: 项目上下文
            file_path: 文件路径

        返回:
            审查结果
        """
        rag_context = ""
        if self.rag_retriever:
            rag_docs = self.rag_retriever.search("代码规范 代码审查", top_k=3)
            rag_context = "\n\n".join([d["document"] for d in rag_docs])

        prompt = self.ROLE_TEMPLATE.format(
            code_content=code_content[:8000],  # 限制长度
            project_context=project_context or "无特定上下文",
            rag_context=rag_context or "无额外规范参考",
        )

        result = self.agent.execute_task(prompt)
        return self._parse_result(result)

    def _parse_result(self, raw_output: str) -> dict:
        """解析 Agent 输出"""
        import json  # noqa: PLC0415
        import re  # noqa: PLC0415

        json_match = re.search(r"```json\s*(\{.*?\})\s*```", raw_output, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        try:
            return json.loads(raw_output)
        except json.JSONDecodeError:
            return {"raw_output": raw_output}
