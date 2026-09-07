"""
代码审查节点
对生成的代码进行质量审查、安全检查、性能分析
"""

import json
import re
from typing import Any

from ..models import PipelineState, PipelineStage, TaskStatus, ReviewResult, ReviewVerdict


async def review_node(state: PipelineState) -> dict[str, Any]:
    """
    代码审查节点

    对生成的所有代码文件进行多维度审查：
    - 代码质量（可读性、可维护性）
    - 安全性（注入、泄露、权限）
    - 性能（效率、资源消耗）
    - 规范性（编码风格、注释）
    """
    state.current_stage = PipelineStage.REVIEW
    state.add_message("review", "开始代码审查...")

    if not state.code_generation:
        state.add_error("代码生成为空，跳过审查")
        state.review = ReviewResult(
            verdict=ReviewVerdict.COMMENT_ONLY,
            quality_score=0.0,
            issues=[],
            suggestions=["无代码可审查"],
        )
        return state.to_dict()

    # 收集所有代码进行审查
    all_reviews = []
    for artifact in state.code_generation.artifacts:
        review = await _review_single_file(artifact, state)
        all_reviews.append(review)

    # 汇总审查结果
    summary = _summarize_reviews(all_reviews, state)
    state.review = summary

    state.add_message("review", f"审查完成，判定: {summary.verdict.value}, 平均分: {summary.quality_score:.1f}")
    state.update_timestamp()

    return {
        "review": summary,
        "current_stage": PipelineStage.CODE,  # 由路由器决定下一步
        "agent_messages": state.agent_messages,
    }


async def _review_single_file(artifact, state: PipelineState) -> dict:
    """审查单个代码文件"""
    from langchain_openai import ChatOpenAI  # noqa: PLC0415
    from langchain_core.messages import HumanMessage  # noqa: PLC0415

    prompt = f"""\
请审查以下代码的质量、安全性和性能：

## 文件：{artifact.file_path}

```{artifact.language}
{artifact.content[:4000]}
```

## 项目上下文
{state.project_context or "无特定上下文"}

请按以下 JSON 格式输出审查结果：
```json
{{
  "severity": "critical|major|minor|style",
  "issues": [{{"line": 42, "message": "问题描述", "type": "quality|security|performance|style"}}],
  "suggestions": ["改进建议1"],
  "quality_score": 8.5
}}
```
"""

    llm = ChatOpenAI(model="gpt-4o", temperature=0.1)
    response = await llm.ainvoke([HumanMessage(content=prompt)])

    return _parse_review_response(response.content)


def _parse_review_response(content: str) -> dict:
    """解析审查响应"""
    json_match = re.search(r"```json\s*(\{.*?\})\s*```", content, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass
    return {"issues": [], "suggestions": ["无法解析审查结果"], "quality_score": 5.0}


def _summarize_reviews(reviews: list[dict], state: PipelineState) -> ReviewResult:
    """汇总多个文件的审查结果"""
    all_issues = []
    all_suggestions = []
    security_findings = []
    performance_findings = []
    scores = []

    for review in reviews:
        all_issues.extend(review.get("issues", []))
        all_suggestions.extend(review.get("suggestions", []))
        score = review.get("quality_score", 5.0)
        scores.append(score)

        # 分类问题
        for issue in review.get("issues", []):
            issue_type = issue.get("type", "quality")
            if issue_type == "security":
                security_findings.append(f"{issue['message']} (line {issue.get('line', '?')})")
            elif issue_type == "performance":
                performance_findings.append(issue["message"])

    avg_score = sum(scores) / max(len(scores), 1)

    # 确定判定
    critical_count = sum(1 for i in all_issues if i.get("severity") == "critical")
    if critical_count > 0:
        verdict = ReviewVerdict.REJECTED
    elif avg_score >= 7.0:
        verdict = ReviewVerdict.APPROVED
    elif avg_score >= 5.0:
        verdict = ReviewVerdict.CHANGES_REQUESTED
    else:
        verdict = ReviewVerdict.REJECTED

    # 确定质量等级
    if avg_score >= 8.5:
        level = "excellent"
    elif avg_score >= 7.0:
        level = "good"
    elif avg_score >= 5.0:
        level = "needs_improvement"
    else:
        level = "poor"

    return ReviewResult(
        verdict=verdict,
        quality_score=round(avg_score, 1),
        quality_level=level,
        issues=all_issues,
        suggestions=all_suggestions[:10],
        security_findings=security_findings,
        performance_findings=performance_findings,
    )
