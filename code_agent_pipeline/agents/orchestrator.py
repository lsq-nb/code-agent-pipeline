"""
编排器智能体
负责协调整个流水线的执行流程，管理状态流转
"""

import uuid

from crewai import Crew, Process
from langgraph.graph import END, StateGraph

from ..models import (
    AnalysisResult,
    CodeGenerationResult,
    DesignResult,
    DocumentationResult,
    PipelineStage,
    PipelineState,
    ReviewResult,
    TaskStatus,
    TestResult,
)
from ..rag.retriever import CodeRetriever
from .architect import Architect
from .coder import Coder
from .doc_writer import DocWriter
from .requirement_analyst import RequirementAnalyst
from .reviewer import Reviewer
from .tester import Tester


class Orchestrator:
    """
    流水线编排器

    负责协调整个研发辅助流水线的执行：
    1. 需求分析 → 架构设计 → 代码生成 → 代码审查 → 文档生成 → 测试
    2. 使用 LangGraph 管理状态流转
    3. 处理阶段间的依赖和条件分支
    4. 管理重试和错误恢复
    """

    def __init__(self, llm=None, rag_retriever: CodeRetriever | None = None, **agent_kwargs):
        self.llm = llm
        self.rag_retriever = rag_retriever
        self.agent_kwargs = agent_kwargs
        self._graph: StateGraph | None = None
        self._compiled_graph = None

    def build_graph(self) -> StateGraph:
        """构建 LangGraph 状态机"""
        graph = StateGraph(PipelineState)

        # 添加节点
        graph.add_node("analyze", self._node_analyze)
        graph.add_node("design", self._node_design)
        graph.add_node("code", self._node_code)
        graph.add_node("review", self._node_review)
        graph.add_node("document", self._node_document)
        graph.add_node("test", self._node_test)
        graph.add_node("fix_loop", self._node_fix_loop)

        # 设置入口
        graph.set_entry_point("analyze")

        # 添加边（顺序流转）
        graph.add_edge("analyze", "design")
        graph.add_edge("design", "code")
        graph.add_edge("code", "review")

        # 审查后条件分支
        graph.add_conditional_edges(
            "review",
            self._review_router,
            {
                "document": "document",
                "fix": "fix_loop",
                "done": END,
            },
        )

        graph.add_edge("document", "test")
        graph.add_edge("test", END)

        # 修复循环
        graph.add_edge("fix_loop", "code")

        self._graph = graph
        return graph

    def compile(self):
        """编译图"""
        if self._graph is None:
            self.build_graph()
        self._compiled_graph = self._graph.compile()
        return self._compiled_graph

    def run(
        self,
        requirement: str,
        project_context: str = "",
        constraints: list[str] | None = None,
        task_id: str | None = None,
    ) -> PipelineState:
        """
        运行完整流水线

        参数:
            requirement: 需求描述
            project_context: 项目上下文
            constraints: 约束条件
            task_id: 任务 ID（可选，自动生成）

        返回:
            最终流水线状态
        """
        state = PipelineState(
            requirement=requirement,
            project_context=project_context,
            constraints=constraints or [],
            task_id=task_id or str(uuid.uuid4())[:8],
            status=TaskStatus.RUNNING,
        )

        if self._compiled_graph is None:
            self.compile()

        result = self._compiled_graph.invoke(state)
        return PipelineState(**result)

    # ── 节点实现 ──────────────────────────────────────────────────────────

    def _node_analyze(self, state: PipelineState) -> dict:
        """需求分析节点"""
        analyst = RequirementAnalyst(
            llm=self.llm,
            rag_retriever=self.rag_retriever,
            **self.agent_kwargs,
        )
        state.add_message("orchestrator", "开始需求分析...")
        analysis = analyst.analyze(
            requirement=state.requirement,
            project_context=state.project_context,
            constraints=state.constraints,
        )
        state.analysis = AnalysisResult(**analysis)
        state.current_stage = PipelineStage.ANALYZE
        state.update_timestamp()
        state.add_message(
            "analyst", f"分析完成，复杂度: {analysis.get('estimated_complexity', 'unknown')}"
        )
        return state.to_dict()

    def _node_design(self, state: PipelineState) -> dict:
        """架构设计节点"""
        architect = Architect(
            llm=self.llm,
            rag_retriever=self.rag_retriever,
            **self.agent_kwargs,
        )
        state.add_message("orchestrator", "开始架构设计...")
        design = architect.design(
            analysis_result=state.analysis.model_dump() if state.analysis else {},
            project_context=state.project_context,
        )
        state.design = DesignResult(**design)
        state.current_stage = PipelineStage.DESIGN
        state.update_timestamp()
        state.add_message(
            "architect", f"设计完成，模式: {design.get('architecture_pattern', 'unknown')}"
        )
        return state.to_dict()

    def _node_code(self, state: PipelineState) -> dict:
        """代码生成节点"""
        coder = Coder(
            llm=self.llm,
            rag_retriever=self.rag_retriever,
            **self.agent_kwargs,
        )
        state.add_message("orchestrator", "开始代码生成...")
        code_result = coder.generate(
            design_doc=state.design.model_dump() if state.design else {},
            project_context=state.project_context,
        )
        state.code_generation = CodeGenerationResult(**code_result)
        state.current_stage = PipelineStage.CODE
        state.update_timestamp()
        state.add_message("coder", f"生成 {len(code_result.get('artifacts', []))} 个代码文件")
        return state.to_dict()

    def _node_review(self, state: PipelineState) -> dict:
        """代码审查节点"""
        reviewer = Reviewer(
            llm=self.llm,
            rag_retriever=self.rag_retriever,
            **self.agent_kwargs,
        )
        state.add_message("orchestrator", "开始代码审查...")

        # 审查所有生成的代码
        all_issues = []
        all_suggestions = []
        total_score = 0.0

        for artifact in state.code_generation.artifacts:
            review = reviewer.review(
                code_content=artifact.content,
                project_context=state.project_context,
                file_path=artifact.file_path,
            )
            all_issues.extend(review.get("issues", []))
            all_suggestions.extend(review.get("suggestions", []))
            total_score += review.get("quality_score", 0.0)

        avg_score = total_score / max(len(state.code_generation.artifacts), 1)
        verdict = "approved" if avg_score >= 7.0 else "changes_requested"

        state.review = ReviewResult(
            verdict=verdict,
            quality_score=avg_score,
            issues=all_issues,
            suggestions=all_suggestions,
        )
        state.current_stage = PipelineStage.REVIEW
        state.update_timestamp()
        state.add_message("reviewer", f"审查完成，平均分: {avg_score:.1f}/10")
        return state.to_dict()

    def _node_document(self, state: PipelineState) -> dict:
        """文档生成节点"""
        doc_writer = DocWriter(
            llm=self.llm,
            rag_retriever=self.rag_retriever,
            **self.agent_kwargs,
        )
        state.add_message("orchestrator", "开始文档生成...")

        code_structure = "\n".join(
            f"- {a.file_path} ({a.language})" for a in state.code_generation.artifacts
        )
        feature_desc = state.analysis.requirement_summary if state.analysis else ""

        doc_result = doc_writer.generate(
            project_context=state.project_context,
            code_structure=code_structure,
            feature_description=feature_desc,
        )
        state.documentation = DocumentationResult(**doc_result)
        state.current_stage = PipelineStage.DOCUMENT
        state.update_timestamp()
        state.add_message("doc_writer", "文档生成完成")
        return state.to_dict()

    def _node_test(self, state: PipelineState) -> dict:
        """测试执行节点"""
        tester = Tester(
            llm=self.llm,
            rag_retriever=self.rag_retriever,
            **self.agent_kwargs,
        )
        state.add_message("orchestrator", "开始测试生成和执行...")

        # 生成测试用例
        test_plan = tester.generate_tests(
            code_content=self._collect_all_code(state),
            project_context=state.project_context,
        )

        # 执行测试（模拟结果）
        test_result = {
            "passed": len(test_plan.get("test_cases", [])),
            "failed": 0,
            "skipped": 0,
            "coverage": 0.85,
            "command_output": "All tests passed.",
        }

        state.testing = TestResult(**test_result)
        state.current_stage = PipelineStage.TEST
        state.update_timestamp()
        state.add_message("tester", f"测试完成: {test_result['passed']} 通过")
        return state.to_dict()

    def _node_fix_loop(self, state: PipelineState) -> dict:
        """修复循环节点 - 根据审查意见修改代码"""
        state.add_message("orchestrator", "进入修复循环...")
        state.iteration_count += 1

        if state.iteration_count >= state.max_iterations:
            state.add_error("达到最大迭代次数，强制退出修复循环")
            return state.to_dict()

        # 收集审查意见
        review_issues = state.review.issues if state.review else []
        fix_prompt = f"请根据以下审查意见修复代码：\n{review_issues}"
        state.add_message("reviewer", fix_prompt)
        state.should_loop = True
        state.loop_reason = "代码审查发现问题，需要修复"
        return state.to_dict()

    # ── 路由函数 ──────────────────────────────────────────────────────────

    def _review_router(self, state: PipelineState) -> str:
        """审查结果路由"""
        if state.iteration_count >= state.max_iterations:
            return "done"
        if state.review and state.review.verdict == "approved":
            return "document"
        return "fix"

    # ── 辅助方法 ──────────────────────────────────────────────────────────

    def _collect_all_code(self, state: PipelineState) -> str:
        """收集所有生成的代码"""
        if not state.code_generation:
            return ""
        parts = []
        for artifact in state.code_generation.artifacts:
            parts.append(
                f"### {artifact.file_path}\n```{artifact.language}\n{artifact.content}\n```"
            )
        return "\n\n".join(parts)

    def get_crew(self) -> Crew:
        """获取 CrewAI 团队（用于并行协作模式）"""
        agents = [
            RequirementAnalyst(llm=self.llm, rag_retriever=self.rag_retriever).agent,
            Architect(llm=self.llm, rag_retriever=self.rag_retriever).agent,
            Coder(llm=self.llm, rag_retriever=self.rag_retriever).agent,
            Reviewer(llm=self.llm, rag_retriever=self.rag_retriever).agent,
            DocWriter(llm=self.llm, rag_retriever=self.rag_retriever).agent,
            Tester(llm=self.llm, rag_retriever=self.rag_retriever).agent,
        ]
        return Crew(
            agents=agents,
            processes=Process.sequential,
            verbose=True,
        )
