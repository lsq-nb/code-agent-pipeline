"""
路由节点
根据当前状态决定流程走向
"""

from typing import Any

from ..models import PipelineState, PipelineStage


def router_node(state: PipelineState) -> str:
    """
    路由节点

    根据审查结果和项目状态，决定下一步流程：
    - 审查通过 → 进入文档生成
    - 审查不通过 → 进入修复循环
    - 达到最大迭代次数 → 结束
    """
    # 检查是否达到最大迭代
    if state.iteration_count >= state.max_iterations:
        state.add_message("router", f"达到最大迭代次数 ({state.max_iterations})，结束流程")
        return "end"

    # 检查审查结果
    if state.review:
        if state.review.verdict.value == "approved":
            state.add_message("router", "代码审查通过，进入下一阶段")
            return "next"
        elif state.review.verdict.value == "changes_requested":
            state.add_message("router", "需要修改，进入修复循环")
            state.should_loop = True
            state.loop_reason = "代码审查发现需要修改的问题"
            return "fix"

    # 默认：继续
    return "next"
