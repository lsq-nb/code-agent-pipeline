"""
需求分析节点
将需求拆解为可执行任务，输出 AnalysisResult
"""

import json
import re
from typing import Any

from ..models import PipelineState, PipelineStage, TaskStatus, AnalysisResult


async def analyze_node(state: PipelineState) -> dict[str, Any]:
    """
    需求分析节点

    使用 LLM 分析用户需求，提取功能需求、非功能需求、
    技术约束，拆分为可执行子任务。
    """
    state.status = TaskStatus.RUNNING
    state.current_stage = PipelineStage.ANALYZE
    state.add_message("analyze", "开始需求分析...")

    # 构建分析提示词
    prompt = _build_analysis_prompt(state)

    # 调用 LLM（通过配置的 LLM 服务）
    result = await _call_llm_analysis(prompt, state)

    # 解析结果
    analysis = _parse_analysis_result(result, state)
    state.analysis = analysis

    state.add_message("analyze", f"分析完成，拆分为 {len(analysis.tasks)} 个子任务")
    state.update_timestamp()

    return {
        "analysis": analysis,
        "current_stage": PipelineStage.DESIGN,
        "agent_messages": state.agent_messages,
    }


def _build_analysis_prompt(state: PipelineState) -> str:
    """构建分析提示词"""
    context = state.project_context or "无特定项目上下文"
    constraints = "\n".join(f"- {c}" for c in state.constraints) if state.constraints else "无特殊约束"

    return f"""\
请对以下软件开发需求进行详细分析：

## 需求描述
{state.requirement}

## 项目上下文
{context}

## 约束条件
{constraints}

请按以下 JSON 格式输出分析结果：
```json
{{
  "requirement_summary": "需求概述",
  "functional_requirements": ["功能需求1", "功能需求2"],
  "non_functional_requirements": ["性能要求", "安全要求"],
  "technical_constraints": ["技术限制1", "技术限制2"],
  "risk_factors": ["风险1: 说明"],
  "suggested_tech_stack": ["技术1", "技术2"],
  "estimated_complexity": "low|medium|high",
  "tasks": [
    {{"id": "T001", "description": "任务描述", "estimated_effort": "高/中/低"}}
  ]
}}
```
"""


async def _call_llm_analysis(prompt: str, state: PipelineState) -> str:
    """调用 LLM 执行分析"""
    from langchain_openai import ChatOpenAI  # noqa: PLC0415 (局部导入)
    from langchain_core.messages import HumanMessage  # noqa: PLC0415
    from ..config import get_config  # noqa: PLC0415

    config = get_config()
    llm = ChatOpenAI(
        model=config.llm.model,
        temperature=config.llm.temperature,
    )
    response = await llm.ainvoke([HumanMessage(content=prompt)])
    return response.content


def _parse_analysis_result(raw: str, state: PipelineState) -> AnalysisResult:
    """解析分析结果为结构化对象"""
    # 提取 JSON
    json_match = re.search(r"```json\s*(\{.*?\})\s*```", raw, re.DOTALL)
    if json_match:
        try:
            data = json.loads(json_match.group(1))
            return AnalysisResult(**data)
        except (json.JSONDecodeError, ValueError):
            pass

    # 尝试直接解析
    try:
        data = json.loads(raw)
        return AnalysisResult(**data)
    except (json.JSONDecodeError, ValueError):
        # 降级：构造最小可用结果
        return AnalysisResult(
            requirement_summary=raw[:200],
            functional_requirements=["待分析"],
            non_functional_requirements=[],
            technical_constraints=[],
            risk_factors=[],
            suggested_tech_stack=[],
            estimated_complexity="medium",
            tasks=[],
        )
