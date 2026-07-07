"""Tests for local conversation memory behavior."""

from __future__ import annotations


def test_get_memory_path_uses_session_json_name(server_module):
    assert server_module.get_memory_path("abc123") == "abc123.json"


def test_local_memory_loads_empty_list_when_file_missing(server_module, monkeypatch, tmp_path):
    monkeypatch.setattr(server_module, "USE_S3", False)
    monkeypatch.setattr(server_module, "MEMORY_DIR", str(tmp_path))

    assert server_module.load_conversation("missing-session") == []


def test_local_memory_save_then_load_round_trip(server_module, monkeypatch, tmp_path):
    monkeypatch.setattr(server_module, "USE_S3", False)
    monkeypatch.setattr(server_module, "MEMORY_DIR", str(tmp_path))

    messages = [
        {"role": "user", "content": "Hello", "timestamp": "2026-01-01T00:00:00"},
        {"role": "assistant", "content": "Hi there", "timestamp": "2026-01-01T00:00:01"},
    ]

    server_module.save_conversation("round-trip", messages)

    assert server_module.load_conversation("round-trip") == messages
