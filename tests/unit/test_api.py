"""
API 层测试
"""

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
    """流水线端点测试"""

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
        # Empty requirement bypasses Pydantic validation (no validator on PipelineRequest)
        # and the pipeline runs, failing with 500 since LLM isn't configured
        resp = client.post("/api/pipeline/run", json={"requirement": ""})
        assert resp.status_code == 500


class TestTaskEndpoints:
    """任务管理端点测试"""

    def test_get_history(self, client):
        resp = client.get("/api/tasks/history")
        assert resp.status_code == 200

    def test_get_stats(self, client):
        resp = client.get("/api/tasks/stats")
        assert resp.status_code == 200
