"""单元测试 — API 路由 mock LLM"""
import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from backend.main import app
    with patch("backend.main.verify_api_key", return_value=None):
        with patch("backend.memory.story_db.init_db", new_callable=AsyncMock):
            yield TestClient(app)


class TestHealthEndpoint:
    def test_health_returns_correlation_id(self, client):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        assert "X-Correlation-ID" in resp.headers

    def test_health_json_structure(self, client):
        resp = client.get("/api/health")
        data = resp.json()
        assert "status" in data
        assert "checks" in data
        assert "database" in data["checks"]


class TestStoriesAPI:
    def test_list_stories_requires_auth(self):
        from backend.main import app
        from backend.core.config import get_settings
        settings = get_settings()
        settings.api_key = "test-key"
        client = TestClient(app)
        resp = client.get("/api/stories")
        assert resp.status_code in (401, 403)
        settings.api_key = ""

    def test_create_story_validates_input(self, client):
        resp = client.post("/api/stories", json={
            "title": "test<script>",
            "genre": "玄幻",
            "style": "热血",
        })
        assert resp.status_code == 422  # Validation error

    def test_create_story_valid(self, client):
        with patch("backend.api.stories.NovelOrchestrator") as mock_orch:
            mock_orch.return_value.create_story = AsyncMock(return_value=MagicMock(
                id="test-1",
                config=MagicMock(title="测试", genre=MagicMock(value="玄幻"), style=MagicMock(value="热血")),
                outline=["ch1"],
                world_bible=MagicMock(model_dump=lambda: {}),
                characters=[],
            ))
            resp = client.post("/api/stories", json={
                "title": "测试小说",
                "genre": "玄幻",
                "style": "热血战斗",
            })
            assert resp.status_code == 200
            data = resp.json()
            assert data["id"] == "test-1"


from unittest.mock import MagicMock
