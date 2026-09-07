"""
基于 LangGraph+CrewAI 的全流程代码研发辅助多智能体流水线

功能：
- 需求分析 → 架构设计 → 代码生成 → 代码审查 → 文档生成 → 测试生成
- 多角色智能体协作，分阶段状态机流转
- RAG 代码规范检索，MCP 跨工具上下文同步
- FastAPI RESTful 服务，Docker 沙箱隔离
"""

__version__ = "0.1.0"
__author__ = "Developer"
