import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer
from src.live_server import create_app


@pytest.mark.anyio
async def test_live_server_dashboard_and_chat_endpoints():
    app = create_app()
    async with TestClient(TestServer(app)) as client:
        # 1. Index HTML page loads
        resp_html = await client.get("/")
        assert resp_html.status == 200
        text = await resp_html.text()
        assert "ДАШБОРД ПРЕДПРИЯТИЯ" in text

        # 2. Dashboard API for director returns both production and procurement
        resp_dir = await client.get("/api/state?role=director")
        assert resp_dir.status == 200
        data_dir = await resp_dir.json()
        assert len(data_dir["production"]) == 5
        assert len(data_dir["procurement"]) == 4

        # 3. Dashboard API for production role blocks procurement (returns empty list + rbac_restricted=True)
        resp_prod = await client.get("/api/state?role=production")
        assert resp_prod.status == 200
        data_prod = await resp_prod.json()
        assert len(data_prod["production"]) == 5
        assert data_prod["procurement_restricted"] is True

        # 4. Chat API answers question and returns safe SQL
        resp_chat = await client.post(
            "/api/chat",
            json={"role": "director", "question": "Покажи сверку 1С и камер по литью и сварке"},
        )
        assert resp_chat.status == 200
        chat_json = await resp_chat.json()
        assert "SELECT" in chat_json["generated_sql"]
        assert "Литьё" in chat_json["answer"]
