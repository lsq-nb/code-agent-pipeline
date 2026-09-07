# 代码研发辅助多智能体流水线

基于 **LangGraph** + **CrewAI** 的全流程代码研发辅助多智能体流水线，串联需求拆解到代码优化的全环节，实现编码自动化与规范化。

## ✨ 功能特性

- **🔍 智能需求分析** — 深度解析用户需求，拆分为可执行的子任务
- **🏗️ 自动架构设计** — 生成系统架构方案、模块划分和 API 设计
- **💻 代码自动生成** — 根据设计文档生成高质量、可运行的代码
- **🔎 代码智能审查** — 多维度代码审查（质量/安全/性能/规范）
- **📝 文档自动生成** — README、API 文档、用户指南一键生成
- **🧪 测试用例生成** — 自动生成 pytest 测试用例并执行
- **🔄 迭代修复循环** — 审查不通过自动进入修复循环
- **📚 RAG 知识检索** — 加载项目代码规范和历史文档约束输出风格
- **🛠️ MCP 工具集成** — 跨工具上下文同步，Function Call 集成开发工具链
- **🐳 Docker 沙箱** — 隔离执行环境，保障测试安全

## 🏗️ 技术架构

```
┌─────────────────────────────────────────────────────────────┐
│                     FastAPI REST API                        │
├─────────────────────────────────────────────────────────────┤
│                    Orchestrator Agent                       │
│              (LangGraph State Machine)                      │
├──────┬──────┬──────┬──────┬────────┬──────┬──────┤
│ Analyze│Design│ Code │Review│Document│ Test │Loop  │
├──────┼──────┼──────┼──────┼────────┼──────┼──────┤
│ CrewAI │CrewAI│CrewAI│CrewAI│CrewAI  │CrewAI│      │
│Agent   │Agent │Agent │Agent │Agent   │Agent │      │
├──────┴──────┴──────┴──────┴────────┴──────┴──────┤
│           Tools & RAG Layer                        │
│  GitTool │ FileTool │ Formatter │ TestRunner │MCP  │
├───────────────────────────────────────────────────┤
│              ChromaDB (RAG Vector Store)           │
└───────────────────────────────────────────────────┘
```

## 📦 安装

### 从源码安装

```bash
# 克隆仓库
git clone https://github.com/your-org/code-agent-pipeline.git
cd code-agent-pipeline

# 安装依赖
pip install -e ".[dev]"

# 或安装全部依赖（含 MCP）
pip install -e ".[dev,mcp]"
```

### Docker 一键启动

```bash
# 复制环境变量配置
cp .env.example .env
# 编辑 .env 填入你的 API Key

# 启动服务
docker compose up -d

# 查看日志
docker compose logs -f
```

## ⚙️ 配置

复制 `.env.example` 为 `.env` 并填写必要配置：

```bash
cp .env.example .env
```

关键配置项：

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `LLM_PROVIDER` | LLM 提供商 | `openai` |
| `LLM_MODEL` | 模型名称 | `gpt-4o` |
| `OPENAI_API_KEY` | OpenAI API 密钥 | - |
| `GRAPH_MAX_ITERATIONS` | 最大迭代次数 | `10` |
| `RAG_TOP_K` | 检索返回条数 | `5` |
| `DOCKER_ENABLED` | 是否启用 Docker | `false` |

## 🚀 快速开始

### CLI 模式

```bash
# 运行完整流水线
python -m code_agent_pipeline.cli run "开发一个用户认证 API" \
  --context "Python FastAPI + SQLAlchemy" \
  --constraint "支持 JWT 认证" \
  --constraint "密码使用 bcrypt 加密" \
  -o output

# 初始化 RAG 索引
python -m code_agent_pipeline.cli setup --rag-source ./my-project

# 启动 API 服务
python -m code_agent_pipeline.cli serve --port 8000
```

### Python API 模式

```python
from code_agent_pipeline.graph import compile_pipeline
from code_agent_pipeline.models import PipelineState

# 编译流水线
graph = compile_pipeline()

# 创建任务状态
state = PipelineState(
    requirement="开发一个 RESTful API 服务",
    project_context="Python FastAPI + PostgreSQL",
    constraints=["支持 JWT 认证", "分页查询"],
)

# 执行流水线
result = graph.invoke(state)
print(f"完成阶段: {result['current_stage']}")
print(f"生成代码: {len(result['code_generation'].artifacts)} 个文件")
```

### REST API 模式

```bash
# 启动服务
make dev

# 提交任务
curl -X POST http://localhost:8000/api/pipeline/run \
  -H "Content-Type: application/json" \
  -d '{
    "requirement": "开发一个用户管理系统",
    "project_context": "Python FastAPI",
    "constraints": ["JWT认证", "Redis缓存"]
  }'

# 查询状态
curl http://localhost:8000/api/pipeline/status/task_0001

# API 文档
open http://localhost:8000/docs
```

## 📁 项目结构

```
code-agent-pipeline/
├── code_agent_pipeline/       # 核心包
│   ├── __init__.py
│   ├── config.py              # 配置管理
│   ├── models.py              # 数据模型
│   ├── cli.py                 # 命令行入口
│   ├── agents/                # CrewAI 智能体
│   │   ├── orchestrator.py    # 编排器
│   │   ├── requirement_analyst.py
│   │   ├── architect.py
│   │   ├── coder.py
│   │   ├── reviewer.py
│   │   ├── doc_writer.py
│   │   └── tester.py
│   ├── graph/                 # LangGraph 流水线图
│   │   └── __init__.py
│   ├── nodes/                 # 状态机节点
│   │   ├── analyze_node.py
│   │   ├── design_node.py
│   │   ├── code_node.py
│   │   ├── review_node.py
│   │   ├── document_node.py
│   │   ├── test_node.py
│   │   └── router_node.py
│   ├── tools/                 # 工具链
│   │   ├── git_tool.py        # Git 操作
│   │   ├── file_tool.py       # 文件操作
│   │   ├── code_formatter.py  # 代码格式化
│   │   ├── test_runner.py     # 测试执行
│   │   └── mcp_client.py      # MCP 客户端
│   ├── rag/                   # RAG 检索
│   │   ├── embedder.py        # 嵌入服务
│   │   ├── retriever.py       # 检索器
│   │   └── indexer.py         # 索引器
│   ├── api/                   # FastAPI 服务
│   │   ├── main.py
│   │   └── routers/
│   └── utils/                 # 工具函数
│       ├── llm.py
│       ├── serializer.py
│       ├── validation.py
│       └── logging.py
├── tests/                     # 测试
│   ├── unit/
│   ├── integration/
│   └── test_models.py
├── .github/workflows/         # CI/CD
├── Dockerfile
├── docker-compose.yml
├── Makefile
├── pyproject.toml
└── README.md
```

## 🧪 测试

```bash
# 运行所有测试
make test

# 运行单元测试
make test-unit

# 运行集成测试
make test-integration

# 查看覆盖率
pytest --cov=code_agent_pipeline --cov-report=html
```

## 📖 核心概念

### LangGraph 状态机

流水线采用 LangGraph 的状态机架构，每个阶段是一个节点，通过条件边实现智能路由：

```
analyze → design → code → review → [document → test] → END
                        ↑_______________|
                              修复循环
```

### CrewAI 多智能体协作

每个阶段由专业的 CrewAI Agent 执行，具备角色化的提示词和工具访问权限：

| 智能体 | 角色 | 职责 |
|--------|------|------|
| Orchestrator | 编排器 | 协调整体流程，管理状态流转 |
| RequirementAnalyst | 需求分析师 | 需求拆解、任务拆分 |
| Architect | 架构师 | 系统设计、API 设计 |
| Coder | 程序员 | 代码生成、文件创建 |
| Reviewer | 审查员 | 代码审查、安全检查 |
| DocWriter | 文档工程师 | 文档生成 |
| Tester | 测试工程师 | 测试生成、执行 |

### RAG 代码规范检索

通过 ChromaDB 向量库存储和检索代码规范、最佳实践：

```python
# 索引项目代码
indexer = CodeIndexer()
indexer.index_directory("./my-project")

# 检索相关规范
retriever = CodeRetriever()
docs = retriever.search("异步编程最佳实践", top_k=3)
```

### MCP 工具集成

支持通过 MCP（Model Context Protocol）连接外部工具：

```python
from code_agent_pipeline.tools.mcp_client import MCPClient

client = MCPClient(
    server_name="filesystem",
    command="npx",
    args=["-y", "@modelcontextprotocol/server-filesystem", "/workspace"],
)
tools = await client.get_tools()
```

## 🔌 API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/pipeline/run` | 执行完整流水线 |
| GET | `/api/pipeline/status/{task_id}` | 查询任务状态 |
| GET | `/api/pipeline/stages` | 获取可用阶段 |
| GET | `/api/tasks/history` | 任务历史记录 |
| GET | `/api/tasks/stats` | 任务统计 |
| GET | `/api/health` | 健康检查 |

完整 API 文档：`http://localhost:8000/docs`

## 🐳 Docker 部署

```bash
# 构建镜像
docker build -t code-agent-pipeline .

# 运行容器
docker run -p 8000:8000 \
  -e OPENAI_API_KEY=your-key \
  -v ./output:/app/output \
  code-agent-pipeline

# 使用 Docker Compose
docker compose up -d
```

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！请参考 [CONTRIBUTING.md](.github/CONTRIBUTING.md)

## 🙏 致谢

- [LangGraph](https://github.com/langchain-ai/langgraph) - 状态机编排框架
- [CrewAI](https://github.com/joaomdmoura/crewai) - 多智能体框架
- [FastAPI](https://github.com/tiangolo/fastapi) - 高性能 Web 框架
- [ChromaDB](https://github.com/chroma-core/chroma) - 向量数据库
