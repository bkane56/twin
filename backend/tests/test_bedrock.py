"""Tests for Bedrock request construction with the AWS client mocked."""

from __future__ import annotations


class FakeBedrockClient:
    def __init__(self):
        self.calls = []

    def converse(self, **kwargs):
        self.calls.append(kwargs)
        return {
            "output": {
                "message": {
                    "content": [
                        {"text": "Mocked Bedrock response"},
                    ]
                }
            }
        }


def test_call_bedrock_filters_history_and_builds_nova_payload(monkeypatch, server_module):
    fake_client = FakeBedrockClient()
    monkeypatch.setattr(server_module, "bedrock_client", fake_client)
    monkeypatch.setattr(server_module, "BEDROCK_MODEL_ID", "amazon.nova-lite-v1:0")
    monkeypatch.setattr(server_module, "prompt", lambda: "You are Brian's digital twin.")

    conversation = [
        {"role": "system", "content": "Ignored system message"},
        {"role": "user", "content": " Earlier user question "},
        {"role": "assistant", "content": "Earlier assistant answer"},
        {"role": "assistant", "content": "   "},
        {"role": "tool", "content": "Ignored tool message"},
    ]

    result = server_module.call_bedrock(conversation, " New user question ")

    assert result == "Mocked Bedrock response"
    assert len(fake_client.calls) == 1
    call = fake_client.calls[0]
    assert call["modelId"] == "amazon.nova-lite-v1:0"
    assert call["system"] == [{"text": "You are Brian's digital twin."}]
    assert call["inferenceConfig"] == {
        "maxTokens": 2000,
        "temperature": 0.7,
        "topP": 0.9,
    }
    assert call["messages"] == [
        {"role": "user", "content": [{"text": "Earlier user question"}]},
        {"role": "assistant", "content": [{"text": "Earlier assistant answer"}]},
        {"role": "user", "content": [{"text": "New user question"}]},
    ]
