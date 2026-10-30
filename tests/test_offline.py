"""Offline tests: no OpenAI key, no network."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT), str(ROOT / "api")]

from fastapi.testclient import TestClient  # noqa: E402

from aimakerspace.text_utils import CharacterTextSplitter  # noqa: E402
from app import app  # noqa: E402

client = TestClient(app)


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200 and r.json()["status"] == "healthy"


def test_chat_requires_api_key_field():
    r = client.post("/api/chat", json={"developer_message": "hi", "user_message": "hi"})
    assert r.status_code == 422


def test_text_splitter_chunks_with_overlap():
    text = "abcdefghij" * 30
    chunks = CharacterTextSplitter(chunk_size=100, chunk_overlap=20).split(text)
    assert len(chunks) > 1 and all(len(c) <= 100 for c in chunks)
    assert chunks[0][-20:] == chunks[1][:20]


def test_chat_with_rejected_key_returns_401(monkeypatch):
    import app as app_module
    import httpx
    from openai import AuthenticationError

    class FakeCompletions:
        def create(self, **_):
            req = httpx.Request("POST", "https://api.openai.com/v1/chat/completions")
            raise AuthenticationError("bad key", response=httpx.Response(401, request=req), body=None)

    class FakeClient:
        def __init__(self, **_):
            self.chat = type("C", (), {"completions": FakeCompletions()})()

    monkeypatch.setattr(app_module, "OpenAI", FakeClient)
    r = client.post("/api/chat", json={"developer_message": "x", "user_message": "hi", "api_key": "not-a-key"})
    assert r.status_code == 401
    assert "rejected" in r.json()["detail"]
