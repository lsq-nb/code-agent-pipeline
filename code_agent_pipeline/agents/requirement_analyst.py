"""
需求分析师智能体
负责解析用户需求，拆分子任务，识别技术约束
"""

from crewai import Agent

from ..rag.retriever import CodeRetriever


class RequirementAnalyst:
    """
    需求分析师

    职责：
    - 深度理解用户需求描述
    - 提取功能性和非功能性需求
    - 识别技术约束和风险因素
    - 拆分可执行的子任务
    - 推荐技术栈选型
    """

    ROLE_TEMPLATE = """\
你是资深软件需求分析师，拥有10年以上大型系统需求分析经验。
你的任务是深入理解用户需求，将其转化为清晰、可执行的技术规格。

## 你的能力
- 精准提取功能和非功能需求
- 识别潜在技术风险和约束
- 合理拆分复杂度到可管理粒度
- 推荐适配的技术栈和架构模式

## 分析框架
1. 需求理解：复述并确认核心需求
2. 功能拆解：按模块/层级拆分功能点
3. 约束识别：技术栈、性能、安全、合规等限制
4. 风险评估：技术难点、依赖风险、时间估算
5. 任务输出：生成可执行的开发任务清单

## 输出格式
严格按照以下 JSON 结构输出：
```json
{{
  "requirement_summary": "需求概述（100字内）",
  "functional_requirements": ["功能点1", "功能点2", ...],
  "non_functional_requirements": ["性能要求", "安全要求", ...],
  "technical_constraints": ["技术限制1", "技术限制2", ...],
  "risk_factors": ["风险1: 说明", ...],
  "suggested_tech_stack": ["技术1", "技术2", ...],
  "estimated_complexity": "low|medium|high",
  "tasks": [{{"id": "T001", "description": "任务描述"}}]
}}
```

## 项目上下文
{project_context}

## 约束条件
{constraints}

## 用户需求
{requirement}

## 代码规范参考
{rag_context}

请开始分析，输出 JSON 格式结果。
"""

    def __init__(self, llm=None, tools=None, rag_retriever: CodeRetriever | None = None):
        """
        初始化需求分析师

        参数:
            llm: LLM 实例
            tools: 工具列表
            rag_retriever: RAG 检索器（用于获取代码规范上下文）
        """
        self.llm = llm
        self.tools = tools or []
        self.rag_retriever = rag_retriever

        # 创建 CrewAI Agent
        self.agent = Agent(
            role="需求分析师",
            goal="精准分析用户需求，拆分为可执行任务，识别技术约束与风险",
            backstory="""\
资深软件需求分析师，擅长从模糊需求中提取精确规格，
有丰富的需求管理和项目规划经验。
熟悉各类技术栈和架构模式，能够评估技术可行性。""",
            llm=llm,
            tools=self.tools,
            verbose=True,
            allow_delegation=False,
        )

    def analyze(
        self, requirement: str, project_context: str = "", constraints: list[str] | None = None
    ) -> dict:
        """
        分析需求

        参数:
            requirement: 需求描述
            project_context: 项目上下文
            constraints: 约束条件列表

        返回:
            分析结果字典
        """
        # 获取 RAG 上下文
        rag_context = ""
        if self.rag_retriever:
            rag_docs = self.rag_retriever.search(requirement, top_k=3)
            rag_context = "\n\n".join([d["document"] for d in rag_docs])

        prompt = self.ROLE_TEMPLATE.format(
            requirement=requirement,
            project_context=project_context or "无特定上下文",
            constraints="\n".join(f"- {c}" for c in (constraints or [])) or "无特殊约束",
            rag_context=rag_context or "无额外规范参考",
        )

        result = self.agent.execute_task(prompt)
        return self._parse_result(result)

    def _parse_result(self, raw_output: str) -> dict:
        """解析 Agent 输出为结构化结果"""
        import json  # noqa: PLC0415 (局部导入避免顶层循环)
        import re  # noqa: PLC0415

        # 尝试从输出中提取 JSON
        json_match = re.search(r"```json\s*(\{.*?\})\s*```", raw_output, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        # 尝试直接解析
        try:
            return json.loads(raw_output)
        except json.JSONDecodeError:
            return {"raw_output": raw_output, "requirement_summary": raw_output[:200]}
