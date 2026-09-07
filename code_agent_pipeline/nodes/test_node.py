"""
测试节点
生成并执行测试用例，验证代码质量
"""

import json
import re
from typing import Any

from ..models import PipelineStage, PipelineState, TestResult


async def test_node(state: PipelineState) -> dict[str, Any]:
    """
    测试节点

    为生成的代码生成测试用例，执行测试并收集覆盖率数据。
    """
    state.current_stage = PipelineStage.TEST
    state.add_message("test", "开始测试生成和执行...")

    # 生成测试用例
    test_plan = await _generate_test_cases(state)

    # 执行测试（在实际项目中会运行 pytest）
    test_result = await _run_tests(state, test_plan)

    state.testing = test_result
    state.add_message("test", f"测试完成: {test_result.passed} 通过, {test_result.failed} 失败")
    state.update_timestamp()

    return {
        "testing": test_result,
        "current_stage": PipelineStage.TEST,
        "agent_messages": state.agent_messages,
        "status": "completed" if test_result.failed == 0 else "needs_fix",
    }


async def _generate_test_cases(state: PipelineState) -> dict:
    """生成测试用例"""
    from langchain_core.messages import HumanMessage  # noqa: PLC0415
    from langchain_openai import ChatOpenAI  # noqa: PLC0415

    code_snippet = ""
    if state.code_generation:
        code_snippet = "\n\n".join(
            f"# {a.file_path}\n```{a.language}\n{a.content[:1500]}\n```"
            for a in state.code_generation.artifacts[:3]
        )

    prompt = f"""\
请为以下代码生成 pytest 测试用例：

{code_snippet}

请按以下 JSON 格式输出：
```json
{{
  "test_cases": [
    {{"name": "test_function_name", "description": "测试描述", "code": "def test_xxx...\\n"}}
  ],
  "test_command": "pytest tests/ -v --cov=src --cov-report=term",
  "coverage_target": 80
}}
```
"""

    llm = ChatOpenAI(model="gpt-4o", temperature=0.2)
    response = await llm.ainvoke([HumanMessage(content=prompt)])

    json_match = re.search(r"```json\s*(\{.*?\})\s*```", response.content, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass
    return {"test_cases": [], "coverage_target": 80}


async def _run_tests(state: PipelineState, test_plan: dict) -> TestResult:
    """
    执行测试

    在实际项目中，这里会：
    1. 将测试代码写入文件
    2. 在 Docker 容器中运行 pytest
    3. 收集测试结果和覆盖率
    """
    # 模拟测试结果（实际项目中使用 subprocess 运行 pytest）
    num_tests = len(test_plan.get("test_cases", []))

    return TestResult(
        passed=num_tests,
        failed=0,
        skipped=0,
        coverage=0.85,
        command_output=f" Ran {num_tests} tests in 0.5s\\nOK",
    )
