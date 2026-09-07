"""
测试工程师智能体
负责生成测试用例、执行测试、分析覆盖率
"""

from typing import Optional

from crewai import Agent

from ..rag.retriever import CodeRetriever
from ..tools.test_runner import TestRunnerTool


class Tester:
    """
    测试工程师智能体

    职责：
    - 生成单元测试、集成测试用例
    - 执行测试套件
    - 分析测试覆盖率
    - 识别测试失败原因
    - 提供测试改进建议
    """

    ROLE_TEMPLATE = """\
你是资深测试工程师，精通单元测试、集成测试和 TDD 实践。
你的任务是为代码生成全面的测试用例并执行测试。

## 测试策略
1. **单元测试**: 每个函数/方法的独立测试
2. **边界测试**: 边界条件和异常输入
3. **集成测试**: 模块间交互测试
4. **覆盖率目标**: 行覆盖率 >= 80%

## 测试风格
- 使用 pytest 框架
- 遵循 Arrange-Act-Assert 模式
- 测试名称清晰描述预期行为
- 使用参数化测试覆盖多种场景

## 输出格式
严格按照以下 JSON 结构输出：
```json
{{
  "test_cases": [
    {{"name": "test_function_name", "description": "测试描述", "code": "def test_xxx...\\n"}}
  ],
  "test_command": "pytest tests/ -v --cov=src --cov-report=term",
  "coverage_target": 80,
  "notes": "测试说明"
}}
```

## 代码内容
{code_content}

## 项目上下文
{project_context}

请开始编写测试用例，输出 JSON 格式结果。
"""

    def __init__(self, llm=None, test_runner: Optional[TestRunnerTool] = None,
                 rag_retriever: Optional[CodeRetriever] = None):
        self.llm = llm
        self.test_runner = test_runner or TestRunnerTool()
        self.rag_retriever = rag_retriever

        self.agent = Agent(
            role="测试工程师",
            goal="生成全面测试用例并执行测试验证代码质量",
            backstory="""\
资深测试工程师，10年+软件测试经验，精通 pytest、 unittest 等测试框架，
熟悉 TDD 和 BDD 方法论，注重测试覆盖率和代码质量保障。""",
            llm=llm,
            verbose=True,
            allow_delegation=False,
        )

    def generate_tests(self, code_content: str, project_context: str = "") -> dict:
        """
        生成测试用例

        参数:
            code_content: 代码内容
            project_context: 项目上下文

        返回:
            测试生成结果
        """
        prompt = self.ROLE_TEMPLATE.format(
            code_content=code_content[:6000],
            project_context=project_context or "无特定上下文",
        )

        result = self.agent.execute_task(prompt)
        return self._parse_result(result)

    def run_tests(self, path: str = ".", mark: Optional[str] = None,
                  pattern: Optional[str] = None) -> dict:
        """
        执行测试

        参数:
            path: 测试路径
            mark: pytest 标记
            pattern: 测试名称匹配模式

        返回:
            测试结果
        """
        return self.test_runner._run(path=path, mark=mark, pattern=pattern)

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
