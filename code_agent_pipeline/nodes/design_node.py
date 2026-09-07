"""
架构设计节点
根据分析结果生成系统架构设计方案
"""

import json
import re
from typing import Any

from ..models import PipelineState, PipelineStage, TaskStatus, DesignResult


async def design_node(state: PipelineState) -> dict[str, Any]:
    """
    架构设计节点

    基于需求分析结果，生成系统架构设计，包括模块划分、
    API 设计、数据流、安全考虑等。
    """
    state.current_stage = PipelineStage.DESIGN
    state.add_message("design", "开始架构设计...")

    prompt = _build_design_prompt(state)
    result = await _call_llm_design(prompt, state)
    design = _parse_design_result(result, state)
    state.design = design

    state.add_message("design", f"设计完成，架构模式: {design.architecture_pattern}")
    state.update_timestamp()

    return {
        "design": design,
        "current_stage": PipelineStage.CODE,
        "agent_messages": state.agent_messages,
    }


def _build_design_prompt(state: PipelineState) -> str:
    """构建设计提示词"""
    analysis = state.analysis
    if not analysis:
        analysis_summary = "无分析结果"
    else:
        analysis_summary = json.dumps(
            analysis.model_dump(exclude_none=True),
            ensure_ascii=False,
            indent=2,
        )

    return f"""\
请根据以下需求分析结果，设计系统架构方案：

## 需求分析结果
{analysis_summary}

请按以下 JSON 格式输出架构设计：
```json
{{
  "architecture_pattern": "架构模式（如：分层架构、微服务、DDD）",
  "module_structure": ["模块1: 职责描述", "模块2: 职责描述"],
  "api_design": [
    {{"method": "GET/POST/PUT/DELETE", "path": "/api/endpoint", "description": "接口描述"}}
  ],
  "database_schema": {{"tables": ["表名: 字段描述"]}},
  "data_flow": "数据流转描述",
  "error_handling_strategy": "错误处理策略",
  "security_considerations": ["安全考虑1", "安全考虑2"],
  "diagram_description": "Mermaid 架构图描述"
}}
```
"""


async def _call_llm_design(prompt: str, state: PipelineState) -> str:
    """调用 LLM 执行设计"""
    from langchain_openai import ChatOpenAI  # noqa: PLC0415
    from langchain_core.messages import HumanMessage  # noqa: PLC0415

    llm = ChatOpenAI(model="gpt-4o", temperature=0.3)
    response = await llm.ainvoke([HumanMessage(content=prompt)])
    return response.content


def _parse_design_result(raw: str, state: PipelineState) -> DesignResult:
    """解析设计结果为结构化对象"""
    json_match = re.search(r"```json\s*(\{.*?\})\s*```", raw, re.DOTALL)
    if json_match:
        try:
            data = json.loads(json_match.group(1))
            return DesignResult(**data)
        except (json.JSONDecodeError, ValueError):
            pass

    try:
        data = json.loads(raw)
        return DesignResult(**data)
    except (json.JSONDecodeError, ValueError):
        return DesignResult(
            architecture_pattern="unknown",
            module_structure=["待设计"],
            api_design=[],
            data_flow="",
            error_handling_strategy="",
            security_considerations=[],
            diagram_description="",
        )
