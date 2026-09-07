"""
全局配置管理
使用 pydantic-settings 加载环境变量，支持 .env 文件
"""

from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class LLMConfig(BaseModel):
    """大语言模型配置"""

    provider: str = Field(default="openai", description="LLM 提供商")
    model: str = Field(default="gpt-4o", description="模型名称")
    temperature: float = Field(default=0.2, ge=0.0, le=1.0, description="采样温度")
    max_tokens: int = Field(default=4096, description="最大输出 token 数")
    api_key: Optional[str] = Field(default=None, description="API 密钥")
    base_url: Optional[str] = Field(
        default=None, description="API 端点（兼容 OpenAI 格式时填写）"
    )


class GraphConfig(BaseModel):
    """LangGraph 状态机配置"""

    max_iterations: int = Field(default=10, description="最大迭代次数")
    timeout_seconds: int = Field(default=300, description="超时时间（秒）")
    parallel_branches: bool = Field(default=True, description="是否启用并行分支")
    retry_policy: str = Field(default="exponential", description="重试策略")


class RAGConfig(BaseModel):
    """RAG 检索配置"""

    embedding_model: str = Field(
        default="text-embedding-3-small", description="嵌入模型"
    )
    top_k: int = Field(default=5, description="检索返回条数")
    chunk_size: int = Field(default=512, description="文档分块大小")
    chunk_overlap: int = Field(default=64, description="分块重叠大小")
    collection_name: str = Field(default="code_standards", description="向量库集合名")
    persist_directory: str = Field(default=".cache/chroma", description="持久化目录")


class AgentConfig(BaseModel):
    """智能体配置"""

    max_retries: int = Field(default=3, description="最大重试次数")
    verbose: bool = Field(default=False, description="是否启用详细日志")
    cache_enabled: bool = Field(default=True, description="是否启用缓存")
    concurrent_tasks: int = Field(default=3, description="并发任务数")


class PipelineConfig(BaseSettings):
    """
    流水线全局配置

    环境变量（可在 .env 文件中设置）：
        LLM_PROVIDER: 默认 openai
        LLM_MODEL: 默认 gpt-4o
        OPENAI_API_KEY: OpenAI API 密钥
        OPENAI_BASE_URL: OpenAI API 端点
        GRAPH_MAX_ITERATIONS: 默认 10
        RAG_TOP_K: 默认 5
        DOCKER_ENABLED: 默认 false
    """

    # 项目路径
    project_root: Path = Field(default=Path(__file__).parent.parent)
    output_dir: Path = Field(default=Path("output"))
    artifacts_dir: Path = Field(default=Path("artifacts"))

    # LLM 配置
    llm: LLMConfig = Field(default_factory=LLMConfig)

    # 状态机配置
    graph: GraphConfig = Field(default_factory=GraphConfig)

    # RAG 配置
    rag: RAGConfig = Field(default_factory=RAGConfig)

    # 智能体配置
    agents: AgentConfig = Field(default_factory=AgentConfig)

    # 服务配置
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)
    debug: bool = Field(default=False)

    # Docker 沙箱
    docker_enabled: bool = Field(default=False)
    docker_image: str = Field(default="python:3.11-slim")
    docker_working_dir: str = Field(default="/workspace")

    # MCP 配置
    mcp_servers: dict = Field(default_factory=dict)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# 全局配置实例（懒加载）
_config: Optional[PipelineConfig] = None


def get_config() -> PipelineConfig:
    """获取全局配置实例（单例）"""
    global _config
    if _config is None:
        _config = PipelineConfig()
    return _config


def reset_config() -> None:
    """重置全局配置（用于测试）"""
    global _config
    _config = None
