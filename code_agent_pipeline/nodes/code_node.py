"""
代码生成节点
根据设计文档生成具体代码实现
"""

import json
import re
from pathlib import Path
from typing import Any

from ..models import CodeArtifact, CodeGenerationResult, PipelineStage, PipelineState


async def code_node(state: PipelineState) -> dict[str, Any]:
    """
    代码生成节点

    基于架构设计文档，使用 LLM 生成完整可运行的代码实现。
    支持多文件生成，包含依赖管理和构建说明。
    """
    state.current_stage = PipelineStage.CODE
    state.add_message("code", "开始代码生成...")

    prompt = _build_code_prompt(state)
    result = await _call_llm_code(prompt, state)
    code_result = _parse_code_result(result, state)

    # 保存生成的代码到文件系统
    _save_artifacts(code_result, state)

    state.code_generation = code_result
    state.add_message("code", f"生成 {len(code_result.artifacts)} 个代码文件")
    state.update_timestamp()

    return {
        "code_generation": code_result,
        "current_stage": PipelineStage.REVIEW,
        "agent_messages": state.agent_messages,
    }


def _build_code_prompt(state: PipelineState) -> str:
    """构建代码生成提示词"""
    design = state.design
    if not design:
        design_summary = "无设计文档"
    else:
        design_summary = json.dumps(
            design.model_dump(exclude_none=True),
            ensure_ascii=False,
            indent=2,
        )

    return f"""\
请根据以下架构设计文档，生成完整的 Python 代码实现：

## 架构设计
{design_summary}

## 代码规范
- 遵循 PEP 8 编码规范
- 添加完整的类型注解
- 关键函数添加文档字符串
- 完善的错误处理
- 安全的输入验证

请按以下 JSON 格式输出代码产物：
```json
{{
  "artifacts": [
    {{
      "file_path": "src/module/file.py",
      "content": "#!/usr/bin/env python3\\n\\\"\"\"模块文档字符串\\\"\"\"\\n\\n...",
      "language": "python",
      "description": "文件功能描述",
      "dependencies": ["package>=1.0.0"],
      "test_required": true
    }}
  ],
  "build_instructions": "pip install -r requirements.txt\\npython -m src",
  "environment_requirements": ["Python >= 3.11", "Redis >= 7.0"],
  "notes": "部署注意事项"
}}
```
"""


async def _call_llm_code(prompt: str, state: PipelineState) -> str:
    """调用 LLM 生成代码"""
    from langchain_core.messages import HumanMessage  # noqa: PLC0415
    from langchain_openai import ChatOpenAI  # noqa: PLC0415

    llm = ChatOpenAI(model="gpt-4o", temperature=0.1)
    response = await llm.ainvoke([HumanMessage(content=prompt)])
    return response.content


def _parse_code_result(raw: str, state: PipelineState) -> CodeGenerationResult:
    """解析代码生成结果"""
    json_match = re.search(r"```json\s*(\{.*?\})\s*```", raw, re.DOTALL)
    if json_match:
        try:
            data = json.loads(json_match.group(1))
            artifacts = [CodeArtifact(**a) for a in data.get("artifacts", [])]
            return CodeGenerationResult(
                artifacts=artifacts,
                build_instructions=data.get("build_instructions", ""),
                environment_requirements=data.get("environment_requirements", []),
                notes=data.get("notes", ""),
            )
        except (json.JSONDecodeError, ValueError):
            pass

    try:
        data = json.loads(raw)
        artifacts = [CodeArtifact(**a) for a in data.get("artifacts", [])]
        return CodeGenerationResult(
            artifacts=artifacts,
            build_instructions=data.get("build_instructions", ""),
            environment_requirements=data.get("environment_requirements", []),
            notes=data.get("notes", ""),
        )
    except (json.JSONDecodeError, ValueError):
        return CodeGenerationResult(
            artifacts=[],
            build_instructions="",
            environment_requirements=[],
            notes=raw[:500],
        )


def _save_artifacts(code_result: CodeGenerationResult, state: PipelineState) -> None:
    """将代码产物保存到文件系统"""
    output_dir = Path(state.output_dir) if hasattr(state, "output_dir") else Path("output")
    output_dir.mkdir(parents=True, exist_ok=True)

    for artifact in code_result.artifacts:
        full_path = output_dir / artifact.file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(artifact.content, encoding="utf-8")
