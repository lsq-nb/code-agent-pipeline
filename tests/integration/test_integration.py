"""
集成测试 - 测试完整的流水线组件协作
"""

from unittest.mock import patch

import pytest


class TestGraphIntegration:
    """LangGraph 流水线集成测试"""

    @pytest.mark.asyncio
    async def test_graph_compiles(self):
        """测试图能成功编译"""
        from code_agent_pipeline.graph import build_pipeline_graph  # noqa: PLC0415

        graph = build_pipeline_graph()
        assert graph is not None
        # 编译应该不抛出异常
        compiled = graph.compile()
        assert compiled is not None

    @pytest.mark.asyncio
    async def test_analyze_node_integration(self):
        """测试分析节点的端到端流程"""
        from code_agent_pipeline.models import PipelineState  # noqa: PLC0415
        from code_agent_pipeline.nodes.analyze_node import analyze_node  # noqa: PLC0415

        state = PipelineState(
            requirement="开发一个简单的 REST API",
            project_context="Python FastAPI",
        )

        # 模拟 LLM 调用
        with patch("code_agent_pipeline.nodes.analyze_node._call_llm_analysis") as mock_llm:
            mock_llm.return_value = """
            ```json
            {
              "requirement_summary": "开发一个简单的REST API",
              "functional_requirements": ["用户认证", "数据 CRUD"],
              "non_functional_requirements": ["响应时间<200ms"],
              "technical_constraints": [],
              "risk_factors": [],
              "suggested_tech_stack": ["FastAPI", "SQLAlchemy"],
              "estimated_complexity": "medium",
              "tasks": [{"id": "T001", "description": "创建用户模型"}]
            }
            ```
            """
            result = await analyze_node(state)
            assert result["current_stage"].value == "design"
            assert result["analysis"].requirement_summary == "开发一个简单的REST API"

    @pytest.mark.asyncio
    async def test_code_node_integration(self):
        """测试代码生成节点"""
        from code_agent_pipeline.models import PipelineState  # noqa: PLC0415
        from code_agent_pipeline.nodes.code_node import code_node  # noqa: PLC0415

        state = PipelineState(
            requirement="测试",
            project_context="Python",
        )

        with patch("code_agent_pipeline.nodes.code_node._call_llm_code") as mock_llm:
            mock_llm.return_value = """
            ```json
            {
              "artifacts": [
                {
                  "file_path": "src/main.py",
                  "content": "print('hello')",
                  "language": "python",
                  "description": "主程序",
                  "dependencies": [],
                  "test_required": true
                }
              ],
              "build_instructions": "python src/main.py",
              "environment_requirements": ["Python >= 3.11"],
              "notes": ""
            }
            ```
            """
            result = await code_node(state)
            assert result["current_stage"].value == "review"
            assert len(result["code_generation"].artifacts) == 1


class TestRAGIntegration:
    """RAG 模块集成测试"""

    def test_retriever_init(self):
        """测试检索器初始化"""
        from code_agent_pipeline.rag.retriever import CodeRetriever  # noqa: PLC0415

        retriever = CodeRetriever(collection_name="test_collection")
        assert retriever.collection_name == "test_collection"

    def test_indexer_chunking(self):
        """测试索引器的文本分块"""
        from code_agent_pipeline.rag.indexer import CodeIndexer  # noqa: PLC0415

        indexer = CodeIndexer(chunk_size=100, chunk_overlap=10)
        long_text = "hello world " * 50
        chunks = indexer._chunk_text(long_text)
        assert len(chunks) > 1
        for chunk in chunks:
            assert len(chunk) <= 110  # 允许少量超额


class TestRouter:
    """路由逻辑测试"""

    def test_router_approved(self):
        from code_agent_pipeline.models import (  # noqa: PLC0415
            PipelineState,
            ReviewResult,
            ReviewVerdict,
        )
        from code_agent_pipeline.nodes.router_node import router_node  # noqa: PLC0415

        state = PipelineState(iteration_count=0, max_iterations=10)
        state.review = ReviewResult(verdict=ReviewVerdict.APPROVED)

        result = router_node(state)
        assert result == "next"

    def test_router_rejected(self):
        from code_agent_pipeline.models import (  # noqa: PLC0415
            PipelineState,
            ReviewResult,
            ReviewVerdict,
        )
        from code_agent_pipeline.nodes.router_node import router_node  # noqa: PLC0415

        state = PipelineState(iteration_count=0, max_iterations=10)
        state.review = ReviewResult(verdict=ReviewVerdict.CHANGES_REQUESTED)

        result = router_node(state)
        assert result == "fix"

    def test_router_max_iterations(self):
        from code_agent_pipeline.models import PipelineState  # noqa: PLC0415
        from code_agent_pipeline.nodes.router_node import router_node  # noqa: PLC0415

        state = PipelineState(iteration_count=10, max_iterations=10)
        result = router_node(state)
        assert result == "end"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
