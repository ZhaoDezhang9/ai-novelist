"""单元测试 — 后端核心逻辑，不依赖真实 LLM API"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock


class TestAuth:
    @pytest.fixture
    def auth_client(self):
        from fastapi import FastAPI, Depends, APIRouter
        from fastapi.testclient import TestClient
        from backend.core.auth import verify_api_key
        router = APIRouter()

        @router.get("/protected")
        async def protected():
            return {"ok": True}

        app = FastAPI()
        app.include_router(router, dependencies=[Depends(verify_api_key)])
        return TestClient(app)

    def test_auth_passes_when_no_key_configured(self, auth_client):
        resp = auth_client.get("/protected")
        assert resp.status_code == 200

    def test_auth_blocks_when_key_configured_no_header(self, auth_client):
        from backend.core.config import get_settings
        settings = get_settings()
        settings.api_key = "test-key"
        resp = auth_client.get("/protected")
        assert resp.status_code == 401
        settings.api_key = ""

    def test_auth_blocks_wrong_key(self, auth_client):
        from backend.core.config import get_settings
        settings = get_settings()
        settings.api_key = "correct-key"
        resp = auth_client.get("/protected", headers={"Authorization": "Bearer wrong-key"})
        assert resp.status_code == 401
        settings.api_key = ""

    def test_auth_passes_with_correct_key(self, auth_client):
        from backend.core.config import get_settings
        settings = get_settings()
        settings.api_key = "correct-key"
        resp = auth_client.get("/protected", headers={"Authorization": "Bearer correct-key"})
        assert resp.status_code == 200
        settings.api_key = ""


class TestValidators:
    def test_valid_input_passes(self):
        from backend.core.validators import validate_no_injection, validate_length
        result = validate_no_injection("正常的中文标题和介绍")
        assert result == "正常的中文标题和介绍"

    def test_injection_rejected(self):
        from backend.core.validators import validate_no_injection
        with pytest.raises(ValueError):
            validate_no_injection("hello<script>alert(1)</script>")

    def test_sql_injection_rejected(self):
        from backend.core.validators import validate_no_injection
        with pytest.raises(ValueError):
            validate_no_injection("test'; DROP TABLE stories; --")

    def test_length_limit(self):
        from backend.core.validators import validate_length
        validate_length("short text")
        with pytest.raises(ValueError):
            validate_length("x" * 5001)


class TestHealthCheck:
    @pytest.mark.anyio
    async def test_health_endpoint(self):
        """测试 /api/health 返回结构正确"""
        from unittest.mock import patch, AsyncMock
        from backend.main import app
        from fastapi.testclient import TestClient

        # Test without deep checks triggering external calls
        client = TestClient(app)
        # Mock the deep checks to avoid real API calls
        with patch("backend.main.verify_api_key", return_value=None):
            resp = client.get("/api/health")
            assert resp.status_code == 200
            data = resp.json()
            assert "status" in data
            assert "system" in data
            assert "checks" in data
            assert "X-Correlation-ID" in resp.headers


class TestLogging:
    def test_correlation_id_var(self):
        from backend.core.logging import correlation_id_var
        correlation_id_var.set("test-cid-123")
        assert correlation_id_var.get() == "test-cid-123"
        correlation_id_var.set("")
        assert correlation_id_var.get() == ""


class TestConfig:
    def test_default_settings(self):
        from backend.core.config import Settings
        s = Settings()
        assert s.api_key == ""
        assert s.cors_origins == "http://localhost:3000,http://127.0.0.1:3000"
        assert s.log_level == "INFO"
        assert s.rate_limit == "30/minute"

    def test_cors_origins_parsing(self):
        from backend.core.config import Settings
        s = Settings(cors_origins="http://a.com, http://b.com")
        origins = [o.strip() for o in s.cors_origins.split(",")]
        assert len(origins) == 2
        assert "http://a.com" in origins
