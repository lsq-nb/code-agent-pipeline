"""
LangGraph 流水线图构建
"""

from langgraph.graph import END, StateGraph

from ..models import PipelineState
from ..nodes import (
    analyze_node,
    code_node,
    design_node,
    document_node,
    review_node,
    router_node,
    test_node,
)


def build_pipeline_graph() -> StateGraph:
    """
    构建完整的流水线状态机

    流程：
    analyze → design → code → review → [document → test] → END
                  ↑_______________|
                         修复循环
    """
    graph = StateGraph(PipelineState)

    # 注册节点
    graph.add_node("analyze", analyze_node)
    graph.add_node("design", design_node)
    graph.add_node("code", code_node)
    graph.add_node("review", review_node)
    graph.add_node("document", document_node)
    graph.add_node("test", test_node)
    graph.add_node("router", router_node)

    # 设置入口
    graph.set_entry_point("analyze")

    # 顺序连接
    graph.add_edge("analyze", "design")
    graph.add_edge("design", "code")
    graph.add_edge("code", "review")

    # 审查后路由
    graph.add_conditional_edges(
        "review",
        router_node,
        {
            "next": "document",
            "fix": "code",
            "end": END,
        },
    )

    # 文档 → 测试 → 结束
    graph.add_edge("document", "test")
    graph.add_edge("test", END)

    return graph


def compile_pipeline():
    """编译流水线图"""
    graph = build_pipeline_graph()
    return graph.compile()
