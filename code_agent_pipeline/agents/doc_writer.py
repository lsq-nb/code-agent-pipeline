"""
文档工程师智能体
负责生成 README、API 文档、用户指南等项目文档
"""

from crewai import Agent

from ..rag.retriever import CodeRetriever


class DocWriter:
    """
    文档工程师智能体

    职责：
    - 生成 README.md 项目说明
    - 编写 API 文档
    - 创建用户指南
    - 维护 CHANGELOG
    - 编写 CONTRIBUTING 规范
    """

    ROLE_TEMPLATE = """\
你是专业 technical writer，擅长撰写清晰、完整的技术文档。
你的任务是为项目生成高质量的文档材料。

## 文档标准
- README: 项目简介、安装、快速开始、配置说明
- API 文档: 接口说明、参数描述、响应格式、示例
- 用户指南: 详细使用说明、最佳实践、故障排查
- CHANGELOG: 版本变更记录
- CONTRIBUTING: 贡献指南和开发规范

## 文档风格
- 简洁明了，避免冗余
- 使用代码示例辅助说明
- 层次分明，便于查找
- 中英文混合时保持一致性

## 输出格式
严格按照以下 JSON 结构输出所有文档：
```json
{{
  "readme": "# 项目标题\\n\\n项目描述...",
  "api_docs": "## API 接口\\n\\n### GET /api/xxx\\n...",
  "user_guide": "## 用户指南\\n\\n### 安装\\n...",
  "changelog": "# 变更日志\\n\\n## v0.1.0\\n...",
  "contributing_guidelines": "# 贡献指南\\n\\n..."
}}
```

## 项目上下文
{project_context}

## 代码结构
{code_structure}

## 功能描述
{feature_description}

请开始编写文档，输出 JSON 格式结果。
"""

    def __init__(self, llm=None, rag_retriever: CodeRetriever | None = None):
        self.llm = llm
        self.rag_retriever = rag_retriever

        self.agent = Agent(
            role="技术文档工程师",
            goal="生成高质量、结构化的项目文档",
            backstory="""\
专业 technical writer，5年+技术文档经验。
擅长将复杂的技术概念转化为清晰易懂的文档，
注重文档的完整性、准确性和可操作性。""",
            llm=llm,
            verbose=True,
            allow_delegation=False,
        )

    def generate(self, project_context: str, code_structure: str, feature_description: str) -> dict:
        """
        生成项目文档

        参数:
            project_context: 项目上下文
            code_structure: 代码结构描述
            feature_description: 功能描述

        返回:
            文档生成结果
        """
        prompt = self.ROLE_TEMPLATE.format(
            project_context=project_context,
            code_structure=code_structure,
            feature_description=feature_description,
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
