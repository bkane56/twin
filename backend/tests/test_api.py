"""API-level tests for the FastAPI digital twin backend."""

from __future__ import annotations

import pytest
from fastapi import HTTPException


def test_health_endpoint_reports_runtime_configuration(app_client):
    response = app_client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "healthy"
    assert body["use_s3"] is False
    assert body["bedrock_model"]


def test_root_endpoint_returns_service_metadata(app_client):
    response = app_client.get("/")

    assert response.status_code == 200
    body = response.json()
    assert "AI Digital Twin API" in body["message"]
    assert body["storage"] == "local"
    assert body["memory_enabled"] is True


def test_chat_rejects_missing_message(app_client):
    response = app_client.post("/chat", json={"session_id": "abc123"})

    assert response.status_code == 422


def test_chat_uses_existing_session_and_persists_conversation(
    app_client,
    monkeypatch: pytest.MonkeyPatch,
    server_module,
):
    saved_payloads = []

    def fake_load_conversation(session_id: str):
        assert session_id == "existing-session"
        return [{"role": "user", "content": "Earlier question", "timestamp": "2026-01-01T00:00:00"}]

    def fake_call_bedrock(conversation, user_message: str):
        assert conversation[0]["content"] == "Earlier question"
        assert user_message == "What projects has Brian built?"
        return "Brian has built full-stack AI portfolio projects."

    def fake_save_conversation(session_id: str, messages):
        saved_payloads.append((session_id, messages))

    monkeypatch.setattr(server_module, "load_conversation", fake_load_conversation)
    monkeypatch.setattr(server_module, "call_bedrock", fake_call_bedrock)
    monkeypatch.setattr(server_module, "save_conversation", fake_save_conversation)

    response = app_client.post(
        "/chat",
        json={
            "message": "What projects has Brian built?",
            "session_id": "existing-session",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body == {
        "response": "Brian has built full-stack AI portfolio projects.",
        "session_id": "existing-session",
    }
    assert saved_payloads
    saved_session, saved_messages = saved_payloads[0]
    assert saved_session == "existing-session"
    assert saved_messages[-2]["role"] == "user"
    assert saved_messages[-2]["content"] == "What projects has Brian built?"
    assert saved_messages[-1]["role"] == "assistant"
    assert saved_messages[-1]["content"] == "Brian has built full-stack AI portfolio projects."


def test_chat_converts_unexpected_backend_error_to_500(
    app_client,
    monkeypatch: pytest.MonkeyPatch,
    server_module,
):
    monkeypatch.setattr(server_module, "load_conversation", lambda _session_id: [])

    def fake_call_bedrock(_conversation, _message: str):
        raise RuntimeError("model unavailable")

    monkeypatch.setattr(server_module, "call_bedrock", fake_call_bedrock)

    response = app_client.post("/chat", json={"message": "Hello"})

    assert response.status_code == 500
    assert "model unavailable" in response.json()["detail"]


def test_chat_preserves_explicit_http_exception(
    app_client,
    monkeypatch: pytest.MonkeyPatch,
    server_module,
):
    monkeypatch.setattr(server_module, "load_conversation", lambda _session_id: [])

    def fake_call_bedrock(_conversation, _message: str):
        raise HTTPException(status_code=403, detail="Access denied to Bedrock model")

    monkeypatch.setattr(server_module, "call_bedrock", fake_call_bedrock)

    response = app_client.post("/chat", json={"message": "Hello"})

    assert response.status_code == 403
    assert response.json()["detail"] == "Access denied to Bedrock model"
