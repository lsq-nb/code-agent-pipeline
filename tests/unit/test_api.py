"""
API 层测试
"""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from code_agent_pipeline.api.main import app


@pytest.fixture
def client():
    return TestClient(app)


class TestHealthEndpoints:
    """健康检查端点测试"""

    def test_health(self, client):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "components" in data

    def test_readiness(self, client):
        resp = client.get("/api/health/ready")
        assert resp.status_code == 200
        assert resp.json()["ready"] is True

    def test_liveness(self, client):
        resp = client.get("/api/health/live")
        assert resp.status_code == 200
        assert resp.json()["alive"] is True


class TestPipelineEndpoints:
    """流水线端点测试（流水线执行 mock 掉，避免真实 LLM 调用）"""

    def test_get_stages(self, client):
        resp = client.get("/api/pipeline/stages")
        assert resp.status_code == 200
        stages = resp.json()["stages"]
        assert "analyze" in stages
        assert "code" in stages
        assert "review" in stages

    def test_run_pipeline_missing_requirement(self, client):
        resp = client.post("/api/pipeline/run", json={})
        assert resp.status_code == 422  # 验证失败

    def test_run_pipeline_empty_requirement(self, client):
        # 空需求绕过 Pydantic 校验，流水线真正执行。
        # 此处 mock 掉图的 ainvoke，避免触发真实 LLM，使测试快且可复现。
        from code_agent_pipeline.api.routers import pipeline as pmod  # noqa: PLC0415

        with patch.object(pmod, "compiled_graph") as fake_graph:
            fake_graph.ainvoke = AsyncMock(return_value={"requirement": ""})
            resp = client.post("/api/pipeline/run", json={"requirement": ""})
        assert resp.status_code in (200, 500)


class TestTaskEndpoints:
    """任务管理端点测试"""

    def test_get_history(self, client):
        resp = client.get("/api/tasks/history")
        assert resp.status_code == 200

    def test_get_stats(self, client):
        resp = client.get("/api/tasks/stats")
        assert resp.status_code == 200
