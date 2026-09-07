"""
数据模型定义
使用 Pydantic 定义流水线中各阶段的数据结构
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator


# ── 枚举定义 ──────────────────────────────────────────────────────────────────


class TaskStatus(str, Enum):
    """任务状态枚举"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    NEEDS_REVIEW = "needs_review"
    NEEDS_FIX = "needs_fix"


class ReviewVerdict(str, Enum):
    """代码审查判定"""

    APPROVED = "approved"
    CHANGES_REQUESTED = "changes_requested"
    REJECTED = "rejected"
    COMMENT_ONLY = "comment_only"


class CodeQualityLevel(str, Enum):
    """代码质量等级"""

    EXCELLENT = "excellent"
    GOOD = "good"
    NEEDS_IMPROVEMENT = "needs_improvement"
    POOR = "poor"


class AgentRole(str, Enum):
    """智能体角色枚举"""

    REQUIREMENT_ANALYST = "requirement_analyst"
    ARCHITECT = "architect"
    CODER = "coder"
    REVIEWER = "reviewer"
    DOC_WRITER = "doc_writer"
    TESTER = "tester"
    ORCHESTRATOR = "orchestrator"


class PipelineStage(str, Enum):
    """流水线阶段枚举"""

    ANALYZE = "analyze"
    DESIGN = "design"
    CODE = "code"
    REVIEW = "review"
    DOCUMENT = "document"
    TEST = "test"
    DEPLOY = "deploy"


# ── 输入模型 ──────────────────────────────────────────────────────────────────


class RequirementInput(BaseModel):
    """需求输入"""

    requirement: str = Field(..., description="需求描述")
    project_context: str = Field(
        default="", description="项目上下文（技术栈、框架等）"
    )
    constraints: list[str] = Field(
        default=[], description="约束条件（性能、安全等）"
    )
    extra_instructions: str = Field(default="", description="额外说明")
    git_repo_url: Optional[str] = Field(
        default=None, description="关联的 Git 仓库 URL"
    )

    @field_validator("requirement")
    @classmethod
    def validate_requirement(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("需求描述不能为空")
        return v.strip()


class UpdateInput(BaseModel):
    """任务更新输入"""

    task_id: str
    status: TaskStatus
    message: str = ""
    data: Optional[dict[str, Any]] = None


# ── 中间状态模型 ──────────────────────────────────────────────────────────────


class AnalysisResult(BaseModel):
    """需求分析结果"""

    requirement_summary: str
    functional_requirements: list[str]
    non_functional_requirements: list[str]
    technical_constraints: list[str]
    risk_factors: list[str]
    suggested_tech_stack: list[str]
    estimated_complexity: str  # low / medium / high
    tasks: list[dict[str, str]] = Field(default=[], description="拆分的子任务")


class DesignResult(BaseModel):
    """架构设计结果"""

    architecture_pattern: str
    module_structure: list[str]
    api_design: list[dict[str, Any]]
    database_schema: Optional[dict[str, Any]] = None
    data_flow: str
    error_handling_strategy: str
    security_considerations: list[str]
    diagram_description: str  # Mermaid 图描述


class CodeArtifact(BaseModel):
    """代码产物"""

    file_path: str
    content: str
    language: str
    description: str
    dependencies: list[str] = Field(default=[])
    test_required: bool = Field(default=True)


class CodeGenerationResult(BaseModel):
    """代码生成结果"""

    artifacts: list[CodeArtifact]
    build_instructions: str
    environment_requirements: list[str]
    notes: str = ""


class ReviewResult(BaseModel):
    """代码审查结果"""

    verdict: ReviewVerdict = ReviewVerdict.COMMENT_ONLY
    quality_score: float = Field(default=0.0, ge=0.0, le=10.0)
    quality_level: CodeQualityLevel = CodeQualityLevel.NEEDS_IMPROVEMENT
    issues: list[dict[str, Any]] = Field(default=[])
    suggestions: list[str] = Field(default=[])
    security_findings: list[str] = Field(default=[])
    performance_findings: list[str] = Field(default=[])
    diff_command: Optional[str] = None


class TestResult(BaseModel):
    """测试执行结果"""

    passed: int
    failed: int
    skipped: int
    errors: list[dict[str, Any]] = Field(default=[])
    coverage: float = Field(default=0.0, ge=0.0, le=1.0)
    command_output: str = ""


class DocumentationResult(BaseModel):
    """文档生成结果"""

    readme: str
    api_docs: str
    user_guide: str
    changelog: str
    contributing_guidelines: str


# ── 流水线状态模型 ────────────────────────────────────────────────────────────


class PipelineState(BaseModel):
    """
    LangGraph 流水线主状态
    承载全流程流转所需的完整上下文
    """

    # 输入
    requirement: str = ""
    project_context: str = ""
    constraints: list[str] = Field(default=[])
    git_repo_url: Optional[str] = None

    # 阶段产物
    analysis: Optional[AnalysisResult] = None
    design: Optional[DesignResult] = None
    code_generation: Optional[CodeGenerationResult] = None
    review: Optional[ReviewResult] = None
    testing: Optional[TestResult] = None
    documentation: Optional[DocumentationResult] = None

    # 控制流
    current_stage: PipelineStage = PipelineStage.ANALYZE
    iteration_count: int = 0
    max_iterations: int = 10
    should_loop: bool = False
    loop_reason: str = ""

    # 元数据
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    agent_messages: list[dict[str, Any]] = Field(default=[])
    errors: list[str] = Field(default=[])

    # 运行时
    task_id: str = ""
    status: TaskStatus = TaskStatus.PENDING

    def update_timestamp(self) -> None:
        """更新状态时间戳"""
        self.updated_at = datetime.utcnow()

    def add_message(self, agent: str, message: str) -> None:
        """添加智能体消息"""
        self.agent_messages.append(
            {
                "agent": agent,
                "message": message,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

    def add_error(self, error: str) -> None:
        """添加错误信息"""
        self.errors.append(f"[{datetime.utcnow().isoformat()}] {error}")

    def to_dict(self) -> dict[str, Any]:
        """转换为字典（序列化用）"""
        return self.model_dump(exclude_unset=True, by_alias=True)


# ── API 响应模型 ──────────────────────────────────────────────


class PipelineResponse(BaseModel):
    """流水线执行响应"""

    success: bool
    task_id: str
    stage: str
    status: str
    message: str = ""
    result: Optional[dict[str, Any]] = None
    errors: list[str] = Field(default=[])


class TaskHistoryItem(BaseModel):
    """历史任务条目"""

    task_id: str
    requirement: str
    created_at: datetime
    final_stage: str
    final_status: str
    summary: str = ""


class HealthResponse(BaseModel):
    """健康检查响应"""

    status: str
    version: str
    components: dict[str, str] = Field(default_factory=dict)
