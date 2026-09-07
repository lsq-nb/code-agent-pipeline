"""
程序员智能体
负责根据设计文档生成高质量代码
"""

from crewai import Agent

from ..rag.retriever import CodeRetriever


class Coder:
    """
    程序员智能体

    职责：
    - 根据架构设计生成高质量代码
    - 遵循项目编码规范
    - 实现所有功能和边界条件
    - 编写必要的注释和文档字符串
    - 集成必要的测试用例
    """

    ROLE_TEMPLATE = """\
你是资深全栈开发工程师，精通 {languages} 等多语言开发。
你的任务是根据设计文档生成高质量、可运行的代码。

## 代码规范
- 遵循 PEP 8 / 项目编码规范
- 函数和类添加文档字符串
- 关键逻辑添加行内注释
- 错误处理完善
- 类型注解完整

## 代码质量要求
1. 可读性：命名清晰，结构合理
2. 健壮性：边界条件处理，异常捕获
3. 可测试性：模块化设计，易于单元测试
4. 安全性：输入验证，防止注入攻击
5. 性能：避免不必要的计算和资源消耗

## 输出格式
严格按照以下 JSON 结构输出代码产物列表：
```json
{{
  "artifacts": [
    {{
      "file_path": "src/module/file.py",
      "content": "#!/usr/bin/env python3\\n...代码内容...",
      "language": "python",
      "description": "文件功能描述",
      "dependencies": ["依赖包"],
      "test_required": true
    }}
  ],
  "build_instructions": "构建步骤说明",
  "environment_requirements": ["依赖1", "依赖2"],
  "notes": "注意事项"
}}
```

## 架构设计
{design_doc}

## 项目上下文
{project_context}

## 代码规范参考
{rag_context}

请开始编写代码，输出 JSON 格式结果。
"""

    def __init__(
        self,
        llm=None,
        tools=None,
        rag_retriever: CodeRetriever | None = None,
        target_languages: list[str] | None = None,
    ):
        self.llm = llm
        self.rag_retriever = rag_retriever
        self.target_languages = target_languages or ["python"]
        self.tools = tools or []

        langs_str = ", ".join(self.target_languages)
        self.agent = Agent(
            role="全栈开发工程师",
            goal="根据设计文档生成高质量、可运行的代码",
            backstory=f"""\
资深全栈开发工程师，精通 {langs_str} 等开发语言。
擅长将架构设计转化为清晰、可维护的生产级代码，
注重代码质量、安全规范和最佳实践。""",
            llm=llm,
            tools=self.tools,
            verbose=True,
            allow_delegation=False,
        )

    def generate(self, design_doc: dict, project_context: str = "") -> dict:
        """
        生成代码

        参数:
            design_doc: 架构设计文档
            project_context: 项目上下文

        返回:
            代码生成结果
        """
        rag_context = ""
        if self.rag_retriever:
            stack = design_doc.get("suggested_tech_stack", [])
            rag_docs = self.rag_retriever.search(" ".join(stack), top_k=3)
            rag_context = "\n\n".join([d["document"] for d in rag_docs])

        prompt = self.ROLE_TEMPLATE.format(
            languages=", ".join(self.target_languages),
            design_doc=self._format_design(design_doc),
            project_context=project_context or "无特定上下文",
            rag_context=rag_context or "无额外规范参考",
        )

        result = self.agent.execute_task(prompt)
        return self._parse_result(result)

    def _format_design(self, design: dict) -> str:
        """格式化设计文档为文本"""
        import json  # noqa: PLC0415

        return json.dumps(design, ensure_ascii=False, indent=2)

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
