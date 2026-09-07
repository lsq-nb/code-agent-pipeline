# Contributing

感谢你对本项目的关注！以下是贡献指南。

## 开发环境设置

```bash
# 克隆仓库
git clone https://github.com/your-org/code-agent-pipeline.git
cd code-agent-pipeline

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
make install

# 安装预提交钩子
pre-commit install
```

## 提交规范

遵循 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

```
feat: 新增代码生成节点
fix: 修复审查结果解析 bug
docs: 更新 API 文档
test: 添加 RAG 集成测试
refactor: 重构状态机路由逻辑
chore: 更新依赖版本
```

## PR 流程

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feat/your-feature`)
3. 提交更改 (`git commit -m 'feat: ...'`)
4. 推送到分支 (`git push origin feat/your-feature`)
5. 创建 Pull Request

## 代码风格

- 使用 `ruff` 进行代码检查和格式化
- 使用 `mypy` 进行类型检查
- 确保所有测试通过后再提交 PR

```bash
make lint    # 代码检查
make format  # 格式化代码
make test    # 运行测试
```
