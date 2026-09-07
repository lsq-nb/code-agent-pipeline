.PHONY: help install dev run test lint format docker-up docker-down clean

help: ## 显示可用命令
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## 安装依赖
	pip install -e ".[dev]"

install-mcp: ## 安装 MCP 依赖
	pip install -e ".[mcp]"

dev: ## 启动开发服务（热重载）
	uvicorn code_agent_pipeline.api.main:app --reload --host 0.0.0.0 --port 8000

run: ## 运行流水线（命令行模式）
	python -m code_agent_pipeline.cli

test: ## 运行所有测试
	pytest -v --cov=code_agent_pipeline --cov-report=term-missing

test-unit: ## 运行单元测试
	pytest -v tests/unit

test-integration: ## 运行集成测试
	pytest -v tests/integration

lint: ## 代码检查
	ruff check .
	mypy code_agent_pipeline/

format: ## 格式化代码
	ruff format .

docker-up: ## 启动 Docker 容器
	docker compose up -d

docker-down: ## 停止 Docker 容器
	docker compose down

docker-logs: ## 查看容器日志
	docker compose logs -f

clean: ## 清理构建产物
	rm -rf dist/ build/ *.egg-info/ .pytest_cache/ .ruff_cache/ .mypy_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
	rm -rf .coverage htmlcov/
