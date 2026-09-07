"""
架构师智能体
负责系统设计、模块划分、API 设计、数据库建模
"""

from crewai import Agent

from ..rag.retriever import CodeRetriever


class Architect:
    """
    架构师智能体

    职责：
    - 设计系统整体架构和模块划分
    - 定义 API 接口规范
    - 设计数据库 Schema
    - 规划数据流和错误处理策略
    - 考虑安全性和可扩展性
    """

    ROLE_TEMPLATE = """\
你是资深系统架构师，精通各种架构模式和设计原则。
你的任务是将需求转化为清晰的技术设计方案。

## 设计原则
- 高内聚低耦合
- 单一职责
- 可扩展性和可维护性优先
- 安全-by-design

## 设计框架
1. 架构模式选择：根据需求特点选择合适的架构模式
2. 模块划分：确定系统模块边界和职责
3. API 设计：定义接口规范和数据格式
4. 数据建模：设计数据库 Schema（如需要）
5. 数据流：描述各模块间的数据交互
6. 错误处理：定义异常处理策略
7. 安全考虑：识别安全需求和防护措施

## 输出格式
严格按照以下 JSON 结构输出：
```json
{{
  "architecture_pattern": "架构模式名称",
  "module_structure": ["模块1: 职责", "模块2: 职责", ...],
  "api_design": [{{"method": "GET", "path": "/api/xxx", "description": "描述"}}],
  "database_schema": {{"tables": [...]}},
  "data_flow": "数据流向描述",
  "error_handling_strategy": "错误处理策略",
  "security_considerations": ["安全点1", "安全点2", ...],
  "diagram_description": "Mermaid 架构图描述"
}}
```

## 项目上下文
{project_context}

## 需求分析结果
{analysis_result}

## 代码规范参考
{rag_context}

请开始设计，输出 JSON 格式结果。
"""

    def __init__(self, llm=None, rag_retriever: CodeRetriever | None = None):
        self.llm = llm
        self.rag_retriever = rag_retriever

        self.agent = Agent(
            role="系统架构师",
            goal="设计高质量、可扩展的系统架构方案",
            backstory="""\
资深系统架构师，15年+经验，精通微服务、DDD、CQRS等架构模式。
擅长将复杂业务需求转化为清晰的技术架构方案，
注重系统可维护性、可扩展性和安全性。""",
            llm=llm,
            verbose=True,
            allow_delegation=False,
        )

    def design(self, analysis_result: dict, project_context: str = "") -> dict:
        """
        生成架构设计方案

        参数:
            analysis_result: 需求分析结果
            project_context: 项目上下文

        返回:
            设计结果字典
        """
        rag_context = ""
        if self.rag_retriever:
            query = f"架构设计 {analysis_result.get('suggested_tech_stack', [])}"
            rag_docs = self.rag_retriever.search(query, top_k=3)
            rag_context = "\n\n".join([d["document"] for d in rag_docs])

        prompt = self.ROLE_TEMPLATE.format(
            project_context=project_context or "无特定上下文",
            analysis_result=self._format_analysis(analysis_result),
            rag_context=rag_context or "无额外规范参考",
        )

        result = self.agent.execute_task(prompt)
        return self._parse_result(result)

    def _format_analysis(self, analysis: dict) -> str:
        """格式化分析结果为文本"""
        lines = []
        lines.append(f"**需求摘要**: {analysis.get('requirement_summary', 'N/A')}")
        lines.append(f"**复杂度**: {analysis.get('estimated_complexity', 'N/A')}")
        lines.append("**功能需求**:")
        for fr in analysis.get("functional_requirements", []):
            lines.append(f"- {fr}")
        lines.append("**技术约束**:")
        for tc in analysis.get("technical_constraints", []):
            lines.append(f"- {tc}")
        lines.append("**推荐技术栈**:")
        for ts in analysis.get("suggested_tech_stack", []):
            lines.append(f"- {ts}")
        return "\n".join(lines)

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
