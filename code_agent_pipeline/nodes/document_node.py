"""
文档生成节点
生成 README、API 文档、用户指南等项目文档
"""

from typing import Any

from ..models import DocumentationResult, PipelineStage, PipelineState


async def document_node(state: PipelineState) -> dict[str, Any]:
    """
    文档生成节点

    根据项目需求和代码结构，生成完整的项目文档：
    - README.md
    - API 文档
    - 用户指南
    - 变更日志
    - 贡献指南
    """
    state.current_stage = PipelineStage.DOCUMENT
    state.add_message("document", "开始生成文档...")

    prompt = _build_document_prompt(state)
    result = await _call_llm_document(prompt, state)
    doc_result = _parse_document_result(result, state)

    state.documentation = doc_result
    state.add_message("document", "文档生成完成")
    state.update_timestamp()

    return {
        "documentation": doc_result,
        "current_stage": PipelineStage.TEST,
        "agent_messages": state.agent_messages,
    }


def _build_document_prompt(state: PipelineState) -> str:
    """构建文档生成提示词"""
    analysis = state.analysis
    code_structure = ""
    if state.code_generation:
        code_structure = "\n".join(
            f"- `{a.file_path}` ({a.language}) - {a.description}"
            for a in state.code_generation.artifacts
        )

    return f"""\
请为以下项目生成完整的项目文档：

## 需求分析
{analysis.requirement_summary if analysis else "无分析结果"}

## 项目上下文
{state.project_context or "无特定上下文"}

## 代码结构
{code_structure or "待补充"}

请按以下 JSON 格式输出所有文档内容：
```json
{{
  "readme": "# 项目标题\\n\\n项目描述...",
  "api_docs": "## API 接口文档\\n\\n### GET /api/xxx...",
  "user_guide": "## 用户指南\\n\\n### 安装\\n...",
  "changelog": "# 变更日志\\n\\n## v0.1.0 - {__import__("datetime").date.today().isoformat()}\\n...",
  "contributing_guidelines": "# 贡献指南\\n\\n..."
}}
```
"""


async def _call_llm_document(prompt: str, state: PipelineState) -> str:
    """调用 LLM 生成文档（统一走 create_llm 工厂，读取全局配置）"""
    from langchain_core.messages import HumanMessage  # noqa: PLC0415

    from ..utils.llm import create_llm  # noqa: PLC0415 (局部导入)

    llm = create_llm(temperature=0.2)
    response = await llm.ainvoke([HumanMessage(content=prompt)])
    return response.content


def _parse_document_result(raw: str, state: PipelineState) -> DocumentationResult:
    """解析文档生成结果"""
    from ..utils.json_extract import extract_json  # noqa: PLC0415 (局部导入)

    data = extract_json(raw)
    if data is not None:
        try:
            return DocumentationResult(**data)
        except (ValueError, KeyError, TypeError):
            pass

    return DocumentationResult(
        readme=(raw or "")[:1000],
        api_docs="",
        user_guide="",
        changelog="",
        contributing_guidelines="",
    )
